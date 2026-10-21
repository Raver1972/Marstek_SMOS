"""Coordinator for marstek_smos integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, EventStateChangedData
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_SELECTED_ENTITY

_LOGGER = logging.getLogger(__name__)


class SmosCoordinator(DataUpdateCoordinator[int]):
    """Coordinator managing marstek_smos data via entity state changes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Smos",
            update_interval=None,
        )
        self.entry = entry
        self.selected_entity_id = entry.data.get(CONF_SELECTED_ENTITY, "")
        self._unsub_listener = None

        # Listen for runtime updates to the config entry (e.g. Reconfigure)
        self.entry.async_on_unload(self.entry.add_update_listener(self._async_entry_updated))

    async def async_config_entry_first_refresh(self) -> None:
        """Set up initial state and event listener."""
        await super().async_config_entry_first_refresh()
        self._setup_listener()

    def _setup_listener(self) -> None:
        """Set up the state change listener for the selected entity."""
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None

        if self.selected_entity_id:
            self._unsub_listener = async_track_state_change_event(
                self.hass,
                [self.selected_entity_id],
                self._handle_entity_state_change,
            )

    @staticmethod
    async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle options/config entry updates."""
        await hass.config_entries.async_reload(entry.entry_id)

    async def _async_update_data(self) -> int:
        """Fetch data from the selected entity's state."""
        if not self.selected_entity_id:
            return 0

        state = self.hass.states.get(self.selected_entity_id)
        if state and state.state not in (None, "unknown", "unavailable"):
            try:
                return int(float(state.state))
            except (ValueError, TypeError):
                return 0
        return 0

    async def _handle_entity_state_change(self, event: Event[EventStateChangedData]) -> None:
        """Callback when the selected entity's state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return

        try:
            val = int(float(new_state.state))
            self.async_set_updated_data(val)
        except (ValueError, TypeError):
            pass