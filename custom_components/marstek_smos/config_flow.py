"""Config flow for SMOS integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_SELECTED_ENTITY

_LOGGER = logging.getLogger(__name__)


class SmosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for the SMOS integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user selects a P1 entity."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        
        return await self._async_handle_form(user_input)

    async def async_step_reconfigure(self, user_input=None):
        """Handle a reconfiguration flow initiated by the user."""
        return await self._async_handle_form(user_input, is_reconfigure=True)

    async def _async_handle_form(self, user_input, is_reconfigure=False):
        """Helper to display the form and handle both setup and reconfiguration."""
        errors = {}

        if user_input is not None:
            selected_entity = user_input.get(CONF_SELECTED_ENTITY)
            if is_reconfigure:
                existing_entry = self._get_reconfigure_entry()
                return self.async_update_reload_and_abort(
                    existing_entry,
                    data={CONF_SELECTED_ENTITY: selected_entity},
                )
            
            return self.async_create_entry(
                title="Marstek SMOS",
                data={CONF_SELECTED_ENTITY: selected_entity},
            )

        default_entity = ""
        if is_reconfigure:
            existing_entry = self._get_reconfigure_entry()
            default_entity = existing_entry.data.get(CONF_SELECTED_ENTITY, "")

        entities = self._async_get_p1_entities()
        entity_choices = {
            entity.entity_id: f"{entity.name or entity.entity_id} ({entity.entity_id})"
            for entity in entities
        }

        if not entity_choices:
            errors["base"] = "no_p1_entities_found"

        if default_entity and default_entity not in entity_choices:
            entity_choices[default_entity] = default_entity

        schema = vol.Schema(
            {
                vol.Optional(CONF_SELECTED_ENTITY, default=default_entity): vol.In(entity_choices) if entity_choices else str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure" if is_reconfigure else "user",
            data_schema=schema,
            errors=errors,
        )

    def _async_get_p1_entities(self) -> list:
        """Fetch all eligible P1 entities, excluding our own integration's entities."""
        p1_entities = []
        
        # Get the entity registry instance
        entity_reg = er.async_get(self.hass)
        
        # Safely get current config entry ID if reconfiguring
        current_entry_id = None
        try:
            reconfig_entry = self._get_reconfigure_entry()
            if reconfig_entry:
                current_entry_id = reconfig_entry.entry_id
        except Exception:
            pass

        for state in self.hass.states.async_all():
            entity_id = state.entity_id or ""
            entity_name = state.name or ""

            # 1. Exclude entities belonging to our own config entry (if reconfiguring)
            registry_entry = entity_reg.async_get(entity_id)
            if current_entry_id and registry_entry and registry_entry.config_entry_id == current_entry_id:
                continue

            # 2. Filter by 'p1' in entity name or entity_id (case-insensitive)
            if "p1" not in entity_name.lower() and "p1" not in entity_id.lower():
                continue

            # 3. Filter out unavailable or unknown states
            if state.state in ("unavailable", "unknown"):
                continue

            # 4. Ensure the state can be parsed as a number (float or int)
            try:
                float(state.state)
            except (ValueError, TypeError):
                continue

            p1_entities.append(state)
            
        return p1_entities