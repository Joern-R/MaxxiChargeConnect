from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy

from ..const import DOMAIN


class BatterySoESensor(SensorEntity):
    def __init__(self, entry: ConfigEntry, index: int):
        self._entry = entry
        self._index = index
        self._attr_name = f"Battery {index + 1} SoE"
        self._attr_unique_id = f"{entry.entry_id}_battery_soe_{index}"
        self._attr_icon = "mdi:file-document-outline"
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_native_value = None

    async def async_added_to_hass(self):
        self.hass.data[DOMAIN][self._entry.entry_id]["listeners"].append(
            self._handle_update
        )

    async def _handle_update(self, data):
        try:
            self._attr_native_value = data["batteriesInfo"][self._index][
                "batteryCapacity"
            ]
            self.async_write_ha_state()
        except (IndexError, KeyError):
            pass

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "mephdrac",
            "model": "CCU - Maxxicharge",
        }
