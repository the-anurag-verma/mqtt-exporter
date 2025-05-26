import os
import json
import time
import ssl
from prometheus_client import start_http_server, Gauge, Counter
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "home/#")
MQTT_TLS = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_TLS_INSECURE = os.getenv("MQTT_TLS_INSECURE", "false").lower() == "true"
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "8000"))

message_counter = Counter('mqtt_messages_total', 'Total MQTT messages received', ['topic'])
last_message = Gauge('mqtt_last_message_timestamp_seconds', 'Last message received time per topic', ['topic'])
json_metrics = {}

def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    topic = msg.topic
    message_counter.labels(topic=topic).inc()
    last_message.labels(topic=topic).set(time.time())

    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if key not in json_metrics:
                        json_metrics[key] = Gauge(f"mqtt_{key}", f"MQTT JSON value for {key}")
                    json_metrics[key].set(value)
    except Exception:
        pass  # ignore non-JSON or bad payloads

def main():
    start_http_server(EXPORTER_PORT)

    client = mqtt.Client(protocol=mqtt.MQTTv311)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    if MQTT_TLS:
        client.tls_set(ca_certs="/ca.crt")
        if MQTT_TLS_INSECURE:
            client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()

