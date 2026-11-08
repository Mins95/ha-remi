# The REMI dashboard card

[Back to the README](../README.md) · [Actions and usage](usage.md)

The included **REMI card** brings everyday controls, schedules, sleep reports and timer profiles together. **0.5.3** clarifies the nightlight brightness label while keeping the separate face brightness control. It requires **Home Assistant 2026.11.0 or newer**. The interface follows your Home Assistant language, with English and French included.

## Add the card

1. [Install stable 0.5.3 or newer](usage.md#installation), restart Home Assistant and reload the browser page.
2. Open the dashboard where you want to use REMI and choose **Edit dashboard**.
3. Choose **Add card** and find **REMI** in the card picker.
4. If you have several REMI devices, choose one in the visual editor.
5. Save the card and finish editing the dashboard.

With one configured REMI, the card can select it automatically. With several, create one card per device or choose the device explicitly in the editor. The choice uses Home Assistant's device registry, so renamed entity IDs are supported.

The integration loads the bundled card resource automatically. You do not need a separate card repository, JavaScript download or manual resource entry. **Adding the card is your choice:** existing dashboards are not changed automatically.

The card is updated with the integration. Its resource URL includes the integration version and a fingerprint of the bundled source, so source changes also invalidate the old cache. After an upgrade, restart Home Assistant and reload the browser or Companion app page. An already-open page keeps its loaded card until it is reloaded; the integration never forces a reload while you are editing a form.

If you already use the card from 0.5.0 or newer, keep your existing dashboard configuration. Updating to 0.5.3 preserves the card configuration and entity IDs; a page reload loads the updated resource. Pre-release versions do not need to be enabled for this release.

## Choose what to display

Open the card's visual editor to show or hide the face selector, each brightness control, temperature, connection status, Music and the Schedules, Sleep or Timers tabs. All options default to visible, so an existing card keeps its layout. Music starts collapsed.

For a compact everyday card, keep the face and brightness controls and hide the secondary tabs you do not use. Hiding a section changes only this card; entities, schedules and device settings remain available elsewhere in Home Assistant. The main REMI tab is always available.

The optional YAML keys are `show_face`, `show_brightness`, `show_face_brightness`, `show_temperature`, `show_connection`, `show_music`, `show_alarms`, `show_sleep` and `show_naps`. Each accepts `true` or `false`; no YAML is required when using the visual editor.

## Four tabs

| Tab | What you can do |
| --- | --- |
| REMI | Turn the face display on/off, choose Awake/Sleepy and adjust brightness; expand Music for playback and volume |
| Schedules | Review schedules and their times, enable or disable them, and use the schedule editor |
| Sleep | Choose an available recording period, read its sleep report and request its environmental charts |
| Timers | Manage stored timer/nap profiles shared with the official app |

The French labels are **Rémi**, **Horaires**, **Sommeil** and **Minuteurs**. For individual entities and advanced automation examples, see the [usage guide](usage.md).

### Two separate brightness controls

**Nightlight brightness** (**Luminosité de la veilleuse**) controls the nightlight on a 0–100 scale. The slider below, **Face brightness** (**Luminosité du visage**), keeps its separate 1–10 scale and behavior. Both labels appear in the visual editor; schedule and timer forms use **Nightlight brightness** for their 0–100 setting. Existing entity IDs and card settings are preserved.

### Everyday face controls

The main tab has a **face display on/off control** and two expression choices: **Awake** and **Sleepy** (**Réveillé** and **Endormi** in French). The on/off control changes the displayed face; it does not cut power to REMI.

Turning the display off sends the `off` face. Turning it back on restores the last non-off face seen by the card for that device, or selects `awake` if none is known. All five expressions remain available under **More settings** and through the native clock-face select entity for automations and other dashboard cards.

The **Music** section is collapsed by default. Expand it to choose a track, use playback controls or adjust volume. This keeps the everyday view shorter without removing those controls.

### What the status means

- A displayed music selection is the path selected in the cloud. It does not confirm that audio is playing. Play starts the selected track again; precise resume position is unavailable.
- Sleep values and charts belong to the same selected recording period. The period and the latest cloud export time are shown separately.
- History clocks follow the app's noon-to-noon grid. Temperature follows the app chart's °C scale; noise and light do not have calibrated dB or lux units. Absolute sample timestamps are not reconstructed.
- Timer forms save profiles. Use the physical timer button on REMI to start a profile; there is no Home Assistant action that starts it.

The card uses the integration's normal Home Assistant entities and actions. It never asks for UrbanHello credentials. Configure or reauthenticate the integration through **Settings → Devices & services** when needed.

### Choose a sleep period

The Sleep tab lists up to **60 available cloud journals**. Use the date selector or arrows to move between available periods; gaps in the cloud catalogue are not filled with invented days. A period runs from the previous day to the journal's UTC calendar date, matching the app's noon-to-noon view. The journal timestamp's hour is not an export time or a proven sample timestamp.

The four sleep values and the optional charts always come from the same selected journal. A current period may still be recording, with no sleep estimate yet. A zero sleep score or zero sleep duration is shown as unavailable, as in the app; midnight remains a valid bedtime or wake-up time. The separate native Home Assistant sensors prefer the latest completed report with a valid sleep estimate, when one is available, so they may describe a different period from the one selected in the card.

If the device time zone is unavailable, native sensors can retain an available sleep estimate without claiming that its period is completed.

**Cloud export** shows when that journal was last updated, using `updated_at`. An export older than 48 hours is marked stale. This date is distinct from the recording period and from the time Home Assistant last fetched it.

Choose **Show environmental charts** to load temperature, noise and light for the selected period. Ambiguous zero bytes in historical temperature remain gaps instead of being displayed as −10 °C. The card does not join lines across missing samples. Zero noise and light values remain valid; the integration does not treat every zero as missing.

### Refresh sleep data

The Sleep tab's **Refresh** button explicitly asks REMI to export its current journal, waits about **12 seconds**, then reads the cloud again. A **60-second cooldown** prevents repeated export commands; pressing it during that interval only rereads the available cloud data. Opening the tab, changing periods, viewing charts and normal background polling do not send this command.

The export command has been verified on a physical REMI and refreshed its current journal. It does not guarantee recovery of missing earlier days or creation of a completed sleep estimate. For a cloud-only refresh without asking the device to export, use the [history action with `refresh: true` and `sync: false`](usage.md#request-history-data).

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
- **Sleep data is old or a chart is empty:** check the selected period and its Cloud export time. Try Refresh to request a new export of the current journal. A period may have no sleep estimate or chart file, and earlier missing days are not guaranteed to return.
- **The music library is empty:** verify that the official app has published a library for the selected device. The card does not invent tracks or upload audio files.

Standard Home Assistant entity and media-player cards remain available if you prefer your own dashboard layout.
