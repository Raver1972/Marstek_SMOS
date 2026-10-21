"""Sensor platform for marstek_smos integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmosCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SMOS sensor platform from a config entry."""
    coordinator: SmosCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([P1PowerSensor(coordinator)])


class P1PowerSensor(CoordinatorEntity[SmosCoordinator], SensorEntity):
    """Representation of a P1 Power Sensor."""

    def __init__(self, coordinator: SmosCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._attr_name = "Power"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "p1_meter_device")},
            name="P1 Meter",
            manufacturer="Custom Integration",
            model="P1 Reader",
        )

    @property
    def native_value(self) -> int | None:
        """Return the state directly from the coordinator data."""
        return self.coordinator.data