"""Apply Home Assistant permissions to device-wide REMI services."""
from homeassistant.auth.permissions.const import POLICY_CONTROL, POLICY_READ
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator


async def async_prepare_device_action(
    hass: HomeAssistant, call: ServiceCall, coordinator: RemiDataUpdateCoordinator,
    *, control: bool, read: bool = False,
) -> None:
    """Check caller permissions before reading data or sending a device command."""
    if call.context.user_id is not None:
        user = await hass.auth.async_get_user(call.context.user_id)
        if user is None or not user.is_active:
            raise Unauthorized(context=call.context)
        if not user.is_admin:
            # The actions target the entire REMI, even data with a disabled sensor.
            entry = coordinator.config_entry
            entities = [e for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
                        if e.platform == DOMAIN] if entry else []
            permissions = []
            if read or not control:
                permissions.append(POLICY_READ)
            if control:
                permissions.append(POLICY_CONTROL)
            for policy in permissions:
                if not entities or not all(user.permissions.check_entity(e.entity_id, policy) for e in entities):
                    raise Unauthorized(context=call.context, permission=policy)
    if control and not coordinator.last_update_success:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="cannot_refresh_device")
