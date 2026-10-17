"""
MINEGUARD - Real-Time IoT Streamer
MQTT-based stream generator that outputs periodic sensor readings.
"""

import json
import time
import random
import logging
from datetime import datetime
from typing import Dict, List
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "mineguard/sensors/{mine_id}/{sensor_type}"
STREAM_INTERVAL = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class IoTStreamer:
    def __init__(self, mine_ids: List[str], broker: str = MQTT_BROKER, port: int = MQTT_PORT):
        self.mine_ids = mine_ids
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")

    def generate_sensor_reading(self, mine_id: str) -> Dict:
        return {
            "mine_id": mine_id,
            "timestamp": datetime.utcnow().isoformat(),
            "methane_ppm": round(random.gauss(1.5, 0.8), 2),
            "co_ppm": round(random.gauss(50, 20), 2),
            "air_velocity_ms": round(random.gauss(15, 3), 2),
            "convergence_ratio_pct": round(random.gauss(2.0, 0.5), 2),
            "ground_vibration_mm": round(random.gauss(0.5, 0.2), 2),
            "slope_displacement_mm": round(random.gauss(1.0, 0.3), 2),
            "roof_pressure_bar": round(random.gauss(2.5, 0.5), 2),
            "temperature_c": round(random.gauss(28, 5), 2),
            "humidity_pct": round(random.gauss(75, 10), 2),
        }

    def publish_reading(self, mine_id: str, reading: Dict):
        topic = MQTT_TOPIC.format(mine_id=mine_id, sensor_type="all")
        payload = json.dumps(reading)
        self.client.publish(topic, payload)
        logger.info(f"Published to {topic}: {payload}")

    def start_streaming(self, duration_seconds: int = 60):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()
        logger.info(f"Starting IoT stream for {duration_seconds} seconds...")
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            for mine_id in self.mine_ids:
                reading = self.generate_sensor_reading(mine_id)
                self.publish_reading(mine_id, reading)
            time.sleep(STREAM_INTERVAL)
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("IoT streaming stopped.")


def main():
    print("=" * 60)
    print("MINEGUARD - Real-Time IoT Streamer")
    print("=" * 60)
    mine_ids = [f"Mine_{i}" for i in range(1, 11)]
    streamer = IoTStreamer(mine_ids)
    streamer.start_streaming(duration_seconds=60)


if __name__ == "__main__":
    main()
