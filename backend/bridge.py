"""Hardware protocol bridge for physical ESP32 guidance signs (MQTT + RS-485)."""

from __future__ import annotations

import json
import logging

from backend.config import Settings
from backend.models import EntranceDisplayState, IntersectionDisplayState

logger = logging.getLogger(__name__)


class HardwareBridge:
    """Publishes real-time signage updates over MQTT and/or RS-485 serial bus."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._mqtt_client = None
        self._serial = None
        self.published_count: int = 0

        if settings.mqtt_enabled:
            self._init_mqtt()
        if settings.rs485_enabled:
            self._init_rs485()

    def _init_mqtt(self) -> None:
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="spg-backend")
            client.connect_async(self.settings.mqtt_host, self.settings.mqtt_port, keepalive=30)
            client.loop_start()
            self._mqtt_client = client
            logger.info("MQTT bridge started (%s:%s)", self.settings.mqtt_host, self.settings.mqtt_port)
        except Exception as exc:
            logger.warning("MQTT bridge unavailable, continuing without broker: %s", exc)

    def _init_rs485(self) -> None:
        try:
            import serial

            self._serial = serial.Serial(
                port=self.settings.rs485_port,
                baudrate=self.settings.rs485_baudrate,
                timeout=0.1,
            )
            logger.info("RS-485 bridge opened on %s", self.settings.rs485_port)
        except Exception as exc:
            logger.warning("RS-485 serial port unavailable, continuing in virtual mode: %s", exc)

    def publish_displays(
        self,
        entrances: list[EntranceDisplayState],
        intersections: list[IntersectionDisplayState],
    ) -> None:
        for ent in entrances:
            payload = {
                "display_id": ent.id,
                "node_id": ent.display_node_id,
                "total_slots": ent.total_slots,
                "available_slots": ent.available_slots,
                "status": ent.status,
                "recommended_zone": ent.recommended_zone,
                "zones": [z.model_dump() for z in ent.zones],
                "timestamp": ent.updated_at.isoformat(),
            }
            self._emit(ent.mqtt_topic, payload, ent.rs485_frame_hex)

        for inter in intersections:
            payload = {
                "display_id": inter.id,
                "node_id": inter.display_node_id,
                "branches": {b.direction: b.model_dump() for b in inter.branches},
                "timestamp": inter.updated_at.isoformat(),
            }
            self._emit(inter.mqtt_topic, payload, inter.rs485_frame_hex)

    def _emit(self, topic: str, json_payload: dict, rs485_hex: str) -> None:
        self.published_count += 1
        if self._mqtt_client is not None:
            try:
                self._mqtt_client.publish(topic, json.dumps(json_payload), qos=0, retain=True)
            except Exception as exc:
                logger.debug("MQTT publish failed for %s: %s", topic, exc)

        if self._serial is not None and rs485_hex:
            try:
                self._serial.write(bytes.fromhex(rs485_hex))
            except Exception as exc:
                logger.debug("RS-485 write failed: %s", exc)

    def close(self) -> None:
        if self._mqtt_client is not None:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        if self._serial is not None:
            self._serial.close()
