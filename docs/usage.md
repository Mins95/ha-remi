# REMI usage and upgrade guide

[Back to the README](../README.md) · [Changelog](../CHANGELOG.md)

This guide covers the public Mins95 integration, its Home Assistant actions and changes from earlier versions. It requires an UrbanHello account and internet access. Example entity IDs and alarm IDs are placeholders: use the IDs from your own installation.

## Everyday controls

Open **Settings → Devices & services → Remi**, then select your device. Its entities can also be added to a dashboard or used in automations.

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

### Temperature

The Celsius conversion is `(raw - 50) / 5`. For example, raw `160` means **22.0 °C**. Decimal values are retained, with a suggested display precision of one decimal place. The official app displays an integer.

The raw measurement and conversion formula are available in the sensor's attributes. Missing or invalid readings remain unknown. Decimal display preserves the reported value; it does not prove that the physical sensor is accurate to a tenth of a degree.

Historical temperatures are not rewritten. A step in a graph after updating may reflect the corrected conversion rather than a change in room temperature. The [protocol observations](protocol-3.4.23.json) record the relevant interoperability facts.

### Firmware status

The **Firmware update available** entity uses the device's `firmware_need_update` indication or its assigned `update_firmware_version`. A server-wide default version is informational and does not establish that an update is available for this particular REMI.

Attributes expose the installed version, assigned target and server default when available. If device-specific information is missing, the update state stays unknown. Firmware metadata is cached for an hour; **Check firmware** refreshes it and the device state.

**Check firmware never installs firmware.** Use the official app and [UrbanHello's update instructions](https://www.urbanhello.com/fr/faq/faqs/comment-mettre-a-jour-remi-manuellement-) for firmware installation.

## Alarm actions

Each discovered schedule provides a switch and a time entity. New or deleted cloud schedules are reflected after refresh. Use the switch to enable or disable a schedule and the time entity to change its hours and minutes.

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

Creation requires **exactly one loaded REMI** because this action has no device selector. With multiple loaded devices it raises an explicit error instead of choosing one.

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

The form displays translated face labels and uses the following codes. Existing `FACE_*` constants remain accepted for compatibility:

| Code | Existing constant | Meaning |
| --- | --- | --- |
| `off` | `FACE_OFF` | Off |
| `awake` | `FACE_DAY` | Awake |
| `sleepy` | `FACE_NIGHT` | Sleepy |
| `semi_awake` | `FACE_SEMI_AWAKE` | Semi-awake |
| `smiley` | `FACE_SMILY` | Smiley |

Only alarm actions accept the old `FACE_*` constants. The clock face select entity uses the lowercase codes.

### Update an alarm

Action: `urbanhello_remi_unofficial.update_alarm`.

Only `event_id` is required. All create-action fields are optional: supply only those you want to change. The integration resolves the owning loaded REMI from the alarm's ID.

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

## Upgrading

<a id="upgrading-from-030"></a>

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

Device state is polled every 60 seconds. Cloud reads use a 15-second timeout per request and up to three attempts for connection failures or HTTP 500, 502, 503 and 504 responses.

Commands, including alarm creation and deletion, are not automatically retried after these failures because the server may already have applied them. Check the resulting state before repeating an action manually. Reauthentication retains the selected REMI, and alarm action handlers resolve the currently loaded integration after a reload.

The recorded installation check on Home Assistant 2026.11.0 with firmware 332 confirmed the corrected temperature, device-specific firmware status, weekday display and alarm time entities. Existing entity IDs, schedules and enabled states were retained. It did not alter physical alarm schedules or validate music playback or the new night face brightness effect.

Automated tests cover cloud responses, validation, command payloads and Home Assistant actions. Consult the [current workflow results](https://github.com/Mins95/ha-remi/actions/workflows/tests.yml) and [changelog](../CHANGELOG.md) for release-specific results.

[Back to the README](../README.md)
