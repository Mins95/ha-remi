# The REMI dashboard card

[Back to the README](../README.md) · [Actions and usage](usage.md)

The included **REMI card** brings everyday controls, schedules, sleep reports and timer profiles together. It requires **Home Assistant 2026.11.0 or newer**. The interface follows your Home Assistant language, with English and French included.

## Add the card

1. [Install stable 0.6.0 or newer](usage.md#installation), restart Home Assistant and reload the browser page.
2. Open the dashboard where you want to use REMI and choose **Edit dashboard**.
3. Choose **Add card** and find **REMI** in the card picker.
4. If you have several REMI devices, choose one in the visual editor.
5. Save the card and finish editing the dashboard.

With one configured REMI, the card can select it automatically. With several, create one card per device or choose the device explicitly in the editor. The choice uses Home Assistant's device registry, so renamed entity IDs are supported.

The integration loads the bundled card resource automatically. You do not need a separate card repository, JavaScript download or manual resource entry. **Adding the card is your choice:** existing dashboards are not changed automatically.

The card is updated with the integration. Its resource URL includes the integration version and a fingerprint of the bundled source, so source changes also invalidate the old cache. After an upgrade, restart Home Assistant and reload the browser or Companion app page. An already-open page keeps its loaded card until it is reloaded; the integration never forces a reload while you are editing a form.

If you already use the card from 0.5.0 or newer, keep your existing dashboard configuration. Updating to 0.6.0 preserves the card configuration and entity IDs. Reload the page to load the updated card.

## Choose what to display

Open the card's visual editor to show or hide the face selector, each brightness control, temperature, connection status, Music and the Schedules, Sleep or Timers tabs. These sections default to visible, so an existing card keeps its layout. Music starts collapsed. The new custom button is hidden until enabled.

Choose the compact layout to reduce the space used by the header and face, or hide secondary tabs you do not use. Hiding a section changes only this card; entities, schedules and device settings remain available elsewhere in Home Assistant. The main REMI tab is always available.

The optional YAML keys are `show_face`, `show_brightness`, `show_face_brightness`, `show_temperature`, `show_connection`, `show_music`, `show_alarms`, `show_sleep` and `show_naps`. Each accepts `true` or `false`; no YAML is required when using the visual editor.

## Appearance and layout

The editor also lets you select a **temperature sensor** from Home Assistant. Under the temperature, the card shows the last report time as **Update: HH:mm** in Home Assistant’s time zone. Hover over the reading to see the sensor name. Clearing the selection restores REMI’s own reading. In YAML, set `temperature_entity` to the sensor entity ID. REMI’s historical curves always use its own readings.

Choose these options in the visual editor:

| Option | Choices |
| --- | --- |
| Appearance | **Home Assistant theme** (`theme`, default), **REMI turquoise** (`remi`) or **Dark glass** (`glass`, translucent dark blue) |
| Layout | **Normal** (`full`, default) or **Compact** (`compact`, useful on a wall tablet or Tap Scheduler) |

Normal keeps larger labels and an everyday control layout, with short schedule rows and tighter sleep controls. Compact goes further by grouping face controls and brightness sliders into smaller panels. Both modes keep the same configured controls and touch targets of at least 44 px. Narrow screens can wrap content; expanded panels and long personal buttons still need additional room. Sections dashboards use automatic card height so expanded panels and forms remain inside their allocated space. An explicit dashboard height override can still constrain the card; remove a fixed `grid_options.rows` value if content overlaps.

In Compact, the schedule list starts collapsed to save space on a Tap Scheduler. In Normal, it starts expanded. Tap the schedule summary in either layout to open or close the list. The count shows how many schedules are enabled out of the total. The next wake-up and bedtime appear when Home Assistant can calculate them.

Tap the alarm-clock icon on a schedule, then **Test now** to apply its face, nightlight brightness and volume to the physical REMI. A configured track may start playing. Testing leaves the saved schedule in place. During a cloud outage the last saved schedules are available for viewing.

Compact also uses a shorter sleep chart, four summary values across when space allows, and an information icon beside the chart selector. The date selector, refresh action, chart values, gaps and face markers remain available.

Normal groups the heading and tabs in one row and uses a horizontal REMI preview. Four tabs move below the heading on narrow cards. The two brightness sliders stay side by side when there is enough room; very narrow cards stack them to keep labels readable. Sliders use the same round handle and thin track across browsers, with a full touch area and keyboard support. Open panels and personal buttons keep the space they need.

```yaml
type: custom:urbanhello-remi-card
appearance: glass
layout: compact
```

## Optional custom button

Enable **Show a custom action** in the visual editor. Select an existing script, automation, scene, button or input button, then optionally choose its label and icon. This configuration belongs to your dashboard; the integration does not create or publish your scripts.

```yaml
type: custom:urbanhello-remi-card
show_custom_button: true
custom_button:
  mode: entity
  entity: script.example_routine
  name: My routine
  icon: mdi:play-circle-outline
```

The button runs the selected entity's normal action. Automation conditions are respected unless **Skip automation conditions** is explicitly enabled (`skip_conditions: true`). An automation's disabled state does not prevent an explicit manual trigger. Scripts already running and unavailable entities are disabled; commands are never retried automatically.

### Keep an existing button and its long-press action

Choose **Existing Lovelace card**, then use the YAML editor to place the complete original card configuration under `custom_button.card`. Its own tap, hold and double-tap actions, templates and styling remain intact. Existing custom-card dependencies, such as Mushroom or Browser Mod, must already be installed in Home Assistant.

```yaml
type: custom:urbanhello-remi-card
show_custom_button: true
custom_button:
  mode: card
  card:
    type: button
    entity: script.example_routine
    name: My routine
    tap_action:
      action: perform-action
      perform_action: script.turn_on
      target:
        entity_id: script.example_routine
    hold_action:
      action: more-info
```

Home Assistant creates the embedded card using its normal card helpers. Its element stays mounted during REMI updates, so an update does not interrupt an ongoing long press. Hide the custom button without deleting its settings using the visual editor or `show_custom_button: false`.

## Firmware update indicator

An update icon appears beside the connection status when the integration's **Firmware update available** sensor is on. Pressing it opens the sensor details; it does not start a firmware update. Unknown, unavailable or missing update information does not produce an alert. Hiding the connection status also hides this indicator.

## Four tabs

| Tab | What you can do |
| --- | --- |
| REMI | Turn the face display on/off, choose Awake/Sleepy and adjust brightness; expand Music for playback and volume |
| Schedules | Check the next wake-up and bedtime. Expand the list to enable, disable, edit or test a schedule |
| Sleep | Choose an available recording period, read its sleep report and view its environmental charts |
| Timers | Manage stored timer/nap profiles shared with the official app |

The French labels are **Rémi**, **Horaires**, **Sommeil** and **Minuteurs**. For individual entities and advanced automation examples, see the [usage guide](usage.md).

### Two separate brightness controls

**Nightlight brightness** (**Luminosité de la veilleuse**) controls the nightlight on a 0–100 scale. **Face brightness** (**Luminosité du visage**) uses 0–10 in the card: **0 turns the face off**, and 1–10 sets its brightness. When the face is off, raising the slider first sets the requested brightness, then restores the last non-off expression observed by this card for that REMI, or Awake when none is known.

The native face-brightness number entity remains on the app's supported 1–10 scale. The card's zero position sends the existing face-off command; it never writes an unsupported zero brightness. Both labels appear in the visual editor; schedule and timer forms use **Nightlight brightness** for their 0–100 setting. Existing entity IDs and card settings are preserved.

### Everyday face controls

The main tab has two expression choices: **Awake** and **Sleepy** (**Réveillé** and **Endormi** in French). There is no separate face power switch: use **Face brightness → 0** to turn the face off. This changes the displayed face without cutting power to REMI.

The slider follows confirmed device state, and unavailable values are not presented as zero. If setting brightness fails, the card does not continue with the restore-face command. All five expressions remain available under **More settings** and through the native clock-face select entity for automations and other dashboard cards. Hiding the expression choices does not disable the separately visible face-brightness slider.

The **Music** section is collapsed by default. Expand it to choose a track, use playback controls or adjust volume. This keeps the everyday view shorter without removing those controls.

### What the status means

- A displayed music selection is the path selected in the cloud. It does not confirm that audio is playing. Play starts the selected track again; precise resume position is unavailable.
- Sleep values and charts belong to the same selected recording period. The period and the latest cloud export time are shown separately.
- History clocks follow the app's noon-to-noon grid. Temperature follows the app chart's °C scale; noise and light do not have calibrated dB or lux units. Absolute sample timestamps are not reconstructed.
- Timer forms save profiles. Use the physical timer button on REMI to start a profile; there is no Home Assistant action that starts it.

The card uses the integration's normal Home Assistant entities and actions. It never asks for UrbanHello credentials. Configure or reauthenticate the integration through **Settings → Devices & services** when needed.

### Choose a sleep period

The Sleep tab lists up to **60 available journals**, including nights saved on this Home Assistant instance. Use the date selector or arrows to move between recording periods. A period runs from the previous day to the journal's UTC calendar date, matching the app's noon-to-noon view.

Sleep values and charts come from the same selected journal. The card opens an available curve, even when a night has no score. The chart selector offers temperature, noise and the app’s light reference. A message identifies curves from an earlier export. **Latest available sleep estimate** switches to a completed journal with an estimate.

A zero sleep score or zero sleep duration is shown as unavailable, as in the app; midnight remains a valid bedtime or wake-up time. The integration does not calculate missing sleep estimates from environmental curves. The separate native Home Assistant sensors prefer the latest completed report with a valid sleep estimate, when one is available, so they may describe a different period from the one selected in the card.

If the device time zone is unavailable, native sensors can retain an available sleep estimate without claiming that its period is completed.

Expand **About these data** for the journal's **Cloud export** (`updated_at`) and separate **Sleep estimate updated** (`sleep_updated_at`) dates. These dates are distinct from the recording period and Home Assistant's fetch time. An unfinished period with an export older than 48 hours is marked stale; an old completed period is normal history.

One environmental chart is displayed at a time, using fixed scales to compare dates: temperature −10 to 40 °C, noise on the app's relative 0–100 scale, and the app's binary light reference. Noise is not measured in calibrated decibels; the light reference is not a lux measurement. Ambiguous zero bytes in historical temperature remain gaps instead of being displayed as −10 °C. The card does not join lines across missing samples. Zero noise and light values remain valid; the integration does not treat every zero as missing. Charts can be hidden or shown again under **About these data**.

When available, face markers reproduce the app's recorded expression changes. They are not detected bedtimes or wake-up times. Their clock positions follow the app; no absolute sample timestamps are inferred.

### Refresh sleep data

The Sleep tab's **Refresh** button explicitly asks REMI to export its current journal, waits about **12 seconds**, then reads the cloud again. A **60-second cooldown** prevents repeated export commands; pressing it during that interval only rereads the available cloud data. This cannot force the cloud to generate a missing sleep estimate for an older period.

Opening the tab, changing periods and viewing charts only read data. The card rereads its cloud catalogue after 20 minutes when returning to Sleep or receiving a Home Assistant state update while that tab is open. It preserves the selected period and reloads its visible chart detail. A failed automatic read waits another 20 minutes before retrying. These passive refreshes never request a device export.

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
