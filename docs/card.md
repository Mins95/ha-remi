# The REMI dashboard card

[Back to the README](../README.md) · [Actions and usage](usage.md)

The included **REMI card** brings everyday controls, schedules, sleep reports and timer profiles together. It is included in **0.5.0**, the stable release for **Home Assistant 2026.11.0 or newer**. The interface follows your Home Assistant language, with English and French included.

## Add the card

1. [Install stable 0.5.0 or newer](usage.md#installation), restart Home Assistant and reload the browser page.
2. Open the dashboard where you want to use REMI and choose **Edit dashboard**.
3. Choose **Add card** and find **REMI** in the card picker.
4. If you have several REMI devices, choose one in the visual editor.
5. Save the card and finish editing the dashboard.

With one configured REMI, the card can select it automatically. With several, create one card per device or choose the device explicitly in the editor. The choice uses Home Assistant's device registry, so renamed entity IDs are supported.

The integration loads the bundled card resource automatically. You do not need a separate card repository, JavaScript download or manual resource entry. **Adding the card is your choice:** existing dashboards are not changed automatically.

The card is updated with the integration. Its resource URL includes the integration version and a fingerprint of the bundled source, so source changes also invalidate the old cache. After an upgrade, restart Home Assistant and reload the browser or Companion app page. An already-open page keeps its loaded card until it is reloaded; the integration never forces a reload while you are editing a form.

If you already use the card from 0.5.0-beta.1 or 0.5.0-beta.2, keep your existing dashboard configuration. Updating to stable 0.5.0 preserves the card configuration and entity IDs; a page reload loads the updated resource. Pre-release versions do not need to be enabled for this release.

## Four tabs

| Tab | What you can do |
| --- | --- |
| REMI | Turn the face display on/off, choose Awake/Sleepy and adjust brightness; expand Music for playback and volume |
| Schedules | Review schedules and their times, enable or disable them, and use the schedule editor |
| Sleep | Read the latest published sleep report and request environmental chart data |
| Timers | Manage stored timer/nap profiles shared with the official app |

The French labels are **Rémi**, **Horaires**, **Sommeil** and **Minuteurs**. For individual entities and advanced automation examples, see the [usage guide](usage.md).

### Everyday face controls

The main tab has a **face display on/off control** and two expression choices: **Awake** and **Sleepy** (**Réveillé** and **Endormi** in French). The on/off control changes the displayed face; it does not cut power to REMI.

Turning the display off sends the `off` face. Turning it back on restores the last non-off face seen by the card for that device, or selects `awake` if none is known. All five expressions remain available under **More settings** and through the native clock-face select entity for automations and other dashboard cards.

The **Music** section is collapsed by default. Expand it to choose a track, use playback controls or adjust volume. This keeps the everyday view shorter without removing those controls.

### What the status means

- A displayed music selection is the path selected in the cloud. It does not confirm that audio is playing. Play starts the selected track again; precise resume position is unavailable.
- Sleep values belong to the report date shown. An older report is marked stale and is not presented as last night's measurement.
- History clocks follow the app's noon-to-noon grid. Temperature follows the app chart's °C scale; noise and light do not have calibrated dB or lux units. Absolute sample timestamps are not reconstructed.
- Timer forms save profiles. Use the physical timer button on REMI to start a profile; there is no Home Assistant action that starts it.

The card uses the integration's normal Home Assistant entities and actions. It never asks for UrbanHello credentials. Configure or reauthenticate the integration through **Settings → Devices & services** when needed.

## Optional YAML

The visual editor is sufficient. If you prefer YAML, the minimal configuration for a single REMI is:

```yaml
type: custom:urbanhello-remi-card
```

To select a device explicitly:

```yaml
type: custom:urbanhello-remi-card
device_id: YOUR_HOME_ASSISTANT_DEVICE_ID
```

`device_id` is the Home Assistant device registry ID, as used by the card's editor. It is different from the cloud `remi_id` accepted by advanced integration actions. You do not need to list every entity ID.

## Troubleshooting

- **The card is missing from the picker or reports “Custom element doesn't exist”:** confirm the installed integration is 0.5.0 or newer, restart Home Assistant, then reload the browser or Companion app page. Avoid adding a duplicate resource URL while automatic registration is active.
- **No device is found:** finish the REMI integration setup first and check that its device is loaded. With several devices, select one in the editor.
- **A control is unavailable:** check REMI's connection and the integration's authentication status. Historical reports and live controls have separate availability.
- **Sleep data is old or a chart is empty:** check the report date. The cloud may publish no newer report or file; reloading the card cannot create missing measurements.
- **The music library is empty:** verify that the official app has published a library for the selected device. The card does not invent tracks or upload audio files.

Standard Home Assistant entity and media-player cards remain available if you prefer your own dashboard layout.
