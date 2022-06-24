from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import CONF_ADDRESS, CONF_NAME, DEVICE_DEFAULT_NAME
from homeassistant.helpers.event import track_point_in_time
from datetime import datetime, timedelta

import time as time
import voluptuous as vol
import logging
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from .relayddl import switch_on
from .relayddl import switch_off
from .relayddl import switch_is_on

_LOGGER = logging.getLogger(__name__)

TOGGLE_FOR_DEFAULT = timedelta(seconds=1)

CONF_I2C_ADDRESS = "i2c_address"
DEFAULT_I2C_ADDRESS = 0x10
CONF_PINS = "pins"
CONF_CHANNELS = "channels"
CONF_INDEX = "index"
CONF_INVERT_LOGIC = "invert_logic"
CONF_INITIAL_STATE = "initial_state"
CONF_MOMENTARY = "momentary"
CONF_ON_FOR = "on_for"

_CHANNELS_SCHEMA = vol.Schema(
    [
        {
            vol.Required(CONF_INDEX): cv.positive_int,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_INITIAL_STATE, default=False): cv.boolean,
            vol.Optional(CONF_MOMENTARY, default=0): cv.positive_int,
            vol.Optional(CONF_ON_FOR): vol.All(cv.time_period, cv.positive_timedelta),
    }
    ]
)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): vol.Coerce(int),
        vol.Required(CONF_CHANNELS): _CHANNELS_SCHEMA,
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    switches = []
    device = config.get(CONF_I2C_ADDRESS)
    channels = config.get(CONF_CHANNELS)
    for channel_config in channels:
      ind = channel_config[CONF_INDEX]
      name = channel_config[CONF_NAME]
      init = channel_config[CONF_INITIAL_STATE]
      momentary = channel_config[CONF_MOMENTARY]
      if CONF_ON_FOR in channel_config:
        togglefor = channel_config[CONF_ON_FOR]
        _LOGGER.debug('Toggle for: ' + str(togglefor))
      else:
        togglefor = None

      switches.append(MySwitch(device,ind,name,init,momentary,togglefor))

    add_entities(switches)

class MySwitch(SwitchEntity):
    def __init__(self, device, ind, name, init, momentary,togglefor):
        self._is_on = False
        self._device = device
        self._ind = ind
        self._name = name or DEVICE_DEFAULT_NAME
        self._init = init
        self._momentary = momentary
        self._toggle_for = togglefor
        self._toggle_until = None

        if init:
          switch_on(self._device, self._ind)
        else:
          switch_off(self._device, self._ind)

    @property
    def name(self):
        """Name of the entity."""
        return self._name

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        self._is_on = switch_is_on(self._device, self._ind)
        return self._is_on

    @property
    def state(self):
      """Return the state of the switch."""
      if self._toggle_until is not None:
        _LOGGER.debug('trigger state' + self._name)
        if self._is_on:
          if self._toggle_until > time.monotonic():
            return "on"
          _LOGGER.debug('turned off')
          self._toggle_until = None
          self._is_on = False
          switch_off(self._device, self._ind)
          return "off"
      else:
        if self._is_on:
          return "on"
        else:
          return "off"

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.debug('turned on ' + self._name + '  ' + str(self._toggle_for))
        switch_on(self._device, self._ind)
        self._is_on = True
        if self._toggle_for is not None:
          _LOGGER.debug('togglefor is not None ' + self._name)
          self._toggle_until = time.monotonic() + self._toggle_for.total_seconds()
          track_point_in_time(self.hass, self.async_update_ha_state, dt_util.utcnow() + self._toggle_for)
        else:
          _LOGGER.debug('togglefor is None ' + self._name)
        self.async_schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        switch_off(self._device, self._ind)
        if self._toggle_until is not None:
          if self._is_on:
            _LOGGER.debug('turned off')
            self._toggle_until = None
        self._is_on = False
