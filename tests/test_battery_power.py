from unittest.mock import AsyncMock, MagicMock, patch, Mock
from homeassistant.const import CONF_WEBHOOK_ID, UnitOfPower
from homeassistant.components.sensor import (
    SensorDeviceClass,    
    SensorStateClass,
)
import pytest
from custom_components.maxxi_charge_connect.const import DOMAIN
from custom_components.maxxi_charge_connect.devices.battery_power import (
    BatteryPower,
)

@pytest.mark.asyncio
async def test_ccu_power_init(caplog):
    
    dummy_config_entry = MagicMock()
    dummy_config_entry.entry_id = "1234abcd"
    dummy_config_entry.title = "Test Entry"
    
    sensor = BatteryPower(dummy_config_entry)

    # Grundlegende Attribute prüfen
    assert sensor._entry == dummy_config_entry
    assert sensor._attr_suggested_display_precision == 2
    assert sensor._attr_device_class == SensorDeviceClass.POWER
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT
    assert sensor._attr_native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.icon == "mdi:battery-charging-outline"
    assert sensor._attr_unique_id == "1234abcd_battery_power"
    assert sensor._attr_native_value is None
    
@pytest.mark.asyncio
@patch("custom_components.maxxi_charge_connect.devices.battery_power.async_dispatcher_connect")
async def test_ccu_power__async_added_to_hass(mock_dispatcher_connect):
    mock_dispatcher_connect.return_value = lambda: None

    hass = MagicMock()
    hass.async_add_job = AsyncMock()

    dummy_config_entry = MagicMock()
    dummy_config_entry.entry_id = "1234abcd"
    dummy_config_entry.title = "Test Entry"
    dummy_config_entry.options = {}

    dummy_config_entry.data = {
        CONF_WEBHOOK_ID: "Webhook_ID"
    }

    sensor = BatteryPower(dummy_config_entry)
    sensor.hass = hass
        
    await sensor.async_added_to_hass()

    mock_dispatcher_connect.assert_called_once()
    args, kwargs = mock_dispatcher_connect.call_args

    assert args[0] is hass
    assert args[1] == f"{DOMAIN}_{dummy_config_entry.data[CONF_WEBHOOK_ID]}_update_sensor"
    assert args[2].__name__ == "_handle_update"


@pytest.mark.asyncio
async def test_ccu_power_device_info(caplog):

    dummy_config_entry = MagicMock()
    dummy_config_entry.title = "Test Entry"

    sensor = BatteryPower(dummy_config_entry)
    
    # device_info liefert Dict mit erwarteten Keys
    device_info = sensor.device_info
    assert "identifiers" in device_info
    assert device_info["name"] == dummy_config_entry.title


@pytest.mark.asyncio
async def test_ccu_power__handle_update_alles_ok(caplog):
    # is_pccu_ok(ccu) == true 
    # is_power_total_ok(pv_power, batteries) == true
    hass = MagicMock()
    hass.async_add_job = AsyncMock()

    dummy_config_entry = MagicMock()
    dummy_config_entry.data = {}
    
    pccu = 37.623
    pv_power = 218

    data = {
        "Pccu": pccu,
        "PV_power_total": pv_power,
        "batteriesInfo": [
            {
                "batteryCapacity": 1187.339966
            }
        ]
    }

    sensor = BatteryPower(dummy_config_entry)

    with patch("custom_components.maxxi_charge_connect.devices.battery_power.BatteryPower.async_write_ha_state", new_callable=MagicMock
               ) as mock_write_ha_state:
        await sensor._handle_update(data)
        mock_write_ha_state.assert_called_once()

    assert sensor._attr_native_value == round(pv_power - pccu, 3)


@pytest.mark.asyncio
async def test_ccu_power__handle_update_pccu_nicht_ok(caplog):
    # is_pccu_ok(ccu) == false 
    # is_power_total_ok(pv_power, batteries) == true
 
    dummy_config_entry = MagicMock()

    pccu = 36500
    pv_power = 218
    
    data = {
        "Pccu": pccu,
        "PV_power_total": pv_power,
        "batteriesInfo": [
            {
                "batteryCapacity": 1187.339966
            }
        ]
    }

    sensor1 = BatteryPower(dummy_config_entry)

    with patch("custom_components.maxxi_charge_connect.devices.battery_power.BatteryPower.async_write_ha_state", 
               new_callable=MagicMock
               ) as mock_write_ha_state1,\
        patch("custom_components.maxxi_charge_connect.devices.battery_power.is_pccu_ok",return_value=False) as mock_is_pccu_ok1,\
        patch("custom_components.maxxi_charge_connect.devices.battery_power.is_power_total_ok",return_value=True) as mock_is_power_ok1:
        await sensor1._handle_update(data)

        mock_is_power_ok1.assert_not_called()
        mock_is_pccu_ok1.assert_called_once()
        mock_write_ha_state1.assert_not_called()

        args, kwargs = mock_is_pccu_ok1.call_args

        assert args[0] == pccu
        assert sensor1._attr_native_value is None

@pytest.mark.asyncio
async def test_ccu_power__handle_update_alles_nicht_ok(caplog):
    # is_pccu_ok(ccu) == false 
    # is_power_total_ok(pv_power, batteries) == false
 
    dummy_config_entry = MagicMock()

    pccu = 36500
    pv_power = 218
    
    data = {
        "Pccu": pccu,
        "PV_power_total": pv_power,
        "batteriesInfo": [
            {
                "batteryCapacity": 1187.339966
            }
        ]
    }

    sensor1 = BatteryPower(dummy_config_entry)

    with patch("custom_components.maxxi_charge_connect.devices.battery_power.BatteryPower.async_write_ha_state", 
               new_callable=MagicMock
               ) as mock_write_ha_state1,\
        patch("custom_components.maxxi_charge_connect.devices.battery_power.is_pccu_ok",return_value=False) as mock_is_pccu_ok1,\
        patch("custom_components.maxxi_charge_connect.devices.battery_power.is_power_total_ok",return_value=False) as mock_is_power_ok1:
        await sensor1._handle_update(data)

        mock_is_power_ok1.assert_not_called()
        mock_is_pccu_ok1.assert_called_once()
        mock_write_ha_state1.assert_not_called()

        args, kwargs = mock_is_pccu_ok1.call_args

        assert args[0] == pccu
        assert sensor1._attr_native_value is None

@pytest.mark.asyncio
async def test_ccu_power__handle_update_power_total_nicht_ok(caplog):
    # is_pccu_ok(ccu) == true
    # is_power_total_ok(pv_power, batteries) == false
 
    dummy_config_entry = MagicMock()

    pccu = 45.345
    pv_power = 218
    
    data = {
        "Pccu": pccu,
        "PV_power_total": pv_power,
        "batteriesInfo": [
            {
                "batteryCapacity": 1187.339966
            }
        ]
    }

    sensor1 = BatteryPower(dummy_config_entry)

    with patch("custom_components.maxxi_charge_connect.devices.battery_power.BatteryPower.async_write_ha_state", 
               new_callable=MagicMock
               ) as mock_write_ha_state1,\
        patch("custom_components.maxxi_charge_connect.devices.battery_power.is_pccu_ok",return_value=True) as mock_is_pccu_ok1,\
        patch("custom_components.maxxi_charge_connect.devices.battery_power.is_power_total_ok",return_value=False) as mock_is_power_ok1:
        await sensor1._handle_update(data)

        mock_is_power_ok1.assert_called_once()
        mock_is_pccu_ok1.assert_called_once()
        mock_write_ha_state1.assert_not_called()

        args1, kwargs1 = mock_is_pccu_ok1.call_args
        args2, kwargs2 = mock_is_power_ok1.call_args
        assert args1[0] == pccu
        assert args2[0] == pv_power
        assert args2[1] == [{"batteryCapacity": 1187.339966}]
        assert sensor1._attr_native_value is None