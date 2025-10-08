FROM python:3.10-slim

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/processor.py /app/processor.py
COPY app/retry_dlq.py /app/retry_dlq.py

ENV PYTHONUNBUFFERED=1

# default command runs the processor; cronjob will override to run retry_dlq.py
CMD ["python", "/app/processor.py"]
