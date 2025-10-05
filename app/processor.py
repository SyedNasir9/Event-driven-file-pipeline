import os
import time
import json
import boto3
from botocore.exceptions import ClientError
from urllib.parse import unquote_plus  

# Environment variables
REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_URL = os.getenv("SQS_URL")
S3_BUCKET = os.getenv("S3_BUCKET")
DDB_TABLE = os.getenv("DDB_TABLE")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")  # new for notifications
POLL_WAIT = int(os.getenv("POLL_WAIT", "10"))  # seconds

# AWS clients
sqs = boto3.client('sqs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
ddb = boto3.resource('dynamodb', region_name=REGION)
table = ddb.Table(DDB_TABLE)
sns = boto3.client('sns', region_name=REGION)

def process_file(s3_key):
    """Download file, count lines and bytes."""
    local_path = "/tmp/" + os.path.basename(s3_key)
    s3.download_file(S3_BUCKET, s3_key, local_path)
    with open(local_path, "rb") as f:
        content = f.read()
    lines = content.count(b'\n')
    size = len(content)
    return {"lines": int(lines), "size_bytes": int(size)}

def send_notification(s3_key):
    """Publish notification to SNS (Slack/Email)."""
    if not SNS_TOPIC_ARN:
        return
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"File processed successfully: {s3_key}",
            Subject="File Processed"
        )
        print(f"Sent notification for {s3_key}")
    except Exception as e:
        print(f"Failed to send notification for {s3_key}: {e}")

def handle_message(msg):
    body = msg.get('Body')
    try:
        payload = json.loads(body)
    except Exception:
        payload = {"s3_key": body}

    # Extract S3 key from payload
    raw_key = payload.get('s3_key') or payload.get('Records', [{}])[0].get('s3', {}).get('object', {}).get('key')
    if not raw_key:
        raise ValueError("No s3_key found in message")

    # Decode key to handle spaces/special characters
    s3_key = unquote_plus(raw_key)

    print(f"Processing s3 key: {s3_key}")
    result = process_file(s3_key)

    

    # Store metadata in DynamoDB
    item = {
        'FileID': s3_key,
        'ProcessedAt': int(time.time()),
        'Lines': result['lines'],
        'SizeBytes': result['size_bytes'],
        'Status': 'SUCCESS'
    }
    table.put_item(Item=item)
    print(f"Stored metadata for {s3_key}")

    # Send SNS notification
    send_notification(s3_key)

def main_loop():
    print("Starting processor main loop...")
    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl=SQS_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
            )
            messages = resp.get('Messages', [])
            if not messages:
                time.sleep(POLL_WAIT)
                continue

            for m in messages:
                receipt_handle = m['ReceiptHandle']
                try:
                    handle_message(m)
                    sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)
                except Exception as e:
                    print("Processing failed for message:", e)
                    table.put_item(Item={
                        'FileID': json.dumps(m.get('MessageId')),
                        'ProcessedAt': int(time.time()),
                        'Status': 'FAILED',
                        'Error': str(e)
                    })
        except ClientError as e:
            print("AWS client error:", e)
            time.sleep(5)
        except Exception as e:
            print("Unexpected error:", e)
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
