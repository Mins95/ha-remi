# REMI usage and upgrade guide

[Back to the README](../README.md) · [Dashboard card](card.md) · [Changelog](../CHANGELOG.md)

This guide covers the public Mins95 integration, its Home Assistant actions and changes from earlier versions. It requires an UrbanHello account and internet access. Example entity IDs and alarm IDs are placeholders: use the IDs from your own installation.

**0.5.0-beta.1 requires Home Assistant 2026.11.0 or newer.** It is an opt-in beta; 0.4.0 remains the latest stable release. Start with the [included dashboard card](card.md) for a visual interface to the features below.

## Everyday controls

Open **Settings → Devices & services → Remi**, then select your device, or add the REMI card to your dashboard. Its entities also work in standard Home Assistant cards and automations.

| Setting | Range or values | Behavior |
| --- | --- | --- |
| Brightness | Integer 0–100 | Upper light; 0 turns it off |
| Night face brightness | Integer 1–10 | Face brightness in darkness |
| Volume | 0–100 | Speaker volume |
| Noise notification threshold | 0–250 | Threshold used for sound notifications |
| Clock face | `off`, `awake`, `sleepy`, `semi_awake`, `smiley` | Displayed expression |
| Clock format | `12h`, `24h` | Clock display format |
| Music mode | `normal`, `single_track`, `repeat_track`, `repeat_playlist` | Playback repeat behavior |
| App background color | RGB color | Color associated with REMI in the official app |

The interface translates supported labels into English or French according to your Home Assistant language. Use the raw codes above in YAML and templates. Changing your interface language does not change these codes.

### Brightness

The two brightness entities control separate settings:

- **Brightness** writes `luminosity` on REMI's 0–100 scale. It is a numeric value with no separate on/off state or remembered previous intensity.
- **Night face brightness** writes `light_min` on the app's 1–10 scale. It changes only this setting, then refreshes the device. It does not modify light calibration, clock face or schedules.

Missing, invalid or out-of-range values are shown as unknown. Night face brightness requires whole numbers; fractions and non-finite values are rejected.

```yaml
action: number.set_value
target:
  entity_id: number.example_night_face_brightness
data:
  value: 3
```

The [UrbanHello brightness guide](https://www.urbanhello.com/fr/faq/faqs/gerer-la-luminosite-de-remi) describes the night face setting. The implementation is covered by API tests; its physical effect has not yet been verified with this fork.

### Face and music options

Select a face using its stable code:

```yaml
action: select.select_option
target:
  entity_id: select.example_clock_face
data:
  option: sleepy
```

The music selector changes playback behavior, not the selected audio file. It does not start or stop playback.

```yaml
action: select.select_option
target:
  entity_id: select.example_music_mode
data:
  option: repeat_playlist
```

### Music player

The separate media player browses the cloud library associated with the selected REMI. Choose a track from its media browser to play an existing file. The integration does not upload files, stream arbitrary URLs or expose baby monitor audio.

| Control | Behavior |
| --- | --- |
| Browse media | Lists the selected REMI's known files; an empty library is a valid result |
| Play a track | Sends the selected library path to REMI |
| Play | Starts the selected file again; it does not guarantee resuming its previous position |
| Pause / Stop | Sends the corresponding app command |
| Previous / Next | Selects the adjacent known file in the same folder; stops at the folder's boundaries |
| Volume | Sets speaker volume |
| Repeat | Off, one track or all tracks; the separate music-mode selector also exposes single-track mode |

**Playback state stays unknown.** A cloud-selected path does not confirm that the speaker is playing, paused or stopped. The player does not manufacture a duration or playback position. Commands are implemented from the app protocol, but their physical effect remains to be validated in this beta.

If the library is empty, check the tracks available in the official app. A missing selection raises a clear error; Play does not guess a file.

### Temperature

The Celsius conversion is `(raw - 50) / 5`. For example, raw `160` means **22.0 °C**. Decimal values are retained, with a suggested display precision of one decimal place. The official app displays an integer.

The raw measurement and conversion formula are available in the sensor's attributes. Missing or invalid readings remain unknown. Decimal display preserves the reported value; it does not prove that the physical sensor is accurate to a tenth of a degree.

Historical temperatures are not rewritten. A step in a graph after updating may reflect the corrected conversion rather than a change in room temperature. The [protocol observations](protocol-3.4.23.json) record the relevant interoperability facts.

### Firmware status

The **Firmware update available** entity uses the device's `firmware_need_update` indication or its assigned `update_firmware_version`. A server-wide default version is informational and does not establish that an update is available for this particular REMI.

Attributes expose the installed version, assigned target and server default when available. If device-specific information is missing, the update state stays unknown. Firmware metadata is cached for an hour; **Check firmware** refreshes it and the device state.

**Check firmware never installs firmware.** Use the official app and [UrbanHello's update instructions](https://www.urbanhello.com/fr/faq/faqs/comment-mettre-a-jour-remi-manuellement-) for firmware installation.

## Alarm actions

Each discovered schedule provides a switch and a time entity. A switch's default name includes its time and name, for example **07:30 · Weekday morning**. Existing entity IDs and user-assigned names are preserved. New, renamed or deleted cloud schedules are reconciled after a successful refresh; a temporary read failure does not remove them.

Use the card's Schedules tab for visual editing, the switch to enable a schedule, or the time entity to adjust its hours and minutes.

```yaml
action: time.set_value
target:
  entity_id: time.example_weekday_morning
data:
  time: "07:30:00"
```

The three integration actions below are available in **Developer tools → Actions**, scripts and automations.

### Time and repeat conventions

- `time` accepts `HH:MM` or `HH:MM:00` in REMI's time zone.
- Seconds must be zero. Date-time strings and nonzero seconds are rejected.
- `repeat` uses integers **0 = Sunday, 1 = Monday, 2 = Tuesday, 3 = Wednesday, 4 = Thursday, 5 = Friday, 6 = Saturday**.
- The cloud's recurrence array and the app's weekly display begin on Monday. The integration converts the service's existing Sunday-first convention.
- `repeat: []` selects no repeat days.

For weekdays use `[1, 2, 3, 4, 5]`; for Saturday and Sunday use `[6, 0]`.

### Create an alarm

Action: `urbanhello_remi_unofficial.create_alarm`.

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Schedule name |
| `time` | Yes | Time in REMI's time zone |
| `enabled` | No | Whether the schedule is active; defaults to `true` |
| `repeat` | No | List of day numbers; defaults to `[]` |
| `face_define` | No | Face to display; supported codes and constants are listed below |
| `volume` | No | Alarm volume, 0–100 |
| `brightness` | No | Upper light brightness at this schedule, 0–100 |
| `music_path` | No | Existing REMI audio file path; an empty string removes the scheduled track |
| `music_duration_minutes` | No | Music duration in minutes, 0–1440 |
| `play_button_enabled` | No | Enable or disable the Play button setting associated with this schedule |
| `remi_id` | No with one REMI | Cloud REMI ID; required to choose among multiple loaded devices |

With exactly one loaded REMI, omit `remi_id`. With several devices, use the visual card's device selector or supply the target's cloud REMI ID. This is distinct from a Home Assistant entity ID and from the card's `device_id`.

```yaml
action: urbanhello_remi_unofficial.create_alarm
data:
  name: Weekday morning
  time: "07:30"
  enabled: true
  repeat: [1, 2, 3, 4, 5]
  face_define: awake
  volume: 40
  brightness: 15
```

The form displays translated face labels and uses the following codes. Existing `FACE_*` constants remain accepted for compatibility:

| Code | Existing constant | Meaning |
| --- | --- | --- |
| `off` | `FACE_OFF` | Off |
| `awake` | `FACE_DAY` | Awake |
| `sleepy` | `FACE_NIGHT` | Sleepy |
| `semi_awake` | `FACE_SEMI_AWAKE` | Semi-awake |
| `smiley` | `FACE_SMILY` | Smiley |

Only alarm actions accept the old `FACE_*` constants. The clock face select entity uses the lowercase codes.

For a scheduled track, enter the path of a file already present on REMI. The media player's library is a separate playback control. Action calls accept a device-relative path, not an internet URL. The music duration uses minutes, including zero as accepted by the app's data format.

For some older schedules, changing the Play button setting requires saving that schedule in the official app first. The integration explains this in its error message and leaves unrecognized settings untouched.

### Update an alarm

Action: `urbanhello_remi_unofficial.update_alarm`.

Only `event_id` is required. All create-action fields are optional: supply only those you want to change. The integration resolves the owning loaded REMI from the alarm's ID and checks the target if you also supply `remi_id`.

Find `event_id` in the attributes of the corresponding alarm time entity. It is the cloud alarm object's ID, not the Home Assistant entity ID.

```yaml
action: urbanhello_remi_unofficial.update_alarm
data:
  event_id: "YOUR_ALARM_ID"
  time: "08:00"
```

### Delete an alarm

Action: `urbanhello_remi_unofficial.delete_alarm`.

This removes the schedule from REMI's cloud account and therefore from the official app as well. To keep a schedule but stop using it, turn off its alarm switch instead.

```yaml
action: urbanhello_remi_unofficial.delete_alarm
data:
  event_id: "YOUR_ALARM_ID"
```

## Sleep and environmental history

The latest available cloud sleep report provides five sensors:

| Sensor | Value |
| --- | --- |
| Last sleep duration | Duration in minutes |
| Last sleep score | Cloud estimate, 0–100, without a physical unit |
| Last bedtime | Clock time as `HH:MM` |
| Last wake-up time | Clock time as `HH:MM` |
| Sleep report date | The cloud journal's timestamp |

These are historical reports, so they remain readable when REMI is offline. A history API failure affects the history entities independently of live controls. Invalid or missing fields stay unknown; a valid zero is preserved.

**“Last” means the last published report, not necessarily last night.** The most recent reports available during validation were 9–10 days old. The sensors expose `log_timestamp`, `report_age_days` and `stale`; a report older than 48 hours is marked stale. Bedtime and wake-up times are retained as the server supplied them, without inventing a date from a clock time.

### Request chart data

Action: `urbanhello_remi_unofficial.get_history`. It returns a response and does not change the device. `limit` is 1 or 2; it defaults to 2. Select a device with `remi_id` only when needed.

```yaml
action: urbanhello_remi_unofficial.get_history
data:
  limit: 2
response_variable: remi_history
```

The response contains `logs`, a metadata `fetched_at` time and the configured `timezone`. Each log includes its `log_timestamp`, sleep fields, `report_age_days`, `stale`, and three `series`: `temperature`, `noise`, `light`. A series has a `status` (`available`, `missing`, `empty` or `unavailable`) and bounded `samples`.

Each sample exposes `index`, `minute_offset`, `clock`, `value`, `raw_value` and `graph_value`. The format has 720 positions, two minutes apart, on the app's **12:00 → 11:58** clock grid. **Absolute sample timestamps are not established**, so `absolute_sample_timestamps` is false. Do not treat the journal's timestamp as a proven start time or insert reconstructed values into Recorder.

| Series | `value` | `graph_value` |
| --- | --- | --- |
| Temperature | °C using the app chart's continuous axis: `raw * 50 / 255 - 10` | The app's 0–100 chart position |
| Noise | Raw 0–255 relative level, without dB | `raw * 100 / 255` |
| Light | Raw byte, without lux | The app's overlay: 100 for raw values 1–7, otherwise 0 |

Historical temperature uses a different scale from the live sensor's `(raw - 50) / 5` conversion. The response names its source as `app_chart_axis` and retains decimals and raw values. This reproduces the graph's scale; it does not independently calibrate the physical sensor. Boundary bytes 0 and 255 are retained and identified in `boundary_values_not_calibrated`, because their meaning as missing data, saturation or measurement is not established.

Metadata refreshes every 20 minutes. Binary chart files are fetched only on demand, with a bounded memory cache. A failed file appears as unavailable without hiding the other series or the sleep report. No historical values are retroactively inserted into Home Assistant's recorder.

## Timer profiles

The Timers tab and actions manage the app's **stored timer/nap profiles**, with a maximum of five profiles. They do not start a physical countdown from Home Assistant; use the physical timer button on REMI to start a profile. Profiles are shared with the UrbanHello account, so edits and deletions affect the official app too.

| Action | Required fields | Response |
| --- | --- | --- |
| `urbanhello_remi_unofficial.list_naps` | None with one REMI | `profiles` list, including each `nap_id` |
| `urbanhello_remi_unofficial.create_nap` | `name`, `duration_minutes` | Optional response containing the new `nap_id` |
| `urbanhello_remi_unofficial.update_nap` | `nap_id` and at least one setting | — |
| `urbanhello_remi_unofficial.delete_nap` | `nap_id` | — |

Every action accepts optional `remi_id`. Omit it for one loaded device; supply it when choosing among several. Listing requires a response, so use `response_variable` in a script:

```yaml
action: urbanhello_remi_unofficial.list_naps
data: {}
response_variable: remi_timers
```

The create and update actions accept these settings:

| Setting | Values | Default on creation |
| --- | --- | --- |
| `name` | Nonempty name, up to 100 characters | Required |
| `duration_minutes` | Whole minutes, 1–1439 | Required |
| `face` | `off`, `awake`, `sleepy`, `semi_awake`, `smiley` | `sleepy` |
| `brightness` | Integer 0–100 | 0 |
| `sleep_aid` | `true` or `false`, as in the app's profile | `false` |
| `music_path_start`, `music_path_end` | Existing REMI file paths, or an empty string | Empty |
| `volume_start`, `volume_end` | Integer 0–100 | 50 |
| `music_duration_start_minutes`, `music_duration_end_minutes` | Integer 0–1440 | 0 |

```yaml
action: urbanhello_remi_unofficial.create_nap
data:
  name: Afternoon nap
  duration_minutes: 45
  face: sleepy
  brightness: 0
response_variable: new_remi_timer
```

To edit a profile, get its `nap_id` with `list_naps` and supply only the fields to change. The integration checks device ownership before updating or deleting a profile. Creating a sixth profile is rejected with a clear message.

## Upgrading

<a id="upgrading-from-030"></a>

### 0.5.0-beta.1: new controls and dashboard card

This release requires **Home Assistant 2026.11.0 or newer**. Its automated runtime checks target 2026.11.0 exactly. The beta is published as a pre-release; **0.4.0 remains the latest stable release**.

- **Marketplace:** enable the disabled-by-default **Pre-release** switch on this repository's Marketplace device, then turn it on and select 0.5.0-beta.1 from available updates.
- **HACS:** enable **Show beta versions** for this repository, then select 0.5.0-beta.1 when updating.

Restart Home Assistant after installing and reload the browser. The included card is registered automatically; [add it to your dashboard](card.md) through the card picker. The integration does not create or replace dashboard cards automatically.

Existing entity IDs and custom names are retained. Alarm switches gain a time in their default display name; the existing time entity remains available. New history sensors and a media player appear on the REMI device. Existing action calls still work; the additional alarm fields are optional.

Read the [music limitations](#music-player), [history time and unit conventions](#sleep-and-environmental-history) and [timer profile scope](#timer-profiles) before building automations around the new features. Firmware installation is unchanged and remains managed by UrbanHello.

### 0.4.0: translated interface and stable state codes

Version 0.4.0 provides English and French display labels for entities, settings, actions, errors and supported entity states. User-assigned entity names and alarm names are retained. Entity unique IDs and the integration domain remain the same.

To support language-independent automation values, face and music states/options now use lowercase codes. **Update scripts, templates, state triggers, conditions and `select.select_option` calls that use the old values.** The integration does not rewrite automations or historical states.

| Entity | Previous raw value | Raw value from 0.4.0 |
| --- | --- | --- |
| Clock face / Current face | `Off` | `off` |
| Clock face / Current face | `Awake` | `awake` |
| Clock face / Current face | `Sleepy` | `sleepy` |
| Clock face / Current face | `Semi-Awake` | `semi_awake` |
| Clock face / Current face | `Smiley` | `smiley` |
| Music mode | `Normal` | `normal` |
| Music mode | `Single track` | `single_track` |
| Music mode | `Repeat track` | `repeat_track` |
| Music mode | `Repeat playlist` | `repeat_playlist` |

The same face mapping applies to an alarm switch's `face` attribute. Update templates that compare this attribute. The `recurrence` attribute keeps its lowercase day codes (`mon` through `sun`), and the `repeat` action input keeps its numeric convention.

Use these codes even when Home Assistant displays a French label. For example:

```yaml
condition: state
entity_id: sensor.example_current_face
state: sleepy
```

The clock format values `12h` and `24h` are unchanged. Existing `FACE_*` constants for the alarm actions remain supported. Account credentials, device selection and custom entity names are preserved by an ordinary update.

### Earlier entity and behavior changes

#### Brightness moved to a number entity

Earlier versions exposed brightness as a dimmable light. Still older versions used a `Screen Brightness` number and a sensor incorrectly labeled in lux. The obsolete light and earlier `_luminosity` number/sensor entries are removed from this integration's entity registry during setup.

Replace old automation targets with the current brightness number shown on your REMI's device page. Existing automation references are not rewritten.

Before:

```yaml
action: light.turn_on
target:
  entity_id: light.example_brightness
data:
  brightness_pct: 40
```

Now:

```yaml
action: number.set_value
target:
  entity_id: number.example_brightness
data:
  value: 40
```

The old `brightness_pct` corresponds directly to the new 0–100 value. The old light's `brightness` attribute used 0–255 and must not be copied directly into a number value or state condition.

Setting the number to `0` turns off the upper light and leaves the setting at zero. The former light entity's memory of the last nonzero brightness is no longer used. The integration does not provide an ambient illuminance sensor. Historical brightness or lux data is not converted.

#### RGB entities

**App background color** remains an RGB light entity with its original unique ID. Its commands change the color associated with REMI in the official app. It does not control a physical RGB light.

The old **Night Light** RGB entity was removed. Commands to `lightnight` produced no observable physical effect on the two devices tested, running firmware 329 and 332. These observations do not establish support on other devices.

The obsolete entity is removed from this integration's entity registry. Remove its references from dashboards, scripts and automations. The integration no longer writes `lightnight` and does not delete or reset values already stored on UrbanHello's servers.

#### Temperature history

The corrected formula may change the reported temperature. Old history remains as recorded; it is not recalculated. See [Temperature](#temperature).

#### Music modes

Versions predating the correction labeled music modes `Off`, `Music` and `White Noise`. Those labels did not match the app's playback behavior. Use the four current modes listed above; update old option selections and comparisons. The selector's unique ID is retained.

#### Alarm times and weekdays

Alarm times now update the `event_time` data used by the official app. Replace date-time/ISO input with `HH:MM` or `HH:MM:00` and remove nonzero seconds.

Alarm attributes display the corrected weekdays. The service convention `repeat` with Sunday = 0 is preserved; it is converted to the cloud's Monday-first representation.

### Existing installations and repository changes

The Mins95 fork and the original integration share the domain `urbanhello_remi_unofficial` and retain the original entity unique IDs where the entity remains supported. Updating the installed code while keeping the configured integration preserves those identities.

Changing a Marketplace repository is a separate operation from updating its release. Marketplace does not allow two installed repositories to provide the same domain. Its **Delete and uninstall** action removes configured integration entries, devices and entities; it is not a lossless source-switch command. Do not delete the configured integration merely to update this fork.

Before changing repository ownership, preserve a Home Assistant backup and verify the source-change procedure supported by your package manager. This guide does not provide an automatic Marketplace source migration.

## Connection behavior and validation

Device state is polled every 60 seconds. Cloud reads use a 15-second timeout per request and up to three attempts for connection failures or HTTP 500, 502, 503 and 504 responses. History metadata has its own 20-minute coordinator and does not block initial device setup. Chart files have bounded size, timeouts and caching.

An explicitly offline or inactive REMI makes live temperature, signal, face and music controls unavailable. Stored device information and historical reports are not presented as new measurements. A failed alarm-list refresh retains existing entities until a successful snapshot can reconcile additions or removals.

Commands, including alarm creation and deletion, are not automatically retried after these failures because the server may already have applied them. Check the resulting state before repeating an action manually. Reauthentication retains the selected REMI, and alarm action handlers resolve the currently loaded integration after a reload.

Earlier installation checks on Home Assistant 2026.11.0 with firmware 332 confirmed corrected live temperature, device-specific firmware status, weekday display and alarm time entities while retaining existing IDs and schedules. Those checks do not establish physical validation of the beta's new music controls, timer behavior or night face brightness.

Automated tests cover cloud responses, validation, command payloads and Home Assistant actions. Consult the [current workflow results](https://github.com/Mins95/ha-remi/actions/workflows/tests.yml) and [changelog](../CHANGELOG.md) for release-specific results.

[Back to the README](../README.md)
