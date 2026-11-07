<p align="center">
  <img src="images/header.svg" alt="UrbanHello REMI for Home Assistant" width="100%">
</p>

<h1 align="center">UrbanHello REMI for Home Assistant</h1>

<p align="center">
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2026.11%2B-41BDF5?style=for-the-badge&amp;logo=home-assistant&amp;logoColor=white" alt="Home Assistant 2026.11 or newer"></a>
  <a href="https://my.home-assistant.io/redirect/marketplace_repository/?owner=Mins95&amp;repository=ha-remi&amp;category=integration"><img src="https://img.shields.io/badge/Marketplace-Custom-0080ff?style=for-the-badge" alt="Custom Marketplace repository"></a>
  <a href="https://github.com/Mins95/ha-remi/releases/latest"><img src="https://img.shields.io/github/v/release/Mins95/ha-remi?style=for-the-badge&amp;label=Latest%20release&amp;color=0080ff" alt="Latest stable release"></a>
  <a href="https://github.com/Mins95/ha-remi/releases"><img src="https://img.shields.io/github/downloads/Mins95/ha-remi/total?style=for-the-badge&amp;label=Downloads&amp;color=0080ff" alt="Release asset downloads"></a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="MIT license"></a>
  <a href="https://github.com/Mins95/ha-remi/stargazers"><img src="https://img.shields.io/github/stars/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="Stars"></a>
  <a href="https://github.com/Mins95/ha-remi/issues"><img src="https://img.shields.io/github/issues/Mins95/ha-remi?style=flat-square&amp;color=0080ff" alt="Open issues"></a>
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/tests.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/tests.yml/badge.svg?branch=main" alt="Tests"></a>
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/hassfest.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/hassfest.yml/badge.svg?branch=main" alt="Hassfest"></a>
  <a href="https://github.com/Mins95/ha-remi/actions/workflows/hacs.yml"><img src="https://github.com/Mins95/ha-remi/actions/workflows/hacs.yml/badge.svg?branch=main" alt="HACS validation"></a>
</p>

<p align="center">
  Your REMI, its schedules and its sleep reports in one dashboard card.<br>
  Everyday controls in English or French, following your Home Assistant language.
</p>

**0.5.2 is the current stable release.** Requires Home Assistant **2026.11.0 or newer**, a REMI configured in the UrbanHello app and internet access.

## Your REMI dashboard

<p align="center">
  <a href="images/remi-dashboard.jpg"><img src="images/remi-dashboard.jpg" alt="REMI dashboard card with face controls, temperature, brightness and collapsed music controls" width="380"></a><br>
  <sub>Actual Home Assistant dashboard · French interface · Light theme</sub>
</p>

## What you can do

- **Control the face and brightness:** on/off, Awake/Sleepy and separate display/night brightness.
- **Manage schedules:** see their times, toggle them and edit their settings.
- **Follow the room and sleep:** decimal temperature, dated sleep reports and environmental charts.
- **Access music and timers:** a collapsible music panel and up to five stored timer profiles.

The card updates with the integration. Existing entity IDs and dashboard configurations are preserved. [Features and limitations →](docs/usage.md)

## Quick installation

[![Open in Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=Mins95&repository=ha-remi&category=integration)

1. In **Settings → Marketplace → Add from link**, add `https://github.com/Mins95/ha-remi` and install **Remi (Mins95)**.
2. Restart Home Assistant, then add **Remi** under **Settings → Devices & services** using your UrbanHello account.
3. Add **REMI** from your dashboard's card picker. No separate card download or YAML is needed.

**Already installed?** Update to **0.5.2**, restart Home Assistant and reload the browser or Companion app. Keep your existing integration and card.

[HACS, manual installation and repository changes →](docs/usage.md#installation)

## Documentation

| Guide | Contents |
| --- | --- |
| [Dashboard card](docs/card.md) | Setup, tabs and everyday controls |
| [Usage](docs/usage.md) | Installation, entities, actions and examples |
| [Upgrading](docs/usage.md#upgrading) | Migration from older versions and betas |
| [Troubleshooting](docs/usage.md#troubleshooting) | Connection, firmware and feature limits |
| [Development](docs/development.md) | Test environment, contributions and releases |
| [Changelog](CHANGELOG.md) | Release notes in French |

## Credits

Community integration maintained by [Mins95](https://github.com/Mins95), based on [timoa/ha-remi](https://github.com/timoa/ha-remi).

Thanks to [timoa](https://github.com/timoa/ha-remi) and the original contributors, and to [pdruart](https://github.com/pdruart/Remi_UrbanHello_hass) for earlier work on REMI alarms and brightness.

Additional ideas and interoperability findings: [Jbis-4](https://github.com/Jbis-4/ha-remi), [ADNPolymerase and homeassistant-fr-ecosystem](https://github.com/homeassistant-fr-ecosystem/urbanhello_remi_hass), and [P-clean / JeeRemi](https://github.com/P-clean/jeedom-jeeremi).

Product photo © [UrbanHello](https://www.urbanhello.com/fr/) · [Original image](https://www.urbanhello.com/img/cms/UH-REMI-Bleu-Simple.webp). This project is not affiliated with or endorsed by UrbanHello.

Community maintained and distributed under the [MIT License](LICENSE).
