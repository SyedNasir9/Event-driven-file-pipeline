import os
import boto3
from botocore.exceptions import ClientError

REGION = os.getenv("AWS_REGION", "us-east-1")
DLQ_URL = os.getenv("DLQ_URL")
MAIN_QUEUE_URL = os.getenv("SQS_URL")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "10"))

sqs = boto3.client('sqs', region_name=REGION)

def requeue_dlq():
    resp = sqs.receive_message(
        QueueUrl=DLQ_URL,
        MaxNumberOfMessages=MAX_MESSAGES,
        WaitTimeSeconds=0
    )
    msgs = resp.get('Messages', [])
    if not msgs:
        print("No messages in DLQ")
        return

    for m in msgs:
        body = m['Body']
        message_id = m.get('MessageId')
        try:
            print(f"Requeuing message: {message_id}")
            # Send back to main queue
            sqs.send_message(QueueUrl=MAIN_QUEUE_URL, MessageBody=body)
            # Delete from DLQ
            sqs.delete_message(QueueUrl=DLQ_URL, ReceiptHandle=m['ReceiptHandle'])
        except ClientError as e:
            print(f"Failed to requeue message {message_id}: {e}")

if __name__ == "__main__":
    if not DLQ_URL or not MAIN_QUEUE_URL:
        print("Error: DLQ_URL and SQS_URL environment variables must be set.")
    else:
        requeue_dlq()
