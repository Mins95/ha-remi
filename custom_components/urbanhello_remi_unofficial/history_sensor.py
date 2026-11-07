"""Sensors for the last cloud sleep report, separate from live REMI readings."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import UnitOfTime

from .entity import RemiEntity
from .history import RemiHistoryCoordinator, parse_history_datetime

HISTORY_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="sleep_duration", translation_key="sleep_duration",
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:sleep", suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="sleep_score", translation_key="sleep_score", icon="mdi:sleep",
    ),
    SensorEntityDescription(
        key="sleep_bedtime", translation_key="sleep_bedtime", icon="mdi:bed-clock",
    ),
    SensorEntityDescription(
        key="sleep_wake_time", translation_key="sleep_wake_time", icon="mdi:weather-sunset-up",
    ),
    SensorEntityDescription(
        key="sleep_report_timestamp", translation_key="sleep_report_timestamp",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


class RemiHistorySensor(RemiEntity, SensorEntity):
    """A historical estimate retains its report date and never replaces live data."""

    def __init__(self, coordinator: RemiHistoryCoordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._remi_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        report = self.coordinator.latest_report
        if self.entity_description.key == "sleep_report_timestamp":
            return parse_history_datetime(report.get("log_timestamp"))
        return report.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        stamp = parse_history_datetime(self.coordinator.latest_report.get("log_timestamp"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds() if stamp else None
        return {
            "source": "cloud_history",
            "log_timestamp": stamp.isoformat() if stamp else None,
            "report_age_days": round(age / 86400, 2) if age is not None else None,
            "stale": age is None or age < 0 or age > 48 * 3600,
            "timezone": self.coordinator.remi.get("timezone"),
        }
