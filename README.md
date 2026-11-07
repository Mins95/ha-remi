<p align="center">
  <img src="images/header.svg" alt="UrbanHello REMI for Home Assistant" width="100%">
</p>

<h1 align="center">UrbanHello REMI for Home Assistant</h1>

<p align="center">
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?style=for-the-badge&logo=home-assistant&logoColor=white" alt="Home Assistant integration"></a>
  <a href="https://my.home-assistant.io/redirect/marketplace_repository/?owner=Mins95&amp;repository=ha-remi&amp;category=integration"><img src="https://img.shields.io/badge/Marketplace-Custom-0080ff?style=for-the-badge" alt="Custom Marketplace repository"></a>
  <a href="https://github.com/Mins95/ha-remi/releases/latest"><img src="https://img.shields.io/github/v/release/Mins95/ha-remi?style=for-the-badge&amp;label=Latest%20release&amp;color=0080ff" alt="Latest release"></a>
  <a href="https://github.com/Mins95/ha-remi/releases/tag/0.5.0-beta.2"><img src="https://img.shields.io/badge/0.5.0--beta.2-Opt--in%20beta-f59e0b?style=for-the-badge" alt="0.5.0-beta.2 opt-in beta"></a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="MIT license"></a>
  <a href="https://github.com/Mins95/ha-remi/stargazers"><img src="https://img.shields.io/github/stars/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="Stars"></a>
  <a href="https://github.com/Mins95/ha-remi/commits/main"><img src="https://img.shields.io/github/last-commit/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="Last commit"></a>
  <a href="https://github.com/Mins95/ha-remi"><img src="https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.14"></a>
  <a href="https://github.com/Mins95/ha-remi/issues"><img src="https://img.shields.io/github/issues/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="Open issues"></a>
  <a href="https://github.com/Mins95/ha-remi/pulls"><img src="https://img.shields.io/github/issues-pr/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="Open pull requests"></a>
</p>

<p align="center">
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/tests.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/tests.yml/badge.svg?branch=main" alt="Tests"></a>
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/hassfest.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/hassfest.yml/badge.svg?branch=main" alt="Hassfest"></a>
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/hacs.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/hacs.yml/badge.svg?branch=main" alt="HACS validation"></a>
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/release.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/release.yml/badge.svg?branch=main" alt="Release workflow"></a>
</p>

<p align="center">
  Your REMI, its schedules and its sleep reports in one dashboard card.<br>
  Everyday controls, music and timer profiles, in English or French.
</p>

<p align="center">
  <img src="images/urbanhello-remi.webp" alt="Blue UrbanHello REMI sleep trainer and alarm clock" width="280"><br>
  <sub>Product photo © <a href="https://www.urbanhello.com/fr/">UrbanHello</a> · <a href="https://www.urbanhello.com/img/cms/UH-REMI-Bleu-Simple.webp">Original image</a></sub>
</p>

Community integration maintained by [Mins95](https://github.com/Mins95), based on [timoa/ha-remi](https://github.com/timoa/ha-remi). It uses your UrbanHello account and requires an internet connection. It is not affiliated with or endorsed by UrbanHello.

> [!IMPORTANT]
> **0.5.0-beta.2 is an opt-in pre-release for Home Assistant 2026.11.0 or newer.** The latest stable release remains **0.4.0**. This update simplifies the card: a face display on/off control, Awake/Sleepy choices and music collapsed by default. The beta also includes sleep reports, environmental charts and stored timer profiles. Read the [beta limitations](#-beta-limitations) before enabling it.

---

## 📖 Documentation

[Install and configure](#-installation) · [Add the REMI card](docs/card.md) · [Controls and actions](docs/usage.md) · [Upgrade guide](docs/usage.md#upgrading) · [Changelog](CHANGELOG.md)

**Start with the included REMI card.** Add it through your dashboard's card picker, choose your device if needed, and use the four tabs: REMI, Schedules, Sleep and Timers. No YAML or separate frontend download is required. Existing dashboards are left as you configured them. [Card setup →](docs/card.md)

The main tab is more compact: turn the **face display** on or off, choose **Awake** or **Sleepy**, and expand **Music** when needed. The display control changes the face shown on REMI; it does not switch off the device's power.

**Upgrading from 0.3.x or the original integration?** Read the [0.4.0 migration notice](#-upgrading-to-040) before updating automations that compare face states or select music modes.

## ✨ Features

- 🌡️ **Temperature with decimals**, corrected conversion and diagnostic attributes.
- 🪄 **An included dashboard card**, with a visual editor and device selection.
- ⏰ **Schedules with time, face, volume, brightness and music settings**, plus switches and time entities.
- 🙂 **Clock face and time format**, with 12-hour and 24-hour display settings.
- 💡 **Two separate brightness controls:** upper light from 0 to 100, and night face brightness from 1 to 10.
- 🔊 **Volume, sound notification threshold and music playback mode.**
- 🎵 **Music player and library browsing**, for files already associated with your REMI.
- 🌙 **Sleep reports**, including duration, score, bedtime, wake-up time and report date.
- 📈 **Environmental history on demand**, with report age and the app's chart scales.
- ⏳ **Up to five stored timer profiles**, with start/end music and volume settings.
- 🎨 **Official app background color**, exposed as an RGB light entity.
- 🔎 **Connection and firmware information**, with a read-only firmware check button.
- 🇬🇧 🇫🇷 **English and French interface**, including translated display labels and errors.

Device state is polled every 60 seconds. Sleep metadata is refreshed separately every 20 minutes; chart files are downloaded only when requested. A history failure does not disable device controls. Transient read failures have bounded retries; commands are not automatically replayed after an ambiguous connection failure.

## 📥 Installation

You need **Home Assistant 2026.11.0 or newer**, a REMI already configured in the official app, its UrbanHello account credentials, and internet access from Home Assistant. Development and release checks target **Home Assistant 2026.11.0 exactly**.

### Home Assistant 2026.11 and newer: Marketplace

[![Open this repository in Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=Mins95&repository=ha-remi&category=integration)

1. Open **Settings → Marketplace → Add from link**.
2. Enter `https://github.com/Mins95/ha-remi`.
3. Connect your GitHub account if Marketplace requests it for custom repositories.
4. Open **Remi (Mins95)** and install the latest published release.
5. Restart Home Assistant, then continue with configuration below.

See the [official Marketplace instructions](https://www.home-assistant.io/integrations/marketplace/#custom-repositories).

### HACS installations

[![Open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Mins95&repository=ha-remi&category=integration)

If you manage custom integrations with HACS, add `https://github.com/Mins95/ha-remi` under **Custom repositories**, choose **Integration**, install the published release and restart Home Assistant. The beta still requires Home Assistant 2026.11.0 or newer.

### Opt in to 0.5.0-beta.2

- **Marketplace:** open the repository's device under the Marketplace integration. Enable its disabled-by-default **Pre-release** switch, then turn that switch on. Check for updates and select **0.5.0-beta.2**.
- **HACS:** enable **Show beta versions** for this repository, then select **0.5.0-beta.2** when downloading the update.

Restart Home Assistant after installation and reload the browser page. The beta does not replace 0.4.0 as the default stable release. [Upgrade details →](docs/usage.md#050-beta2-simpler-everyday-controls)

### Configure REMI

1. Open **Settings → Devices & services → Add integration**.
2. Search for **Remi**.
3. Enter the username and password used in the UrbanHello app.
4. Select the REMI to configure if your account contains several devices.

For a manual installation, download the source from [Releases](https://github.com/Mins95/ha-remi/releases), copy `custom_components/urbanhello_remi_unofficial/` into Home Assistant's `config/custom_components/` directory, then restart.

> [!IMPORTANT]
> **Already using another REMI repository?** Both forks use the domain `urbanhello_remi_unofficial`. Marketplace cannot install two repositories providing that domain. **Delete and uninstall also removes the configured integration, devices and entities**; it is not a repository-switch action. Preserve your existing configuration when changing the code source. See [existing installations](docs/usage.md#existing-installations-and-repository-changes).

## 🎛️ Entities and controls

The table uses English display names. Entity names follow Home Assistant's configured language and refresh when the integration reloads; menus and state labels follow your interface language. French and English are included. Entity IDs depend on your installation; existing IDs and user-assigned names are preserved during ordinary updates.

| Control | Entity type | Purpose |
| --- | --- | --- |
| Clock face | Select | Off, awake, sleepy, semi-awake or smiley |
| Clock format | Select | 12-hour or 24-hour display |
| Music mode | Select | Normal, single track, repeat track or repeat playlist |
| Volume | Number | Speaker volume, **0–100** |
| Brightness | Number | Upper light, **0–100**; `0` turns it off |
| Night face brightness | Number | Face brightness in darkness, **1–10** |
| Noise alert threshold | Number | Sound notification threshold, **0–250** |
| App background color | RGB light | REMI's background color in the official app |
| Each alarm | Switch | Enable or disable that schedule |
| Each alarm time | Time | Set hours and minutes in REMI's time zone |
| Music player | Media player | Browse files, play a selection, pause, stop, previous/next, volume and repeat |

**Night face brightness** matches the scale in the [manufacturer's guide](https://www.urbanhello.com/fr/faq/faqs/gerer-la-luminosite-de-remi). It is independent of the upper light. The RGB entity changes the app's appearance; it does not control a physical multicolor light.

**Music mode** changes repeat behavior. Use the separate music player to select a track. The player reports the selected cloud path, but the API does not confirm whether audio is physically playing. [Music controls and limitations →](docs/usage.md#music-player)

| Information | Entity type | Purpose |
| --- | --- | --- |
| Temperature | Sensor | Degrees Celsius, retaining decimal values |
| Current face | Sensor | Reported clock face |
| Firmware version | Sensor | Installed firmware |
| Online / Alive | Binary sensors | Connection and activity reported by REMI |
| Firmware update available | Binary sensor | Update indication or target assigned to this device |
| Check firmware status | Button | Refresh firmware information; **does not install an update** |
| Wi-Fi signal | Sensor | RSSI in dBm; disabled by default |
| IP address | Sensor | Reported address; disabled by default |
| Last sleep duration / score | Sensors | Estimates from the latest available cloud report |
| Last bedtime / wake-up time | Sensors | Clock times from that report |
| Sleep report date | Timestamp sensor | Date of the report, which may be older than last night |

A missing or invalid measurement stays unknown. The firmware server's default version alone does not trigger an update alert. Firmware installation remains managed by UrbanHello; see the [manufacturer's update instructions](https://www.urbanhello.com/fr/faq/faqs/comment-mettre-a-jour-remi-manuellement-).

## ⏰ Alarm actions

Use the alarm switch and time entity for everyday adjustments. For automation, three actions are available:

| Action | Required fields | Optional fields |
| --- | --- | --- |
| `urbanhello_remi_unofficial.create_alarm` | `name`, `time` | `enabled`, `repeat`, `face_define`, `volume`, `brightness`, `music_path`, `music_duration_minutes`, `play_button_enabled`, `remi_id` |
| `urbanhello_remi_unofficial.update_alarm` | `event_id` | All create fields, including `remi_id` |
| `urbanhello_remi_unofficial.delete_alarm` | `event_id` | `remi_id` |

Times use `HH:MM` or `HH:MM:00` in REMI's time zone. The service's repeat convention remains **Sunday = 0, Monday = 1, …, Saturday = 6**. The app's weekly display starts on Monday; the integration handles the conversion.

```yaml
action: urbanhello_remi_unofficial.create_alarm
data:
  name: Weekday morning
  time: "07:30"
  enabled: true
  repeat: [1, 2, 3, 4, 5]
  face_define: awake
  volume: 40
```

With one loaded REMI, device selection is automatic. With several, specify `remi_id` when creating an alarm. Updating or deleting resolves ownership from `event_id` and checks `remi_id` if supplied. Alarm IDs are available in time entity attributes. See the [full action reference and examples](docs/usage.md#alarm-actions), [history action](docs/usage.md#sleep-and-environmental-history) and [timer profile actions](docs/usage.md#timer-profiles).

## 🔄 Upgrading to 0.4.0

Display labels now follow your Home Assistant language. **Raw face states and music options change to language-independent codes.** Update YAML, templates and state conditions that used the old English values:

| Before | From 0.4.0 |
| --- | --- |
| `Awake` / `Sleepy` | `awake` / `sleepy` |
| `Semi-Awake` | `semi_awake` |
| `Single track` | `single_track` |
| `Repeat playlist` | `repeat_playlist` |

The [complete mapping](docs/usage.md#040-translated-interface-and-stable-state-codes) also covers `Off`, `Smiley`, `Normal`, `Repeat track` and alarm attributes. Use the codes in automations, **not translated display labels**. The `face_define` alarm action's existing `FACE_*` constants remain supported.

This update preserves the integration domain, entity unique IDs and custom names. Automations are not rewritten automatically. Earlier releases also corrected temperature conversion, music modes and brightness entities; review [previous migrations](docs/usage.md#earlier-entity-and-behavior-changes) when upgrading from an older version.

## 🛠️ Troubleshooting and limitations

- **Cloud unavailable or expired login:** check your internet connection and reauthenticate the integration when requested. The selected REMI is retained.
- **Unexpected temperature change after updating:** the corrected conversion is `(raw - 50) / 5`; `160` means `22.0 °C`. Old history is not rewritten. Decimal display does not establish the sensor's physical accuracy.
- **Firmware alert without an install action:** the integration only reads the update status and refreshes it. It cannot install firmware.
- **An automation stopped selecting a face or music mode:** apply the [0.4.0 state mapping](docs/usage.md#040-translated-interface-and-stable-state-codes).
- **A previous brightness or Night Light entity disappeared:** see the [entity migration guide](docs/usage.md#earlier-entity-and-behavior-changes).
- **The new card is missing:** restart Home Assistant after updating, then reload the browser. See [card setup](docs/card.md#troubleshooting).

### 🧪 Beta limitations

- **Sleep reports can be old.** The latest reports available during validation were 9–10 days old. Always check the report date and stale indicator; “last sleep” means the last published report.
- **History uses the app's chart format.** Temperature history follows its °C axis, separately from the live sensor conversion. Noise is relative and light is an overlay, without dB or lux. Sample clocks are available, but absolute timestamps are not reconstructed.
- **Music commands do not prove playback.** Play starts the selected file again; resume position is unknown. Pause and other commands are implemented from the app protocol, with physical behavior still to be validated in this beta.
- **Timer profiles can be created, edited and deleted.** Starting a physical countdown from Home Assistant is not implemented; use the physical timer button on REMI to start a profile.
- **Firmware installation and baby monitor audio are not provided.** The firmware check remains read-only. Night face brightness's physical effect also remains to be confirmed with this fork.

The cloud API may change independently of the integration. See the [usage guide](docs/usage.md) for each feature's limits and the [release notes](CHANGELOG.md) for validation details.

[Usage and migration guide](docs/usage.md) · [Protocol observations](docs/protocol-3.4.23.json) · [Changelog](CHANGELOG.md) · [Report an issue](https://github.com/Mins95/ha-remi/issues)

## 🤝 Development and credits

Contributions should target `main` in [Mins95/ha-remi](https://github.com/Mins95/ha-remi). Use Python 3.14 and an isolated environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install uv==0.13.7
python -m uv pip install -r requirements-test.txt
python -c 'from importlib.metadata import version; assert version("homeassistant") == "2026.11.0"'
python scripts/run_tests.py --cov --cov-report=term-missing
```

Home Assistant requires a Linux test runtime; use WSL on Windows. The tests use the official `pytest-homeassistant==2026.11.0` package paired with the exact Home Assistant release. Create a fresh environment rather than keeping the older `pytest-homeassistant-custom-component` plugin installed alongside it. The runner checks both versions before loading tests. CI uses `python -m uv pip install --system -r requirements-test.txt` in its disposable Python environment.

GitHub Actions runs the test suite against Home Assistant 2026.11.0, plus Hassfest and HACS validation. The Release workflow checks the requested version against the manifest and changelog and runs the tests before publishing. Beta tags are marked as pre-releases and do not become the latest stable release.

Thanks to [timoa](https://github.com/timoa/ha-remi) and the original contributors, and to [pdruart](https://github.com/pdruart/Remi_UrbanHello_hass) for earlier work on REMI alarms and brightness. The product photo belongs to [UrbanHello](https://www.urbanhello.com/fr/).

Community maintained and distributed under the [MIT License](LICENSE).
