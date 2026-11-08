"""Verify Home Assistant loads localized labels without changing entity identity."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from unittest.mock import patch

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations, async_translate_state
from pytest_homeassistant.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN

from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Load the integration's real translation files."""
    yield


ENTITIES = [
    ("sensor", "temperature", "Temperature", "Température"),
    ("sensor", "rssi", "WiFi Signal", "Signal Wi-Fi"),
    ("sensor", "firmware_version", "Firmware Version", "Version du firmware"),
    ("sensor", "ip_address", "IP Address", "Adresse IP"),
    ("sensor", "current_face", "Current Face", "Visage actuel"),
    ("binary_sensor", "online", "Online", "Connexion"),
    ("binary_sensor", "alive", "Alive", "Activité"),
    ("binary_sensor", "firmware_update", "Firmware Update Available", "Mise à jour du firmware disponible"),
    ("button", "check_firmware", "Check firmware status", "Vérifier le firmware"),
    ("light", "background_color", "App Background Color", "Couleur de fond de l’application"),
    ("number", "volume", "Volume", "Volume"),
    ("number", "noise_threshold", "Noise Alert Threshold", "Seuil d’alerte sonore"),
    ("number", "brightness", "Nightlight brightness", "Luminosité de la veilleuse"),
    ("number", "face_brightness", "Face brightness", "Luminosité du visage"),
    ("select", "face", "Clock Face", "Visage du réveil"),
    ("select", "clock_format", "Clock Format", "Format de l’heure"),
    ("select", "music_mode", "Music Mode", "Mode de lecture musicale"),
    ("switch", "alarm_event_id_1", "07:30 · Morning Alarm", "07:30 · Morning Alarm"),
    ("time", "alarm_event_id_1_time", "Morning Alarm time", "Heure de Morning Alarm"),
    ("media_player", "music_player", "Music", "Musique"),
    ("sensor", "sleep_duration", "Last sleep duration", "Durée du dernier sommeil"),
    ("sensor", "sleep_score", "Last sleep score", "Score du dernier sommeil"),
    ("sensor", "sleep_bedtime", "Last bedtime", "Dernière heure de coucher"),
    ("sensor", "sleep_wake_time", "Last wake-up time", "Dernière heure de réveil"),
    ("sensor", "sleep_report_timestamp", "Sleep report date", "Date du bilan de sommeil"),
]


@pytest.mark.parametrize("language", ["en", "fr"])
async def test_localized_names_states_and_reload_preserve_identity(
    hass, mock_api_client, mock_config_entry_data, language,
):
    """Use real setup/reload and real services with a simulated cloud API."""
    hass.config.language = language
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="My REMI")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    existing = {}
    for domain, suffix, english, _ in ENTITIES:
        existing[suffix] = registry.async_get_or_create(
            domain, DOMAIN, f"{MOCK_REMI_ID}_{suffix}",
            config_entry=entry,
            suggested_object_id=f"existing_{suffix}",
            original_name=english,
        )
        if suffix == "background_color":
            existing[suffix] = registry.async_update_entity(
                existing[suffix].entity_id, name="Ma couleur personnelle"
            )
    remi = deepcopy(MOCK_REMI_DATA)
    remi["light_min"] = 7
    mock_api_client.get_remi.return_value = remi
    mock_api_client.get_events.return_value = deepcopy(MOCK_EVENT_DATA)

    def check_names(current_language):
        for domain, suffix, english, french in ENTITIES:
            saved = existing[suffix]
            current = registry.async_get(saved.entity_id)
            assert current is not None
            assert current.id == saved.id
            assert current.unique_id == saved.unique_id
            assert current.original_name == (french if current_language == "fr" else english)
            assert current.name == saved.name
            state = hass.states.get(saved.entity_id)
            assert state is not None
            expected_name = f"Remi Bedroom {saved.name or current.original_name}"
            assert state.attributes["friendly_name"] == expected_name

    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        check_names(language)
        face_id = existing["face"].entity_id
        music_id = existing["music_mode"].entity_id
        assert hass.states.get(face_id).state == "awake"
        assert hass.states.get(existing["current_face"].entity_id).state == "awake"
        assert hass.states.get(music_id).state == "single_track"
        assert hass.states.get(existing["alarm_event_id_1"].entity_id).attributes["face"] == "awake"
        assert hass.states.get(face_id).attributes["options"] == [
            "off", "awake", "sleepy", "semi_awake", "smiley",
        ]
        assert async_translate_state(hass, "awake", "select", DOMAIN, "face", None) == (
            "Éveillé" if language == "fr" else "Awake"
        )
        assert async_translate_state(hass, "single_track", "select", DOMAIN, "music_mode", None) == (
            "Piste unique" if language == "fr" else "Single track"
        )

        # HA's final service wrapper rejects old labels; do not promise aliases.
        with pytest.raises(ServiceValidationError) as raised:
            await hass.services.async_call(
                "select", "select_option", {"entity_id": face_id, "option": "Sleepy"}, blocking=True
            )
        assert raised.value.translation_key == "not_valid_option"
        mock_api_client.update_remi.assert_not_awaited()
        await hass.services.async_call(
            "select", "select_option", {"entity_id": face_id, "option": "sleepy"}, blocking=True
        )
        mock_api_client.update_remi.assert_awaited_once_with({
            "face": {"__type": "Pointer", "className": "Face", "objectId": "rnAltoFwYC"}
        })
        mock_api_client.update_remi.reset_mock()
        await hass.services.async_call(
            "select", "select_option", {"entity_id": music_id, "option": "repeat_playlist"}, blocking=True
        )
        mock_api_client.update_remi.assert_awaited_once_with({"musicMode": 3})

        next_language = "fr" if language == "en" else "en"
        await hass.config.async_update(language=next_language)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        check_names(next_language)
        assert hass.states.get(face_id).state == "awake"
        assert hass.states.get(music_id).state == "single_track"


@pytest.mark.parametrize("language", ["en", "fr"])
async def test_frontend_resources_cover_flows_services_options_and_errors(hass, language):
    """Frontend translations follow its requested language independently of states."""
    resources = {}
    for category in ("config", "services", "selector", "exceptions", "entity"):
        resources.update(await async_get_translations(hass, language, category, {DOMAIN}))
    prefix = f"component.{DOMAIN}"
    expected = (
        {
            "config.step.user.data.password": "Mot de passe",
            "services.create_alarm.name": "Créer une alarme",
            "services.update_alarm.fields.time.name": "Heure",
            "services.update_alarm.fields.music_duration_minutes.name": "Durée de la musique",
            "services.get_history.name": "Consulter l’historique du sommeil et de l’environnement",
            "services.delete_alarm.fields.event_id.name": "Identifiant de l’alarme",
            "selector.alarm_face.options.sleepy": "Endormi",
            "entity.select.face.state.semi_awake": "À moitié réveillé",
            "entity.select.music_mode.state.repeat_playlist": "Répéter la liste",
            "exceptions.alarm_not_found.message": "Cette alarme REMI n’existe plus",
            "entity.light.physical_brightness.name": "Veilleuse",
            "entity.sensor.daily_reconnections.name": "Reconnexions quotidiennes signalées",
            "entity.sensor.reported_clock_shift.name": "Décalage d’horloge signalé",
        } if language == "fr" else {
            "config.step.user.data.password": "Password",
            "services.create_alarm.name": "Create Alarm",
            "services.update_alarm.fields.time.name": "Time",
            "services.update_alarm.fields.music_duration_minutes.name": "Music duration",
            "services.get_history.name": "Get sleep and environmental history",
            "services.delete_alarm.fields.event_id.name": "Event ID",
            "selector.alarm_face.options.sleepy": "Sleepy",
            "entity.select.face.state.semi_awake": "Semi-Awake",
            "entity.select.music_mode.state.repeat_playlist": "Repeat playlist",
            "exceptions.alarm_not_found.message": "This REMI alarm no longer exists",
            "entity.light.physical_brightness.name": "Nightlight",
            "entity.sensor.daily_reconnections.name": "Reported daily reconnections",
            "entity.sensor.reported_clock_shift.name": "Reported clock shift",
        }
    )
    for key, text in expected.items():
        assert resources[f"{prefix}.{key}"] == text


def test_translations_have_matching_keys_placeholders_and_valid_state_codes():
    """Catch untranslated additions and state keys that hassfest would reject."""
    root = Path(__file__).parents[1] / "custom_components" / DOMAIN
    english = json.loads((root / "translations/en.json").read_text(encoding="utf-8"))
    french = json.loads((root / "translations/fr.json").read_text(encoding="utf-8"))
    assert json.loads((root / "strings.json").read_text(encoding="utf-8")) == english

    def check(left, right, path=()):
        if isinstance(left, dict):
            assert left.keys() == right.keys(), path
            if path and path[-1] in {"state", "options"}:
                assert all(re.fullmatch(r"[a-z0-9_-]+", key) for key in left), path
            for key, value in left.items():
                check(value, right[key], (*path, key))
        else:
            assert set(re.findall(r"\{[^}]+\}", left)) == set(re.findall(r"\{[^}]+\}", right)), path
    check(english, french)
