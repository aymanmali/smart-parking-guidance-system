"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPG_", env_file=".env", extra="ignore")

    app_name: str = "Smart Parking Guidance & Management System"
    topology_path: Path = PROJECT_ROOT / "config" / "facility_topology.json"
    rois_path: Path = PROJECT_ROOT / "config" / "rois.json"
    sqlite_path: Path = PROJECT_ROOT / "parking_analytics.db"

    # MQTT Hardware Bridge
    mqtt_enabled: bool = False
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883

    # RS-485 Hardware Bridge
    rs485_enabled: bool = False
    rs485_port: str = "/dev/ttyUSB0"
    rs485_baudrate: int = 115200

    # CORS
    cors_origins: list[str] = ["*"]


settings = Settings()
