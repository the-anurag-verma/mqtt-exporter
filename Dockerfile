FROM python:3.10-slim

WORKDIR /app
COPY mqtt_exporter.py .

RUN pip install paho-mqtt prometheus_client

CMD ["python", "mqtt_exporter.py"]

