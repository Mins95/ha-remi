import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

// Small DOM double: variable HTML parsing is deliberately forbidden, so an
// unsafe text insertion fails instead of becoming a permissive mock operation.
class Style {
  constructor() { this.properties = new Map(); }
  setProperty(name, value) { this.properties.set(name, String(value)); }
  getPropertyValue(name) { return this.properties.get(name) ?? ""; }
}
class Node {
  constructor(tag = "div") { this.tagName = tag; this.children = []; this.listeners = new Map(); this.dataset = {}; this.attributes = {}; this.style = new Style(); this.type = ""; this.value = ""; this.checked = false; this.disabled = false; this.open = false; this.className = ""; this.isConnected = false; this._text = ""; }
  set innerHTML(_) { throw new Error("HTML parsing is forbidden"); }
  get value() { return this._value ?? ""; }
  set value(value) { this._value = String(value); }
  get childNodes() { return this.children; }
  get textContent() { return this._text + this.children.map(node => node.textContent).join(""); }
  set textContent(text) { this._text = String(text); this.children = []; }
  append(...nodes) { for (let node of nodes) { if (typeof node === "string") node = Object.assign(new Node("#text"), { textContent: node }); if (node.tagName === "#fragment") { this.append(...node.children); continue; } if (node.parentNode) node.remove(); node.parentNode = this; this.children.push(node); } }
  insertBefore(node, reference) { if (reference == null) return this.append(node); if (node === reference) return node; if (!this.children.includes(reference)) throw new Error("Reference is not a child"); if (node.tagName === "#fragment") { for (const child of [...node.children]) this.insertBefore(child, reference); return node; } if (node.parentNode) node.remove(); this.children.splice(this.children.indexOf(reference), 0, node); node.parentNode = this; return node; }
  replaceChildren(...nodes) { for (const child of this.children) child.parentNode = null; this.children = []; this._text = ""; this.append(...nodes); }
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter(node => node !== this); this.parentNode = null; }
  setAttribute(key, value) { this.attributes[key] = String(value); if (key === "class") this.className = String(value); }
  getAttribute(key) { return this.attributes[key]; }
  addEventListener(name, listener) { const listeners = this.listeners.get(name) || []; listeners.push(listener); this.listeners.set(name, listeners); }
  dispatchEvent(event) { event.target ??= this; for (const listener of this.listeners.get(event.type) || []) listener(event); return true; }
  matches(selector) { return selector.split(",").some(part => part.startsWith(".") ? this.className.split(" ").includes(part.slice(1)) : this.tagName === part); }
  querySelectorAll(selector) { const results = []; for (const child of this.children) { if (child.matches(selector)) results.push(child); results.push(...child.querySelectorAll(selector)); } return results; }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  attachShadow() { return this.shadowRoot = new Node("#shadow"); }
  reportValidity() { return true; }
}
const definitions = new Map();
globalThis.HTMLElement = Node;
globalThis.customElements = { get: name => definitions.get(name), define: (name, value) => definitions.set(name, value) };
globalThis.CustomEvent = class { constructor(type, options) { this.type = type; Object.assign(this, options); } };
globalThis.document = {
  createElement: tag => definitions.has(tag) ? new (definitions.get(tag))() : new Node(tag),
  createElementNS: (_, tag) => new Node(tag),
  createTextNode: text => Object.assign(new Node("#text"), { textContent: text }),
  createDocumentFragment: () => new Node("#fragment")
};
const source = await readFile(new URL("../custom_components/urbanhello_remi_unofficial/www/remi-card.js", import.meta.url), "utf8");
const cardModule = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const { DOMAIN, UrbanhelloRemiCard, UrbanhelloRemiCardEditor, discoverRemiDevices, indexEntities, makeAlarmPayload, makeNapPayload, serviceRequest } = cardModule;
const device = { id: "device-1", remiId: "REMI1", name: "Bedroom" };
const registryDevice = { id: device.id, identifiers: [[DOMAIN, device.remiId]], name: device.name };
const registryEntity = (domain, key, entityId = `${domain}.renamed_by_user`) => ({ device_id: device.id, platform: DOMAIN, unique_id: `${device.remiId}_${key}`, entity_id: entityId });
const flush = () => new Promise(resolve => setImmediate(resolve));

function setup(entries = [], states = {}) {
  const calls = [], subscriptions = new Map();
  const hass = { language: "fr", states, callWS: async request => { calls.push(request); if (request.type === "config/device_registry/list") return [registryDevice]; if (request.type === "config/entity_registry/list") return entries; return { response: { profiles: [] } }; }, connection: { subscribeEvents: async (fn, name) => { subscriptions.set(name, fn); return () => subscriptions.delete(name); } } };
  const card = new UrbanhelloRemiCard(); card._hass = hass; card._devices = [device]; card._entities = entries; card._registryReady = true; card.isConnected = true; card.hass = hass; card._render();
  return { card, hass, calls, subscriptions };
}

test("discovery uses integration identifiers and registry unique IDs, never entity slugs", () => {
  assert.deepEqual(discoverRemiDevices([registryDevice, { id: "unrelated", identifiers: [["other", "REMI1"]] }]), [device]);
  const correct = registryEntity("number", "brightness", "number.my_lamp");
  const index = indexEntities([correct, { ...correct, entity_id: "number.wrong_device", device_id: "device-2" }, { ...correct, entity_id: "number.wrong_platform", platform: "other" }, { ...correct, entity_id: "number.disabled", disabled_by: "user" }], device);
  assert.deepEqual([...index], [["number:brightness", "number.my_lamp"]]);
});

test("multiple REMI require explicit selection and missing states are never guessed", () => {
  const { card } = setup(); card._devices.push({ id: "device-2", remiId: "REMI2", name: "Other" });
  assert.equal(card._device(), undefined);
  card.setConfig({ device_id: "device-2" }); assert.equal(card._device().remiId, "REMI2");
  assert.equal(card._textState("sensor", "temperature"), "—");
});

test("Monday-first editor sends Sunday=0, preserves Friday/Saturday and rejects invalid days", () => {
  assert.deepEqual(makeAlarmPayload({ repeat: [1, 2, 3, 4, 7] }, "REMI1").repeat, [0, 1, 2, 3, 4]);
  assert.deepEqual(makeAlarmPayload({ repeat: [5, 6] }, "REMI1").repeat, [5, 6]);
  assert.deepEqual(makeAlarmPayload({ repeat: [6, 7] }, "REMI1").repeat, [0, 6]);
  assert.throws(() => makeAlarmPayload({ repeat: [8] }, "REMI1"));
});

test("payload validation keeps native bounds and does not forward unknown fields", () => {
  assert.deepEqual(makeNapPayload({ name: "Nap", duration_minutes: 30, face: "sleepy", secret: "hidden" }, "REMI1", "nap1"), { remi_id: "REMI1", nap_id: "nap1", name: "Nap", duration_minutes: 30, face: "sleepy" });
  assert.throws(() => makeNapPayload({ duration_minutes: 1440 }, "REMI1"));
  assert.throws(() => makeAlarmPayload({ brightness: 21.7 }, "REMI1"));
  assert.throws(() => makeAlarmPayload({ time: "24:00" }, "REMI1"));
});

test("service responses are explicitly requested only for read actions", () => {
  assert.deepEqual(serviceRequest(DOMAIN, "list_naps", { remi_id: "REMI1" }, undefined, true), { type: "call_service", domain: DOMAIN, service: "list_naps", service_data: { remi_id: "REMI1" }, return_response: true });
  assert.deepEqual(serviceRequest("number", "set_value", { value: 8 }, "number.mine"), { type: "call_service", domain: "number", service: "set_value", service_data: { value: 8 }, target: { entity_id: "number.mine" } });
});

test("untrusted device and alarm names stay literal DOM text", () => {
  const entry = registryEntity("switch", "alarm_ABC");
  const malicious = '<img src=x onerror="globalThis.pwned=true">';
  const { card, calls } = setup([entry], { [entry.entity_id]: { state: "on", attributes: { alarm_name: malicious, time: "07:30", recurrence: ["mon"] } } });
  card._tab = "alarms"; card._render();
  assert.ok(card.shadowRoot.textContent.includes(malicious));
  assert.equal(card.shadowRoot.querySelectorAll("img").length, 0);
  assert.equal(calls.length, 0);
  assert.equal(globalThis.pwned, undefined);
});

test("real alarm form dispatches Monday and Sunday with its frozen REMI target", async () => {
  const { card, calls } = setup(); card._openForm("alarm");
  card._form.inputs.get("name").value = "Wake";
  card._form.inputs.get("time").value = "09:00";
  card._form.inputs.get("day_0").checked = true;
  card._form.inputs.get("day_6").checked = true;
  card._form.element.dispatchEvent({ type: "submit", preventDefault() {} });
  await flush();
  const request = calls.find(call => call.service === "create_alarm");
  assert.equal(request.service_data.remi_id, "REMI1");
  assert.equal(request.service_data.time, "09:00");
  assert.deepEqual(request.service_data.repeat, [0, 1]);
});

test("update sends only edited fields, never invents missing cloud settings", async () => {
  const { card, calls } = setup(); card._openForm("alarm", { event_id: "existing", alarm_name: "Morning", time: "07:30" });
  const input = card._form.inputs.get("time"); input.value = "08:15"; input.dispatchEvent({ type: "change" });
  card._form.element.dispatchEvent({ type: "submit", preventDefault() {} }); await flush();
  assert.deepEqual(calls[0].service_data, { remi_id: "REMI1", event_id: "existing", time: "08:15" });
});

test("failed writes show errors without optimistic success or retries", async () => {
  const { card, hass, calls } = setup(); hass.callWS = async request => { calls.push(request); throw new Error("Cloud unavailable"); };
  card._openForm("nap"); card._form.inputs.get("name").value = "Afternoon";
  card._form.element.dispatchEvent({ type: "submit", preventDefault() {} }); await flush();
  assert.equal(calls.length, 1); assert.ok(card._form); assert.equal(card._message.error, true); assert.match(card._message.text, /Cloud unavailable/);
});

test("switching configured devices clears every cached form, library and report", () => {
  const { card, calls } = setup(); card._openForm("alarm"); const old = card._form;
  card._library = { tracks: ["private"] }; card._naps = [{ name: "old" }]; card._history = { logs: ["old"] };
  card.setConfig({ device_id: "other" });
  assert.equal(card._form, null); assert.equal(card._library, null); assert.equal(card._naps, null); assert.equal(card._history, null);
  old.element.dispatchEvent({ type: "submit", preventDefault() {} }); assert.equal(calls.length, 0);
});

test("registry changes invalidate automatic target and unsubscribe on disconnect", async () => {
  const { card, hass, subscriptions } = setup(); await card._loadRegistry();
  assert.equal(subscriptions.size, 2); card._library = { tracks: ["old"] }; card._openForm("alarm");
  hass.callWS = async request => request.type === "config/device_registry/list" ? [registryDevice, { id: "new", identifiers: [[DOMAIN, "REMI2"]] }] : [];
  await card._loadRegistry(); assert.equal(card._device(), undefined); assert.equal(card._form, null); assert.equal(card._library, null);
  card.disconnectedCallback(); assert.equal(subscriptions.size, 0);
});

test("unrelated HA states do not rebuild the card; relevant updates preserve expanded settings", () => {
  const entry = registryEntity("number", "brightness");
  const { card, hass } = setup([entry], { [entry.entity_id]: { state: "42", attributes: {} } });
  const root = card.shadowRoot.children[1], details = card.shadowRoot.querySelector("details"); details.open = true;
  card.hass = { ...hass, states: { ...hass.states, "sensor.unrelated": { state: "3", attributes: {} } } };
  assert.equal(card.shadowRoot.children[1], root);
  card.hass = { ...hass, states: { ...hass.states, [entry.entity_id]: { state: "43", attributes: {} } } };
  assert.notEqual(card.shadowRoot.children[1], root); assert.equal(card.shadowRoot.querySelector("details").open, true);
});

const rangeInput = (card, key) => card.shadowRoot.querySelectorAll("input").find(input => input.type === "range" && input.getAttribute("aria-label") === card.t(key));
const rangeProgress = input => input.style.getPropertyValue("--remi-range-progress");

test("range fills follow each entity's scale at both ends and midway without issuing commands", () => {
  const nightlight = registryEntity("number", "brightness", "number.test_nightlight");
  const noise = registryEntity("number", "noise_threshold", "number.test_noise");
  const { card, calls } = setup([nightlight, noise]);
  for (const [nightlightValue, noiseValue, expected] of [[0, 0, "0%"], [50, 125, "50%"], [100, 250, "100%"]]) {
    card.hass = { ...card.hass, states: {
      [nightlight.entity_id]: { state: String(nightlightValue), attributes: {} },
      [noise.entity_id]: { state: String(noiseValue), attributes: {} },
    } };
    assert.equal(rangeProgress(rangeInput(card, "brightness")), expected);
    assert.equal(rangeProgress(rangeInput(card, "noise_threshold")), expected);
  }
  card.hass = { ...card.hass, states: { [nightlight.entity_id]: { state: "unavailable", attributes: {} } } };
  const unavailable = rangeInput(card, "brightness");
  assert.equal(unavailable.disabled, true);
  assert.equal(unavailable.parentNode.querySelector(".value").textContent, "—");
  assert.equal(rangeProgress(unavailable), "0%");
  assert.deepEqual(calls, []);
});

test("dragging a generic range updates its fill but only release sends the existing command, and reported state restores the fill", async () => {
  const entry = registryEntity("number", "brightness", "number.test_nightlight");
  const { card, calls } = setup([entry], { [entry.entity_id]: { state: "30", attributes: {} } });
  const input = rangeInput(card, "brightness");
  for (const value of [45, 60]) {
    input.value = String(value); input.dispatchEvent({ type: "input" });
    assert.equal(rangeProgress(input), `${value}%`);
    assert.equal(input.parentNode.querySelector(".value").textContent, `${value}%`);
  }
  assert.deepEqual(calls, []);
  assert.equal(card.hass.states[entry.entity_id].state, "30");
  input.dispatchEvent({ type: "change" }); await flush();
  assert.deepEqual(calls, [{ type: "call_service", domain: "number", service: "set_value", service_data: { value: 60 }, target: { entity_id: entry.entity_id } }]);
  assert.equal(rangeProgress(rangeInput(card, "brightness")), "30%", "an acknowledged command is not an observed value");
  card.hass = { ...card.hass, states: { [entry.entity_id]: { state: "42", attributes: {} } } };
  assert.equal(rangeProgress(rangeInput(card, "brightness")), "42%");
});

test("card uses truthful physical controls and app-background labels", () => {
  const { card } = setup(); assert.ok(card.shadowRoot.textContent.includes("Couleur de fond de l’application"));
  card._tab = "naps"; card._render(); assert.ok(card.shadowRoot.textContent.includes("bouton physique"));
  assert.equal(globalThis.customCards.filter(item => item.type === "urbanhello-remi-card").length, 1);
});

test("alarm rows sort by clock time and use current cloud names beside actual switches", () => {
  const entries = [registryEntity("switch", "alarm_late", "switch.late"), registryEntity("switch", "alarm_early", "switch.early")];
  const { card } = setup(entries, { "switch.late": { state: "off", attributes: { alarm_name: "Night", time: "21:30" } }, "switch.early": { state: "on", attributes: { alarm_name: "Morning", time: "07:30" } } });
  card._tab = "alarms"; card._render();
  assert.deepEqual(card.shadowRoot.querySelectorAll(".clock").map(node => node.textContent), ["07:30", "21:30"]);
  assert.deepEqual(card.shadowRoot.querySelectorAll(".toggle").map(node => node.checked), [true, false]);
});

test("compact alarm rows preserve real switch targets and edit the current cloud alarm after its ID rotates", async () => {
  const early = registryEntity("switch", "alarm_early", "switch.renamed_morning"), late = registryEntity("switch", "alarm_late", "switch.renamed_evening");
  const { card, calls } = setup([late, early], {
    [early.entity_id]: { state: "on", attributes: { event_id: "early_cloud", alarm_name: "Morning", time: "07:30", recurrence: ["mon", "sun"] } },
    [late.entity_id]: { state: "off", attributes: { event_id: "late_cloud", alarm_name: "Evening", time: "21:30", recurrence: ["fri", "sat"] } }
  });
  card.setConfig({ layout: "compact" }); card._switchTab("alarms");
  assert.deepEqual(card.shadowRoot.querySelectorAll(".clock").map(node => node.textContent), ["07:30", "21:30"]);
  const toggle = card.shadowRoot.querySelectorAll(".schedule")[0].querySelector(".toggle");
  assert.ok(toggle.getAttribute("aria-label").includes("Morning"));
  toggle.checked = false; toggle.dispatchEvent({ type: "change" }); await flush();
  assert.deepEqual(calls[0], { type: "call_service", domain: "switch", service: "turn_off", service_data: {}, target: { entity_id: early.entity_id } });
  assert.equal(card._state("switch", "alarm_early").state, "on", "the row waits for the reported switch state");
  const edit = card.shadowRoot.querySelectorAll(".schedule")[1].querySelector(".schedule-edit");
  assert.equal(edit.getAttribute("aria-label"), `${card.t("edit")} Evening`); edit.dispatchEvent({ type: "click" });
  const draft = card._form; assert.equal(draft.alarmEntityId, late.entity_id);
  assert.equal(draft.inputs.get("day_4").checked, true); assert.equal(draft.inputs.get("day_5").checked, true); assert.equal(draft.inputs.get("day_6").checked, false);
  draft.inputs.get("time").value = "22:15"; draft.inputs.get("time").dispatchEvent({ type: "change" });
  card.hass = { ...card.hass, states: { ...card.hass.states, [late.entity_id]: { state: "off", attributes: { event_id: "rotated_late", alarm_name: "Evening", time: "21:30", recurrence: ["fri", "sat"] } } } };
  draft.element.dispatchEvent({ type: "submit", preventDefault() {} }); await flush();
  assert.deepEqual(calls[1].service_data, { remi_id: "REMI1", event_id: "rotated_late", time: "22:15" });
  assert.equal(calls[1].service, "update_alarm"); assert.equal(calls.length, 2);
});

test("detached compact alarm controls cannot target an alarm after switching REMI", async () => {
  const alarm = registryEntity("switch", "alarm_current", "switch.original_remi_alarm");
  const second = { id: "device-2", remiId: "REMI2", name: "Other bedroom" };
  const secondAlarm = { ...registryEntity("switch", "alarm_other", "switch.second_remi_alarm"), device_id: second.id, unique_id: "REMI2_alarm_other" };
  const { card, calls } = setup([alarm, secondAlarm], {
    [alarm.entity_id]: { state: "on", attributes: { event_id: "first", time: "07:00", alarm_name: "First", recurrence: ["sun"] } },
    [secondAlarm.entity_id]: { state: "off", attributes: { event_id: "second", time: "08:00", alarm_name: "Second", recurrence: [] } }
  });
  card._devices.push(second); card.setConfig({ device_id: device.id, layout: "compact" }); card._switchTab("alarms");
  const oldRow = card.shadowRoot.querySelector(".schedule");
  card.setConfig({ device_id: second.id, layout: "compact" });
  oldRow.querySelector(".toggle").dispatchEvent({ type: "change" }); oldRow.querySelector(".schedule-edit").dispatchEvent({ type: "click" }); await flush();
  assert.equal(calls.length, 0); assert.equal(card._form, null);
  assert.equal(card.shadowRoot.querySelectorAll(".schedule").length, 1);
  assert.ok(card.shadowRoot.querySelector(".schedule").textContent.includes("Second"));
});

for (const locale of ["fr", "en"]) {
  test(`${locale} compact recurrence distinguishes Sunday, discontinuous days, once and unknown without inactive chips`, () => {
    const cases = [
      [["sun"], "Dim", "Sun"], [["sun", "mon"], "Lun, Dim", "Mon, Sun"],
      [["fri", "sat"], "Ven–Sam", "Fri–Sat"], [["mon", "tue", "wed", "thu", "fri"], "Lun–Ven", "Mon–Fri"],
      [["mon", "tue", "wed", "thu", "fri", "sat", "sun"], "Tous les jours", "Every day"],
      [[], "Une seule fois", "Once"], [undefined, "Non communiqué", "Not reported"], [null, "Non communiqué", "Not reported"],
      ["mon", "Non communiqué", "Not reported"], [["mon", "future_day"], "Non communiqué", "Not reported"]
    ];
    const entries = cases.map((_, index) => registryEntity("switch", `alarm_days${index}`, `switch.example_days_${index}`));
    const states = Object.fromEntries(entries.map((entry, index) => [entry.entity_id, { state: "on", attributes: { alarm_name: `Schedule ${index}`, time: `07:${String(index).padStart(2, "0")}`, ...(cases[index][0] === undefined ? {} : { recurrence: cases[index][0] }) } }]));
    const { card, hass, calls } = setup(entries, states); card.hass = { ...hass, language: locale }; card.setConfig({ layout: "compact" }); card._switchTab("alarms");
    assert.deepEqual(card.shadowRoot.querySelectorAll(".schedule-recurrence").map(node => node.textContent), cases.map(item => item[locale === "fr" ? 1 : 2]));
    assert.equal(card.shadowRoot.querySelectorAll(".day").length, 0);
    assert.equal(card.shadowRoot.querySelectorAll(".toggle").length, cases.length);
    assert.equal(card.shadowRoot.querySelectorAll(".schedule-edit").length, cases.length);
    assert.equal(calls.length, 0);
  });
}

test("normal alarm rows retain their seven Monday-first day chips and literal names after using compact layout", () => {
  const entry = registryEntity("switch", "alarm_named", "switch.example_named"), name = '<img onerror="fail">';
  const { card, calls } = setup([entry], { [entry.entity_id]: { state: "on", attributes: { alarm_name: name, time: "09:00", recurrence: ["sun", "mon"] } } });
  card.setConfig({ layout: "compact" }); card._switchTab("alarms");
  assert.equal(card.shadowRoot.querySelector(".schedule-name").textContent, name);
  assert.equal(card.shadowRoot.querySelector(".schedule-edit").getAttribute("aria-label"), `${card.t("edit")} ${name}`);
  assert.equal(card.shadowRoot.querySelectorAll("img").length, 0);
  card.setConfig({ layout: "full" });
  const days = card.shadowRoot.querySelectorAll(".day");
  assert.deepEqual(days.map(node => node.textContent), ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]);
  assert.deepEqual(days.map(node => node.className.split(" ").includes("active")), [true, false, false, false, false, false, true]);
  assert.equal(card.shadowRoot.querySelector(".schedule-recurrence"), undefined);
  assert.equal(card.shadowRoot.querySelector(".schedule").querySelector("button").textContent, card.t("edit"));
  assert.equal(calls.length, 0);
});

test("deleting requires the explicit confirmation and sends only the frozen object ID", async () => {
  const { card, calls } = setup(); card._openForm("nap", { nap_id: "nap1", name: "Nap", duration_minutes: 30 });
  const context = card._form; card._confirmDelete(context, context.element);
  assert.equal(calls.length, 0);
  context.element.querySelector(".confirm").querySelector(".danger").dispatchEvent({ type: "click" }); await flush();
  const deletion = calls.find(call => call.service === "delete_nap");
  assert.deepEqual(deletion.service_data, { remi_id: "REMI1", nap_id: "nap1" });
  assert.equal(calls.filter(call => call.service === "delete_nap").length, 1);
});

test("a late music-library response cannot repopulate another REMI", async () => {
  const entry = registryEntity("media_player", "music_player"), { card, hass } = setup([entry]);
  let resolve; hass.callWS = () => new Promise(done => { resolve = done; });
  card._browse(); card.setConfig({ device_id: "other" }); resolve({ children: [{ title: "Old REMI", can_play: true }] }); await flush();
  assert.equal(card._library, null); assert.equal(card._message, null);
});

test("display scales remain separate and current states are localized only for labels", () => {
  const entries = [registryEntity("number", "brightness", "number.display"), registryEntity("number", "face_brightness", "number.night")];
  const { card, hass } = setup(entries, { "number.display": { state: "42", attributes: {} }, "number.night": { state: "8", attributes: {} } });
  const ranges = card.shadowRoot.querySelectorAll("input").filter(node => node.type === "range");
  assert.equal(ranges[0].getAttribute("min"), "0"); assert.equal(ranges[0].getAttribute("max"), "100");
  assert.equal(ranges[1].getAttribute("min"), "0"); assert.equal(ranges[1].getAttribute("max"), "10");
  card.hass = { ...hass, language: "en" }; assert.match(card.shadowRoot.textContent, /Face brightness/);
  assert.equal(card._state("number", "face_brightness").state, "8");
});

const FACE_OPTIONS = ["off", "awake", "sleepy", "semi_awake", "smiley"];
const faceState = value => ({ state: value, attributes: { options: FACE_OPTIONS } });
function setupFace(value, brightness = "6") {
  const entry = registryEntity("select", "face", "select.bedroom_expression");
  const brightnessEntry = registryEntity("number", "face_brightness", "number.bedroom_face_brightness");
  const states = value === undefined ? {} : { [entry.entity_id]: faceState(value) };
  if (brightness !== undefined) states[brightnessEntry.entity_id] = { state: brightness, attributes: { min: 1, max: 10, step: 1 } };
  return { ...setup([entry, brightnessEntry], states), entry, brightnessEntry };
}
function reportFace(card, entry, value) {
  card.hass = { ...card.hass, states: { ...card.hass.states, [entry.entity_id]: faceState(value) } };
}
function faceLevelInput(card) {
  return card.shadowRoot.querySelectorAll("input").find(input => input.type === "range" && input.getAttribute("aria-label") === card.t("face_brightness"));
}
function changeFaceLevel(card, value, event = "change") {
  const input = faceLevelInput(card);
  input.value = String(value);
  input.dispatchEvent({ type: event });
}
function confirmBrightnessWrites(card) {
  const callWS = card.hass.callWS;
  card.hass.callWS = async request => {
    const result = await callWS(request);
    if (request.domain === "number" && request.service === "set_value") {
      const id = request.target.entity_id, previous = card.hass.states[id];
      card.hass = { ...card.hass, states: { ...card.hass.states, [id]: { ...previous, state: String(request.service_data.value) } } };
    }
    return result;
  };
}
function faceCommands(calls) {
  return calls.filter(call => call.type === "call_service" && call.domain === "select" && call.service === "select_option");
}
function disclosure(card, key) {
  return card.shadowRoot.querySelectorAll("details").find(node => node.dataset.key === key);
}

test("the zero-to-ten face slider switches off and restores the last observed expression without optimistic state", async () => {
  const { card, calls, entry, brightnessEntry } = setupFace("sleepy");
  assert.equal(card.shadowRoot.querySelector(".face-toggle"), undefined);
  assert.equal(faceLevelInput(card).getAttribute("min"), "0"); assert.equal(faceLevelInput(card).getAttribute("max"), "10");
  changeFaceLevel(card, 0);
  await flush();
  assert.deepEqual(faceCommands(calls)[0].service_data, { option: "off" });
  assert.deepEqual(faceCommands(calls)[0].target, { entity_id: entry.entity_id });
  assert.equal(calls.length, 1, "zero turns off the face without sending an invalid native brightness of zero");
  assert.equal(faceLevelInput(card).value, "6", "a command ACK is not an observed face");
  reportFace(card, entry, "off");
  assert.equal(faceLevelInput(card).value, "0");
  confirmBrightnessWrites(card);
  changeFaceLevel(card, 7);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["off", "sleepy"]);
  assert.deepEqual(calls.slice(1), [
    { type: "call_service", domain: "number", service: "set_value", service_data: { value: 7 }, target: { entity_id: brightnessEntry.entity_id } },
    { type: "call_service", domain: "select", service: "select_option", service_data: { option: "sleepy" }, target: { entity_id: entry.entity_id } }
  ]);
  assert.equal(faceLevelInput(card).value, "0", "restoration waits for reported state too");
  reportFace(card, entry, "sleepy");
  assert.equal(faceLevelInput(card).value, "7");
});

test("failed expression commands are never remembered as a confirmed expression", async () => {
  const { card, hass, calls, entry } = setupFace("sleepy");
  hass.callWS = async request => { calls.push(request); throw new Error("Write rejected"); };
  card.shadowRoot.querySelector(".faces").querySelectorAll("button")[0].dispatchEvent({ type: "click" });
  await flush();
  assert.equal(faceCommands(calls).length, 1, "failed writes are not retried");
  assert.equal(card._message.error, true);
  assert.equal(card._state("select", "face").state, "sleepy");
  reportFace(card, entry, "off");
  card.hass.callWS = async request => { calls.push(request); return {}; };
  confirmBrightnessWrites(card);
  changeFaceLevel(card, 7);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["awake", "sleepy"]);
});

test("starting with an off face uses awake only after an explicit turn-on action", async () => {
  const { card, calls } = setupFace("off");
  assert.equal(faceCommands(calls).length, 0);
  assert.equal(faceLevelInput(card).value, "0");
  confirmBrightnessWrites(card);
  changeFaceLevel(card, 7);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["awake"]);
  assert.equal(card._state("select", "face").state, "off");
});

test("last observed expression and command target remain isolated between two REMI", async () => {
  const { card, calls, entry } = setupFace("sleepy");
  const secondDevice = { id: "device-2", remiId: "REMI2", name: "Other bedroom" };
  const secondEntry = { ...registryEntity("select", "face", "select.second_expression"), device_id: secondDevice.id, unique_id: "REMI2_face" };
  const secondBrightness = { ...registryEntity("number", "face_brightness", "number.second_face_brightness"), device_id: secondDevice.id, unique_id: "REMI2_face_brightness" };
  card._devices.push(secondDevice);
  card._entities.push(secondEntry, secondBrightness);
  card.hass = { ...card.hass, states: { ...card.hass.states, [secondEntry.entity_id]: faceState("smiley"), [secondBrightness.entity_id]: { state: "8", attributes: {} } } };
  card.setConfig({ device_id: secondDevice.id });
  reportFace(card, secondEntry, "off");
  reportFace(card, entry, "off");
  confirmBrightnessWrites(card);
  changeFaceLevel(card, 7);
  await flush();
  card.setConfig({ device_id: device.id });
  changeFaceLevel(card, 7);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => [call.target.entity_id, call.service_data.option]), [
    [secondEntry.entity_id, "smiley"], [entry.entity_id, "sleepy"],
  ]);
});

for (const unknown of [undefined, "unknown", "unavailable", "future_face"]) {
  test(`unreported face ${String(unknown)} creates no expression or main-control command`, async () => {
    const { card, calls } = setupFace(unknown);
    const input = faceLevelInput(card);
    const buttons = card.shadowRoot.querySelector(".faces").querySelectorAll("button");
    assert.equal(input.disabled, true);
    assert.equal(input.getAttribute("aria-valuetext"), "—", "unknown is not presented as an observed off state");
    assert.equal(buttons.length, 2);
    assert.ok(buttons.every(button => button.disabled && button.getAttribute("aria-pressed") === "false"));
    assert.match(card.shadowRoot.textContent, /Non communiqué/);
    assert.equal(card.shadowRoot.querySelector(".face-art").querySelectorAll("path").length, 2, "unknown data must not draw awake or sleepy eyes");
    // Even stale/programmatic UI events cannot bypass the state guard.
    changeFaceLevel(card, 7);
    for (const button of buttons) button.dispatchEvent({ type: "click" });
    await flush();
    assert.equal(calls.length, 0);
    assert.equal(card._lastFaces.size, 0);
  });
}

for (const [lang, labels] of [
  ["fr", ["Réveillé", "Endormi"]],
  ["en", ["Awake", "Sleepy"]],
]) {
  test(`${lang}: two quick expressions and all five advanced options preserve stable state values`, () => {
    const { card } = setupFace("awake");
    card.hass = { ...card.hass, language: lang };
    const buttons = card.shadowRoot.querySelector(".faces").querySelectorAll("button");
    assert.deepEqual(buttons.map(button => button.textContent), labels);
    assert.deepEqual(buttons.map(button => button.getAttribute("aria-pressed")), ["true", "false"]);
    assert.equal(faceLevelInput(card).getAttribute("aria-label"), card.t("face_brightness"));
    assert.equal(card.shadowRoot.querySelector(".face-toggle"), undefined);
    const options = disclosure(card, "remi:advanced").querySelectorAll("select")[0].querySelectorAll("option");
    assert.deepEqual(options.map(option => option.value), FACE_OPTIONS);
    assert.equal(options[1].textContent, labels[0]);
    assert.equal(options[2].textContent, labels[1]);
    assert.equal(card._state("select", "face").state, "awake");
    assert.equal(disclosure(card, "remi:music").querySelector("summary").textContent, lang === "fr" ? "Musique" : "Music");
  });
}

for (const [expression, label] of [["semi_awake", "À moitié éveillé"], ["smiley", "Souriant"]]) {
  test(`${expression} stays visibly on without being misreported as awake or sleepy`, () => {
    const { card, calls } = setupFace(expression);
    assert.equal(faceLevelInput(card).value, "6");
    assert.ok(card.shadowRoot.querySelector(".faces").querySelectorAll("button").every(button => button.getAttribute("aria-pressed") === "false"));
    assert.equal(card.shadowRoot.querySelector(".current-face").textContent, label);
    assert.equal(faceCommands(calls).length, 0);
  });
}

test("semi-awake and sleepy have distinct eye drawings while off has no lit face", () => {
  const { card, entry } = setupFace("sleepy");
  const drawing = () => card.shadowRoot.querySelector(".face-art").querySelectorAll("path").map(node => node.getAttribute("d"));
  const sleepy = drawing();
  reportFace(card, entry, "semi_awake");
  const semiAwake = drawing();
  assert.equal(sleepy.length, 4);
  assert.equal(semiAwake.length, 4);
  assert.notEqual(sleepy[2], semiAwake[2]);
  reportFace(card, entry, "off");
  assert.equal(drawing().length, 2);
});

test("music starts collapsed and retains its own disclosure state across reports and tabs", () => {
  const { card, calls, entry } = setupFace("awake");
  assert.equal(disclosure(card, "remi:music").open, false);
  assert.equal(disclosure(card, "remi:advanced").open, false);
  disclosure(card, "remi:music").open = true;
  reportFace(card, entry, "sleepy");
  assert.equal(disclosure(card, "remi:music").open, true);
  assert.equal(disclosure(card, "remi:advanced").open, false, "music does not open unrelated settings");
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[1].dispatchEvent({ type: "click" });
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[0].dispatchEvent({ type: "click" });
  assert.equal(disclosure(card, "remi:music").open, true);
  disclosure(card, "remi:music").open = false;
  disclosure(card, "remi:advanced").open = true;
  reportFace(card, entry, "awake");
  assert.equal(disclosure(card, "remi:music").open, false);
  assert.equal(disclosure(card, "remi:advanced").open, true);
  assert.equal(calls.length, 0, "rendering, disclosing and changing tabs must not send commands or browse music");
});

test("a replacement HA connection clears the previous connection's face-restoration history", async () => {
  const { card, calls, entry } = setupFace("sleepy");
  reportFace(card, entry, "off");
  card.hass = { ...card.hass, connection: { ...card.hass.connection } };
  await flush();
  assert.equal(card._registryReady, true);
  confirmBrightnessWrites(card);
  changeFaceLevel(card, 7);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["awake"]);
});

test("quick expressions send only the corresponding select command", async () => {
  for (const [index, expected] of ["awake", "sleepy"].entries()) {
    const { card, calls, entry } = setupFace("off");
    card.shadowRoot.querySelector(".faces").querySelectorAll("button")[index].dispatchEvent({ type: "click" });
    await flush();
    assert.deepEqual(calls, [{ type: "call_service", domain: "select", service: "select_option", service_data: { option: expected }, target: { entity_id: entry.entity_id } }]);
  }
});

test("rapid face actions cannot send a second command while the first is pending", async () => {
  const { card, hass, calls } = setupFace("sleepy");
  let finish;
  hass.callWS = request => { calls.push(request); return new Promise(resolve => { finish = resolve; }); };
  changeFaceLevel(card, 0);
  assert.equal(card._busy, true);
  assert.ok(card.shadowRoot.querySelector(".faces").querySelectorAll("button").every(button => button.disabled));
  card.shadowRoot.querySelector(".faces").querySelectorAll("button")[0].dispatchEvent({ type: "click" });
  changeFaceLevel(card, 7);
  assert.equal(faceCommands(calls).length, 1);
  finish({});
  await flush();
  assert.equal(card._busy, false);
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["off"]);
});

test("dragging the face slider sends no intermediate command and an already lit face needs only a brightness write", async () => {
  const { card, calls, entry, brightnessEntry } = setupFace("sleepy");
  assert.equal(rangeProgress(faceLevelInput(card)), "60%");
  for (const value of [2, 4, 7]) {
    changeFaceLevel(card, value, "input");
    assert.equal(rangeProgress(faceLevelInput(card)), `${value * 10}%`);
    assert.equal(faceLevelInput(card).getAttribute("aria-valuetext"), `${value}/10`);
  }
  assert.equal(calls.length, 0); assert.equal(card.hass.states[brightnessEntry.entity_id].state, "6");
  changeFaceLevel(card, 7); await flush();
  assert.deepEqual(calls, [{ type: "call_service", domain: "number", service: "set_value", service_data: { value: 7 }, target: { entity_id: brightnessEntry.entity_id } }]);
  assert.equal(card.hass.states[entry.entity_id].state, "sleepy");
  assert.equal(faceLevelInput(card).value, "6", "an acknowledged write must not invent a new number state");
  assert.equal(rangeProgress(faceLevelInput(card)), "60%");
});

test("the face fill distinguishes confirmed off from unavailable while tracking the displayed zero-to-ten scale", () => {
  const { card, calls, entry, brightnessEntry } = setupFace("off", "10");
  assert.equal(rangeProgress(faceLevelInput(card)), "0%");
  assert.equal(faceLevelInput(card).getAttribute("aria-valuetext"), card.t("off"));
  assert.equal(faceLevelInput(card).disabled, false);
  reportFace(card, entry, "awake");
  assert.equal(rangeProgress(faceLevelInput(card)), "100%");
  card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "5", attributes: {} } } };
  assert.equal(rangeProgress(faceLevelInput(card)), "50%");
  reportFace(card, entry, "unknown");
  assert.equal(rangeProgress(faceLevelInput(card)), "0%");
  assert.equal(faceLevelInput(card).getAttribute("aria-valuetext"), "—");
  assert.equal(faceLevelInput(card).disabled, true);
  assert.deepEqual(calls, []);
});

for (const invalid of [undefined, "unknown", "unavailable", "NaN", "Infinity", "0", "11", "1.5"]) {
  test(`an unknown or invalid native face brightness ${String(invalid)} disables the composite slider without showing a fake off`, async () => {
    const { card, calls, brightnessEntry } = setupFace("sleepy", invalid);
    if (invalid === undefined) {
      const states = { ...card.hass.states }; delete states[brightnessEntry.entity_id]; card.hass = { ...card.hass, states };
    }
    assert.equal(faceLevelInput(card).disabled, true);
    assert.equal(faceLevelInput(card).getAttribute("aria-valuetext"), "—");
    changeFaceLevel(card, 7); changeFaceLevel(card, 0); await flush();
    assert.equal(calls.length, 0);
  });
}

test("a confirmed off face can display zero with missing brightness but cannot issue a composite command", async () => {
  const { card, calls } = setupFace("off", "unavailable");
  assert.equal(faceLevelInput(card).value, "0"); assert.equal(faceLevelInput(card).disabled, true);
  changeFaceLevel(card, 7); await flush(); assert.equal(calls.length, 0);
});

test("the composite slider rejects non-finite, fractional and out-of-range changes instead of truncating them", async () => {
  const { card, calls } = setupFace("off");
  for (const value of ["", "bad", -1, 11, 1.5, Infinity, NaN]) { changeFaceLevel(card, value); await flush(); }
  assert.equal(calls.length, 0);
});

test("turning an off face up waits for a confirmed brightness, serializes both writes and never updates the face optimistically", async () => {
  const { card, hass, calls, entry, brightnessEntry } = setupFace("off");
  let finishNumber, finishFace;
  hass.callWS = request => {
    calls.push(request);
    return new Promise(resolve => { if (request.domain === "number") finishNumber = resolve; else finishFace = resolve; });
  };
  changeFaceLevel(card, 7);
  assert.deepEqual(calls.map(call => call.domain), ["number"]); assert.equal(card._busy, true);
  assert.equal(faceLevelInput(card).disabled, true); assert.equal(faceLevelInput(card).value, "0");
  changeFaceLevel(card, 8); card.shadowRoot.querySelector(".faces").querySelector("button").dispatchEvent({ type: "click" });
  assert.equal(calls.length, 1);
  card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } };
  finishNumber({}); await flush();
  assert.deepEqual(calls.map(call => [call.domain, call.service_data]), [["number", { value: 7 }], ["select", { option: "awake" }]]);
  assert.equal(card._busy, true); assert.equal(card.hass.states[entry.entity_id].state, "off");
  changeFaceLevel(card, 9); assert.equal(calls.length, 2);
  finishFace({}); await flush();
  assert.equal(card._busy, false); assert.equal(faceLevelInput(card).value, "0");
  assert.equal(card.hass.states[entry.entity_id].state, "off");
});

test("a rejected brightness write cannot restore the face or retry either command", async () => {
  const { card, hass, calls } = setupFace("off");
  hass.callWS = async request => { calls.push(request); throw new Error("Brightness rejected"); };
  changeFaceLevel(card, 7); await flush();
  assert.deepEqual(calls.map(call => call.domain), ["number"]);
  assert.equal(card._message.error, true); assert.match(card._message.text, /Brightness rejected/);
  assert.equal(faceLevelInput(card).value, "0");
});

for (const reported of ["unavailable", "unknown", "11", "7.5"]) {
  test(`an acknowledged brightness write with observed value ${reported} cannot switch on the face`, async () => {
    const { card, hass, calls, brightnessEntry } = setupFace("off");
    hass.callWS = async request => {
      calls.push(request);
      card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: reported, attributes: {} } } };
      return {};
    };
    changeFaceLevel(card, 7); await flush();
    assert.deepEqual(calls.map(call => call.domain), ["number"]);
    assert.equal(card._state("select", "face").state, "off");
  });
}

test("a brightness acknowledgement waits for a later HA state confirmation before restoring the face", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { card, calls, brightnessEntry } = setupFace("off");
  changeFaceLevel(card, 7); await flush();
  assert.deepEqual(calls.map(call => call.domain), ["number"]);
  assert.equal(card._busy, true); assert.equal(faceLevelInput(card).value, "0");
  t.mock.timers.tick(4999); await flush();
  assert.deepEqual(calls.map(call => call.domain), ["number"]);
  queueMicrotask(() => { card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } }; });
  await flush();
  assert.deepEqual(calls.map(call => [call.domain, call.service_data]), [["number", { value: 7 }], ["select", { option: "awake" }]]);
  assert.equal(card._busy, false); assert.equal(faceLevelInput(card).value, "0");
  t.mock.timers.tick(10000); await flush(); assert.equal(calls.length, 2);
});

test("an unconfirmed brightness expires after five seconds and a later state does not replay restoration", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { card, calls, brightnessEntry } = setupFace("off");
  changeFaceLevel(card, 7); await flush();
  assert.deepEqual(calls.map(call => call.domain), ["number"]); assert.equal(card._busy, true);
  t.mock.timers.tick(5000); await flush();
  assert.deepEqual(calls.map(call => call.domain), ["number"]); assert.equal(card._busy, false);
  card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } };
  await flush(); assert.equal(calls.length, 1); assert.equal(card._state("select", "face").state, "off");
});

test("a face changed by the app while brightness is pending is never overwritten by restoration", async () => {
  const { card, hass, calls, entry, brightnessEntry } = setupFace("off"); let finish;
  hass.callWS = request => { calls.push(request); return new Promise(resolve => { finish = resolve; }); };
  changeFaceLevel(card, 7);
  card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} }, [entry.entity_id]: faceState("smiley") } };
  finish({}); await flush();
  assert.deepEqual(calls.map(call => call.domain), ["number"]);
  assert.equal(card._state("select", "face").state, "smiley");
});

for (const change of ["device", "connection", "config", "disconnect"]) {
  test(`${change} changes invalidate restoration after the first composite-slider write`, async () => {
    const { card, hass, calls, brightnessEntry } = setupFace("off"); let finish;
    const originalCall = hass.callWS;
    hass.callWS = request => {
      if (request.type !== "call_service") return originalCall(request);
      calls.push(request); return new Promise(resolve => { finish = resolve; });
    };
    changeFaceLevel(card, 7);
    card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } };
    if (change === "device") { card.setConfig({ device_id: "other" }); card.setConfig({ device_id: device.id }); }
    if (change === "connection") { card.hass = { ...card.hass, connection: { ...card.hass.connection } }; await flush(); }
    if (change === "config") { card.setConfig({ show_face_brightness: false }); card.setConfig({ show_face_brightness: true }); }
    if (change === "disconnect") { card.isConnected = false; card.disconnectedCallback(); }
    finish({}); await flush();
    assert.deepEqual(calls.filter(call => call.type === "call_service").map(call => call.domain), ["number"]);
  });
}

for (const eventName of ["ready", "disconnected"]) {
  test(`a ${eventName} event on the same HA connection cancels a pending brightness confirmation`, async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const { card, hass, calls, brightnessEntry } = setupFace("off");
    const listeners = new Map();
    const connection = { ...hass.connection,
      addEventListener: (name, listener) => { const set = listeners.get(name) || new Set(); set.add(listener); listeners.set(name, set); },
      removeEventListener: (name, listener) => listeners.get(name)?.delete(listener)
    };
    card.hass = { ...hass, connection }; await flush();
    changeFaceLevel(card, 7); await flush();
    assert.equal(card._busy, true); assert.ok(listeners.get(eventName)?.size, "the existing connection must be observed without replacing its object");
    for (const listener of listeners.get(eventName)) listener();
    await flush();
    assert.equal(card.hass.connection, connection);
    card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } };
    t.mock.timers.tick(5000); await flush();
    assert.deepEqual(calls.filter(call => call.type === "call_service").map(call => call.domain), ["number"]);
    assert.equal(card._busy, false);
    card.disconnectedCallback();
    assert.equal(listeners.get("ready")?.size || 0, 0); assert.equal(listeners.get("disconnected")?.size || 0, 0);
  });
}

for (const change of ["unavailable", "app_face", "hidden"]) {
  test(`${change} during the confirmation wait prevents restoration even if the value arrives later`, async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const { card, calls, entry, brightnessEntry } = setupFace("off");
    changeFaceLevel(card, 7); await flush(); assert.equal(card._busy, true);
    if (change === "unavailable") card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "unavailable", attributes: {} } } };
    if (change === "app_face") reportFace(card, entry, "smiley");
    if (change === "hidden") card.setConfig({ show_face_brightness: false });
    await flush(); assert.equal(card._busy, false);
    card.hass = { ...card.hass, states: { ...card.hass.states, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } };
    t.mock.timers.tick(5000); await flush();
    assert.deepEqual(calls.map(call => call.domain), ["number"]);
    assert.equal(card._state("select", "face").state, change === "app_face" ? "smiley" : "off");
  });
}

test("a registry rename during confirmation cancels the old target immediately without waiting for a state event", async t => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const { card, calls, brightnessEntry } = setupFace("off"), originalId = brightnessEntry.entity_id;
  changeFaceLevel(card, 7); await flush(); assert.equal(card._busy, true);
  brightnessEntry.entity_id = "number.renamed_face_brightness";
  card.hass.states[brightnessEntry.entity_id] = { state: "7", attributes: {} };
  await card._loadRegistry(); await flush();
  assert.equal(card._busy, false);
  t.mock.timers.tick(5000); await flush();
  assert.deepEqual(calls.filter(call => call.type === "call_service").map(call => [call.domain, call.target.entity_id]), [["number", originalId]]);
});

for (const key of ["online", "alive"]) {
  test(`a confirmed ${key}=off prevents restoration and disables the face slider`, async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const { card, calls, brightnessEntry } = setupFace("off");
    const status = registryEntity("binary_sensor", key, `binary_sensor.example_${key}`); card._entities.push(status);
    card.hass = { ...card.hass, states: { ...card.hass.states, [status.entity_id]: { state: "on", attributes: {} } } };
    changeFaceLevel(card, 7); await flush(); assert.equal(card._busy, true);
    card.hass = { ...card.hass, states: { ...card.hass.states, [status.entity_id]: { state: "off", attributes: {} }, [brightnessEntry.entity_id]: { state: "7", attributes: {} } } };
    await flush(); assert.equal(card._busy, false); assert.equal(faceLevelInput(card).disabled, true);
    changeFaceLevel(card, 8); t.mock.timers.tick(5000); await flush();
    assert.deepEqual(calls.map(call => call.domain), ["number"]);
  });
}

const historyReport = (report_id, period_end, extra = {}) => ({
  report_id, period_start: period_end === "2026-11-08" ? "2026-11-07" : "2026-11-04", period_end,
  updated_at: "2026-11-07T14:00:00Z", sleep_updated_at: "2026-11-07T13:30:00Z", report_status: "completed", sleep_status: "available", stale: false,
  sleep_duration: 510, sleep_score: 86, sleep_bedtime: "21:15", sleep_wake_time: "06:45", ...extra
});
const historySample = (index, value) => ({ index, value, graph_value: value, clock: "unexpected" });
function setupHistory(extra = {}) {
  const reports = [historyReport("recent", "2026-11-08", { report_status: "in_progress", sleep_status: "unavailable", sleep_duration: null, sleep_score: null, sleep_bedtime: null, sleep_wake_time: null }), historyReport("older", "2026-11-05")];
  const stateEntry = registryEntity("sensor", "sleep_duration", "sensor.global_sleep");
  const context = setup([stateEntry], { [stateEntry.entity_id]: { state: "999", attributes: { unit_of_measurement: "min" } } });
  const { card, hass, calls } = context;
  hass.callWS = async request => {
    calls.push(request);
    const data = request.service_data;
    if (data?.report_id) return { response: { logs: [{ ...reports.find(report => report.report_id === data.report_id), series: {
      temperature: { samples: [historySample(0, 20), historySample(1, 21)] },
      noise: { samples: [historySample(0, 0), historySample(1, 7)] },
      light: { samples: [historySample(0, 0), historySample(1, 1)] }
    } }] } };
    return { response: { logs: reports, ...extra } };
  };
  card._tab = "sleep"; card._render();
  return { ...context, reports, stateEntry };
}

test("opening Sleep shows the selected period's temperature even without sleep estimates and never exports", async () => {
  const { card, calls, hass, stateEntry } = setupHistory(); card._tab = "remi"; card._render();
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[2].dispatchEvent({ type: "click" });
  await flush();
  assert.deepEqual(calls.map(call => call.service_data), [
    { remi_id: "REMI1", limit: 60, include_series: false, sync: false },
    { remi_id: "REMI1", limit: 1, report_id: "recent" }
  ]);
  assert.equal(calls[0].return_response, true);
  assert.equal(card._historyId, "recent");
  assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
  assert.match(card.shadowRoot.textContent, /Enregistrement en cours/);
  assert.doesNotMatch(card.shadowRoot.textContent, /Cet export cloud est ancien/);
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1);
  assert.match(card.shadowRoot.querySelector(".chart").textContent, /Température/);
  assert.equal(card.shadowRoot.querySelectorAll("polyline").length, 1);
  assert.ok(card.shadowRoot.querySelector(".history-latest"));
  assert.doesNotMatch(card.shadowRoot.querySelector(".body-sleep").textContent, /8 h 30|86\/100|999/);
  card._render(); card.hass = { ...hass, states: { [stateEntry.entity_id]: { state: "1000", attributes: {} } } };
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[0].dispatchEvent({ type: "click" });
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[2].dispatchEvent({ type: "click" });
  assert.equal(calls.length, 2, "render, entity updates and return before the TTL must reuse the current journal");
});

test("date selection navigates actual journals and never invents missing calendar days", async () => {
  const { card, calls } = setupHistory(); await card._loadHistory();
  assert.equal(card.shadowRoot.querySelector(".history-date").querySelectorAll("option").length, 2);
  assert.equal(card.shadowRoot.querySelector(".history-next").disabled, true);
  card.shadowRoot.querySelector(".history-previous").dispatchEvent({ type: "click" });
  await flush();
  assert.equal(card._historyId, "older");
  assert.equal(card.shadowRoot.querySelector(".history-previous").disabled, true);
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["8 h 30", "86/100", "21:15", "06:45"]);
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "older" });
  assert.doesNotMatch(card.shadowRoot.querySelector(".body-sleep").textContent, /999|Enregistrement en cours/);
  card.shadowRoot.querySelector(".history-next").dispatchEvent({ type: "click" });
  await flush();
  assert.equal(card._historyId, "recent");
  const select = card.shadowRoot.querySelector(".history-date"); select.value = "older"; select.dispatchEvent({ type: "change" });
  await flush();
  assert.equal(card._historyId, "older");
  card._selectHistory("missing-date"); assert.equal(card._historyId, "older");
});

test("the single selected chart and all four statistics come from the same detailed journal", async () => {
  const { card, hass, calls, reports } = setupHistory(); await card._loadHistory();
  hass.callWS = async request => {
    calls.push(request);
    return { response: { logs: [{ ...reports.find(report => report.report_id === request.service_data.report_id), sleep_duration: 600, sleep_score: 90, sleep_bedtime: "20:00", sleep_wake_time: "06:00", series: { noise: { samples: [historySample(0, 0), historySample(1, 7)] } } }] } };
  };
  await card._selectHistory("older");
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "older" });
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["10 h 00", "90/100", "20:00", "06:00"]);
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1);
  assert.equal(card.shadowRoot.querySelectorAll("polyline").length, 0, "missing temperature is not silently replaced with noise");
  const chartKind = card.shadowRoot.querySelector(".history-chart-kind");
  assert.deepEqual(chartKind.querySelectorAll("option").map(option => option.value), ["temperature", "noise", "light"]);
  chartKind.value = "noise"; chartKind.dispatchEvent({ type: "change" });
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1);
  assert.equal(card.shadowRoot.querySelectorAll("polyline").length, 1);
  assert.equal(calls.length, 3, "switching chart kinds reuses the selected journal's series");
  await card._selectHistory("recent");
  assert.equal(card._historyCharts, true);
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "recent" });
  assert.equal(card._selectedHistory().report_id, "recent");
  await card._toggleHistoryCharts();
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 0);
  assert.equal(calls.length, 4);
});

test("explicit Refresh requests one export, announces the wait, then reloads the selected journal", async () => {
  const { card, hass, calls, reports } = setupHistory(); await card._loadHistory(); await card._selectHistory("older");
  let finish;
  hass.callWS = request => {
    calls.push(request);
    if (!request.service_data.report_id) return new Promise(resolve => { finish = resolve; });
    return Promise.resolve({ response: { logs: [reports[1]] } });
  };
  card.shadowRoot.querySelector(".history-refresh").dispatchEvent({ type: "click" });
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 60, include_series: false, refresh: true, sync: true });
  assert.match(card.shadowRoot.textContent, /environ 12 secondes/);
  assert.equal(card.shadowRoot.querySelector(".history-date").disabled, true);
  assert.equal(card.shadowRoot.querySelector(".history-refresh").disabled, true);
  card._loadHistory({ refresh: true }); card._selectHistory("recent");
  assert.equal(calls.length, 4); assert.equal(card._historyId, "older");
  finish({ response: { logs: reports, sync_status: "cooldown" } }); await flush();
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "older" });
  assert.equal(card._busy, false); assert.match(card.shadowRoot.textContent, /demandé récemment/);
  assert.match(card._message.text, /Journal cloud relu/);
  assert.doesNotMatch(card._message.text, /envoyé|récupéré/);
});

test("failed refresh retains the previous journal and its export date without claiming success", async () => {
  const { card, hass, calls } = setupHistory(); await card._loadHistory(); await card._selectHistory("older");
  const oldDetail = card._historyDetail;
  hass.callWS = async request => { calls.push(request); throw new Error("Cloud unavailable"); };
  await card._loadHistory({ refresh: true });
  assert.equal(card._historyDetail, oldDetail); assert.equal(card._historyId, "older");
  assert.equal(card._message.error, true); assert.match(card._message.text, /Cloud unavailable/);
  assert.ok(card.shadowRoot.querySelector(".history-export")); assert.equal(calls.length, 4);
});

test("a delayed catalogue cannot populate another REMI", async () => {
  const { card, hass, reports } = setupHistory(); let finish;
  hass.callWS = () => new Promise(resolve => { finish = resolve; });
  const pending = card._loadHistory(); card.setConfig({ device_id: "other" });
  finish({ response: { logs: reports } }); await pending;
  assert.equal(card._history, null); assert.equal(card._historyId, null); assert.equal(card._historyDetail, null); assert.equal(card._message, null);
});

test("a delayed chart response is ignored after the selected report changes", async () => {
  const { card, hass, reports } = setupHistory(); await card._loadHistory(); await card._toggleHistoryCharts(); let finish;
  hass.callWS = () => new Promise(resolve => { finish = resolve; });
  const pending = card._toggleHistoryCharts(); card._historyId = "older";
  finish({ response: { logs: [{ ...reports[0], series: { temperature: { samples: [historySample(0, 21)] } } }] } }); await pending;
  assert.notEqual(card._historyDetail?.report_id, "older"); assert.equal(card._selectedHistory().report_id, "older");
});

test("a mismatched detailed response cannot replace selected statistics", async () => {
  const { card, hass, reports } = setupHistory(); await card._loadHistory();
  hass.callWS = async () => ({ response: { logs: [reports[0]] } }); await card._selectHistory("older");
  assert.equal(card._historyDetail, null); assert.equal(card._selectedHistory().report_id, "older");
  assert.equal(card._message.error, true); assert.match(card._message.text, /ne correspond pas/);
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["8 h 30", "86/100", "21:15", "06:45"]);
});

for (const [locale, labels] of [["fr", ["Période enregistrée", "Jour disponible précédent", "Enregistrement en cours", "Actualiser"]], ["en", ["Recorded period", "Previous available day", "Recording in progress", "Refresh"]]]) {
  test(`${locale} localizes history navigation and status without changing service arguments`, async () => {
    const { card, hass, calls } = setupHistory(); card.hass = { ...hass, language: locale }; await card._loadHistory();
    assert.equal(card.shadowRoot.querySelector(".history-date").getAttribute("aria-label"), labels[0]);
    assert.equal(card.shadowRoot.querySelector(".history-previous").getAttribute("aria-label"), labels[1]);
    assert.ok(card.shadowRoot.textContent.includes(labels[2])); assert.equal(card.shadowRoot.querySelector(".history-refresh").textContent, labels[3]);
    assert.deepEqual(calls[0].service_data, { remi_id: "REMI1", limit: 60, include_series: false, sync: false });
  });
}

test("no journal and undated metadata do not invent zero statistics or an old-report warning", async () => {
  const { card, hass } = setupHistory(); hass.callWS = async () => ({ response: { logs: [] } }); await card._loadHistory();
  assert.match(card.shadowRoot.textContent, /Aucun bilan disponible/); assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
  assert.doesNotMatch(card.shadowRoot.textContent, /ancien/);
  card._history = { logs: [{ report_id: "undated", period_start: '<img onerror="fail">', period_end: "2026-02-31", report_status: "unknown" }] }; card._historyId = "undated"; card._render();
  assert.match(card.shadowRoot.textContent, /Période non datée|non communiqué/); assert.equal(card.shadowRoot.querySelectorAll("img").length, 0);
  assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
});

test("the latest available sleep summary changes the whole selected period rather than filling empty statistics", async () => {
  const { card, calls } = setupHistory(); await card._loadHistory();
  assert.equal(card._historyId, "recent");
  assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
  assert.doesNotMatch(card.shadowRoot.textContent, /86\/100|8 h 30/);
  card.shadowRoot.querySelector(".history-latest").dispatchEvent({ type: "click" }); await flush();
  assert.equal(card._historyId, "older");
  assert.equal(card._selectedHistory().report_id, "older");
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "older" });
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["8 h 30", "86/100", "21:15", "06:45"]);
  assert.equal(card.shadowRoot.querySelector(".history-latest"), undefined);
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1);
  assert.ok(calls.every(call => call.service_data?.sync !== true));
});

for (const missing of ["sleep_duration", "sleep_score"]) {
  test(`latest summary ignores unfinished or unavailable reports but accepts a valid summary without ${missing}`, async () => {
    const { card, reports } = setupHistory();
    reports[1][missing] = null;
    reports.splice(1, 0,
      historyReport("unfinished", "2026-11-07", { report_status: "in_progress" }),
      historyReport("unavailable", "2026-11-06", { sleep_status: "unavailable" }),
      historyReport("empty", "2026-11-06", { sleep_duration: 0, sleep_score: 0 })
    );
    await card._loadHistory();
    card.shadowRoot.querySelector(".history-latest").dispatchEvent({ type: "click" }); await flush();
    assert.equal(card._historyId, "older");
    assert.equal(card._selectedHistory()[missing], null);
    assert.equal(card.shadowRoot.querySelector(".history-latest"), undefined);
  });
}

test("no latest-summary action is offered when there is no completed available summary", async () => {
  const { card, reports } = setupHistory(); reports[1].sleep_status = "unavailable";
  await card._loadHistory();
  assert.equal(card.shadowRoot.querySelector(".history-latest"), undefined);
  assert.equal(card._historyId, "recent"); assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
});

test("a real midnight estimate is retained while an entirely empty report has no placeholder statistic cards", async () => {
  const { card, reports } = setupHistory();
  reports[0].sleep_bedtime = "00:00";
  await card._loadHistory();
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["—", "—", "00:00", "—"]);
  reports[0].sleep_bedtime = null; card._historyDetail = null; card._render();
  assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
});

test("history chart selection is local, bounded to known kinds and never downloads another period", async () => {
  const { card, calls } = setupHistory(); await card._loadHistory();
  for (const [kind, label] of [["noise", card.t("noiseChart")], ["light", card.t("lightReference")], ["temperature", card.t("temperature")]]) {
    const select = card.shadowRoot.querySelector(".history-chart-kind"); select.value = kind; select.dispatchEvent({ type: "change" });
    assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1);
    assert.ok(card.shadowRoot.querySelector(".chart").textContent.includes(label));
    assert.equal(card._historyId, "recent"); assert.equal(calls.length, 2);
  }
  const select = card.shadowRoot.querySelector(".history-chart-kind"); select.value = '<img onerror="fail">'; select.dispatchEvent({ type: "change" });
  assert.ok(card.shadowRoot.querySelector(".chart").textContent.includes(card.t("temperature")));
  assert.equal(card.shadowRoot.querySelectorAll("img").length, 0); assert.equal(calls.length, 2);
});

test("sleep update and curve export dates come from the selected report, separately from global sensor values", async () => {
  const { card, hass, reports } = setupHistory();
  const updatedEntry = registryEntity("sensor", "sleep_updated_at", "sensor.global_updated");
  card._entities.push(updatedEntry); hass.states[updatedEntry.entity_id] = { state: "2026-11-16T20:00:00Z", attributes: {} };
  await card._loadHistory(); await card._selectHistory("older");
  const info = card.shadowRoot.querySelector(".history-info"); assert.ok(info); assert.equal(info.open, false);
  assert.ok(info.textContent.includes(new Date(reports[1].sleep_updated_at).toLocaleString("fr")));
  assert.ok(info.textContent.includes(new Date(reports[1].updated_at).toLocaleString("fr")));
  assert.ok(!info.textContent.includes(new Date(hass.states[updatedEntry.entity_id].state).toLocaleString("fr")));
  card._historyDetail.sleep_updated_at = null; card._render();
  assert.doesNotMatch(card.shadowRoot.querySelector(".history-info").textContent, /Invalid Date/);
});

test("returning to Sleep revalidates after twenty minutes and refetches the selected detail even with unchanged metadata", async t => {
  let now = 1_800_000_000_000; t.mock.method(Date, "now", () => now);
  const { card, hass, calls, reports } = setupHistory(); await card._loadHistory(); await card._selectHistory("older");
  const previousDetail = card._historyDetail;
  now += 20 * 60 * 1000 - 1;
  card._switchTab("remi"); card._switchTab("sleep"); await flush();
  assert.equal(calls.length, 3);
  hass.callWS = async request => {
    calls.push(request);
    return { response: { logs: request.service_data.report_id ? [{ ...reports[1], series: { temperature: { samples: [historySample(0, 24), historySample(1, 25)] } } }] : reports } };
  };
  now += 1; card._switchTab("remi"); card._switchTab("sleep"); await flush();
  assert.deepEqual(calls.slice(-2).map(call => call.service_data), [
    { remi_id: "REMI1", limit: 60, include_series: false, refresh: true, sync: false },
    { remi_id: "REMI1", limit: 1, report_id: "older" }
  ]);
  assert.equal(card._historyId, "older"); assert.notEqual(card._historyDetail, previousDetail);
  assert.equal(card._historyDetail.updated_at, previousDetail.updated_at);
  assert.equal(card._historyDetail.series.temperature.samples[0].value, 24);
  assert.ok(calls.every(call => call.service_data?.sync !== true));
});

test("an expired active Sleep tab reads once on HA updates and never requests a device export", async t => {
  let now = 1_800_000_000_000; t.mock.method(Date, "now", () => now);
  const { card, hass, calls, reports } = setupHistory(); await card._loadHistory();
  card.hass = { ...hass, states: { ...hass.states, "sensor.unrelated": { state: "one" } } };
  assert.equal(calls.length, 2);
  let finish;
  hass.callWS = request => {
    calls.push(request);
    return request.service_data.report_id ? Promise.resolve({ response: { logs: [reports[0]] } }) : new Promise(resolve => { finish = resolve; });
  };
  now += 20 * 60 * 1000;
  card.hass = { ...hass, states: { ...hass.states, "sensor.unrelated": { state: "two" } } };
  card.hass = { ...hass, states: { ...hass.states, "sensor.unrelated": { state: "three" } } };
  assert.equal(calls.length, 3);
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 60, include_series: false, refresh: true, sync: false });
  finish({ response: { logs: reports } }); await flush();
  assert.equal(calls.length, 4); assert.equal(card._busy, false);
  assert.ok(calls.every(call => call.service_data?.sync !== true));
});

test("failed passive revalidation retains the old journal and backs off until the next TTL", async t => {
  let now = 1_800_000_000_000; t.mock.method(Date, "now", () => now);
  const { card, hass, calls } = setupHistory(); await card._loadHistory();
  const oldDetail = card._historyDetail, oldHistory = card._history;
  hass.callWS = async request => { calls.push(request); throw new Error("Cloud unavailable"); };
  now += 20 * 60 * 1000;
  card._switchTab("remi"); card._switchTab("sleep"); await flush();
  assert.equal(calls.length, 3); assert.equal(card._message.error, true);
  assert.equal(card._historyDetail, oldDetail); assert.equal(card._history, oldHistory);
  card._switchTab("remi"); card._switchTab("sleep"); card.hass = { ...hass }; await flush();
  assert.equal(calls.length, 3, "every HA state update must not retry a failed cloud request");
  now += 20 * 60 * 1000;
  card._switchTab("remi"); card._switchTab("sleep"); await flush();
  assert.equal(calls.length, 4); assert.ok(calls.every(call => call.service_data?.sync !== true));
});

test("temperature chart breaks at null readings and missing indexes without plotting missing raw zero", () => {
  const { card } = setupHistory();
  const chart = card._chart("temperature", { samples: [historySample(0, 20), historySample(1, 21), { ...historySample(2, null), raw_value: 0 }, historySample(3, 22), historySample(4, 22), historySample(7, 23)] });
  assert.equal(chart.querySelectorAll("polyline").length, 2); assert.equal(chart.querySelectorAll("circle").length, 1);
  assert.ok(chart.querySelectorAll("polyline").every(line => line.getAttribute("points").split(" ").length === 2));
  assert.match(chart.textContent, /°C/);
});

test("temperature graphs use the same physical scale across reports instead of exaggerating small changes", () => {
  const { card } = setupHistory();
  const points = chart => chart.querySelector("polyline").getAttribute("points").split(" ").map(point => point.split(",").map(Number));
  const narrow = card._chart("temperature", { samples: [historySample(0, 20), historySample(1, 20.2)] });
  const wide = card._chart("temperature", { samples: [historySample(0, 20), historySample(1, 40)] });
  assert.equal(points(narrow)[0][1], points(wide)[0][1]);
  assert.ok(Math.abs(points(narrow)[0][1] - points(narrow)[1][1]) < 1);
  assert.equal(points(wide)[1][1], 11);
  assert.ok(narrow.querySelectorAll("text").some(label => label.textContent === "-10"));
  assert.ok(narrow.querySelectorAll("text").some(label => label.textContent === "40"));
});

test("noise remains relative and light uses its binary reference scale without claiming decibels or lux", () => {
  const { card } = setupHistory();
  for (const [kind, samples, topLabel] of [
    ["noise", [historySample(0, 0), historySample(1, 255)], "100"],
    ["light", [{ ...historySample(0, 0), graph_value: 0 }, { ...historySample(1, 1), graph_value: 100 }], "1"]
  ]) {
    const chart = card._chart(kind, { samples });
    const points = chart.querySelector("polyline").getAttribute("points").split(" ").map(point => point.split(",").map(Number));
    assert.equal(points[0][1], 103); assert.equal(points[1][1], 11);
    assert.ok(chart.querySelectorAll("text").some(label => label.textContent === topLabel));
    assert.doesNotMatch(chart.textContent, /\bdB\b|\blux\b/i);
  }
});

test("recorded face markers retain their own clock, use translated faces and never claim detected sleep", () => {
  const { card, hass } = setupHistory();
  const events = [
    { minute_offset: 0, clock: "12:00", face: "awake" },
    { minute_offset: 600, clock: "22:00", face: "semi_awake" },
    { minute_offset: 720, clock: "00:00", face: "sleepy" },
    { minute_offset: 1200, clock: "08:00", face: "smiley" },
    { minute_offset: 1439, clock: "11:59", face: "off" }
  ];
  for (const locale of ["fr", "en"]) {
    card.hass = { ...hass, language: locale };
    const chart = card._chart("temperature", { samples: [historySample(0, 20), historySample(1, 21)] }, events);
    const markers = chart.querySelectorAll(".face-event");
    assert.equal(markers.length, events.length);
    markers.forEach((marker, index) => {
      const label = `${events[index].clock} · ${card.t(events[index].face)}`;
      assert.equal(marker.getAttribute("aria-label"), label); assert.equal(marker.querySelector("title").textContent, label);
    });
    assert.equal(markers[0].querySelector("circle").getAttribute("cx"), "32");
    assert.equal(markers.at(-1).querySelector("circle").getAttribute("cx"), "292");
    assert.equal(chart.querySelector(".chart-face-note").textContent, card.t("faceEvents"));
    assert.match(chart.querySelector(".chart-face-note").textContent, locale === "fr" ? /pas les heures de sommeil détectées/ : /not detected sleep times/);
  }
});

test("malformed face events cannot create markers, markup or a chart without real samples", () => {
  const { card } = setupHistory();
  const valid = { minute_offset: 720, clock: "00:00", face: "sleepy" };
  const malformed = [null, "unknown", { ...valid, minute_offset: -1 }, { ...valid, minute_offset: 1440 }, { ...valid, minute_offset: 1.5 }, { ...valid, clock: "24:00" }, { ...valid, clock: '<img onerror="fail">' }, { ...valid, face: "unknown" }, { ...valid, face: '<img onerror="fail">' }];
  const chart = card._chart("temperature", { samples: [historySample(0, 20)] }, malformed);
  assert.equal(chart.querySelectorAll(".face-event").length, 0); assert.equal(chart.querySelectorAll("img").length, 0);
  assert.equal(chart.querySelector(".chart-face-note"), undefined);
  const empty = card._chart("temperature", { samples: [] }, [valid]);
  assert.equal(empty.querySelectorAll("svg").length, 0); assert.equal(empty.querySelectorAll(".face-event").length, 0);
});

test("changing the report replaces face markers without deriving them from sleep estimates", async () => {
  const { card, reports } = setupHistory();
  reports[0].face_events = [{ minute_offset: 720, clock: "00:00", face: "off" }];
  reports[1].face_events = [{ minute_offset: 480, clock: "20:00", face: "sleepy" }];
  await card._loadHistory();
  assert.deepEqual(card.shadowRoot.querySelectorAll(".face-event").map(node => node.getAttribute("aria-label")), [`00:00 · ${card.t("off")}`]);
  await card._selectHistory("older");
  assert.deepEqual(card.shadowRoot.querySelectorAll(".face-event").map(node => node.getAttribute("aria-label")), [`20:00 · ${card.t("sleepy")}`]);
  card._historyDetail.face_events = []; card._render();
  assert.equal(card.shadowRoot.querySelectorAll(".face-event").length, 0);
  assert.ok(card.shadowRoot.querySelectorAll(".stat-value").some(node => node.textContent === "21:15"));
});

for (const locale of ["fr", "en"]) {
  test(`${locale} compact Sleep preserves a 180-point report, fixed scales, dates and face markers from normal layout`, async () => {
    const { card, hass, calls, reports } = setupHistory();
    const detailed = {
      ...reports[1],
      series: { temperature: { samples: Array.from({ length: 180 }, (_, index) => historySample(index, 20 + index % 10 / 10)) } },
      face_events: [{ minute_offset: 30, clock: "12:30", face: "awake" }, { minute_offset: 720, clock: "00:00", face: "sleepy" }]
    };
    const expected = JSON.stringify(detailed);
    hass.callWS = async request => { calls.push(request); return { response: { logs: request.service_data.report_id ? [request.service_data.report_id === "older" ? detailed : reports[0]] : reports } }; };
    card.hass = { ...hass, language: locale }; await card._loadHistory(); await card._selectHistory("older");
    const initialCalls = calls.length; let originalPoints, originalMarkers;
    for (const layout of ["full", "compact", "full"]) {
      card.setConfig({ layout });
      assert.equal(card._historyId, "older"); assert.equal(JSON.stringify(card._selectedHistory()), expected);
      assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["8 h 30", "86/100", "21:15", "06:45"]);
      assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1);
      const chart = card.shadowRoot.querySelector(".chart"), svg = chart.querySelector("svg");
      assert.equal(svg.getAttribute("role"), "img"); assert.equal(svg.getAttribute("aria-label"), card.t("temperature"));
      const points = chart.querySelector("polyline").getAttribute("points").split(" ").map(point => point.split(",").map(Number));
      assert.equal(points.length, 180); assert.ok(points.at(-1)[0] < 100, "a six-hour sample window must not stretch across a whole day");
      const horizontal = chart.querySelectorAll("line").filter(line => line.getAttribute("y1") === line.getAttribute("y2")).map(line => Number(line.getAttribute("y1")));
      const low = Math.max(...horizontal), high = Math.min(...horizontal);
      const normalized = points.map(([x, y]) => [x, (low - y) / (low - high)]);
      if (originalPoints) normalized.forEach((point, index) => { assert.equal(point[0], originalPoints[index][0]); assert.ok(Math.abs(point[1] - originalPoints[index][1]) < 1e-10); });
      else originalPoints = normalized;
      const labels = chart.querySelectorAll("text").map(node => node.textContent);
      for (const label of ["-10", "40", "12:00", "00:00", "11:58"]) assert.ok(labels.includes(label));
      const markers = chart.querySelectorAll(".face-event").map(marker => [marker.getAttribute("aria-label"), marker.querySelector("circle").getAttribute("cx")]);
      assert.deepEqual(markers.map(item => item[0]), [`12:30 · ${card.t("awake")}`, `00:00 · ${card.t("sleepy")}`]);
      if (originalMarkers) assert.deepEqual(markers, originalMarkers); else originalMarkers = markers;
      const info = card.shadowRoot.querySelector(".history-info"), summary = info.querySelector("summary");
      assert.equal(summary.getAttribute("aria-label") || summary.textContent, card.t("historyInfo"));
      assert.ok(info.textContent.includes(new Date(detailed.updated_at).toLocaleString(locale)));
      assert.ok(info.textContent.includes(new Date(detailed.sleep_updated_at).toLocaleString(locale)));
      assert.equal(card.shadowRoot.querySelector(".history-date").getAttribute("aria-label"), card.t("historyPeriod"));
      assert.equal(card.shadowRoot.querySelector(".history-chart-kind").getAttribute("aria-label"), card.t("historyChartKind"));
      assert.equal(card.shadowRoot.querySelector(".history-previous").getAttribute("aria-label"), card.t("previousReport"));
      assert.equal(card.shadowRoot.querySelector(".history-next").getAttribute("aria-label"), card.t("nextReport"));
    }
    assert.equal(calls.length, initialCalls, "layout changes must not re-read or export the journal");
  });
}

test("compact Sleep keeps information and period navigation accessible when charts are hidden and restored", async () => {
  const { card, calls } = setupHistory(); card.setConfig({ layout: "compact" }); await card._loadHistory(); await card._selectHistory("older");
  const period = card._historyId, stats = card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent);
  let info = card.shadowRoot.querySelector(".history-info"); info.open = true;
  info.querySelector(".history-charts").dispatchEvent({ type: "click" }); await flush();
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 0);
  info = card.shadowRoot.querySelector(".history-info"); assert.ok(info); assert.equal(info.open, true);
  assert.ok(card.shadowRoot.querySelector(".history-date")); assert.ok(card.shadowRoot.querySelector(".history-next"));
  assert.equal(card._historyId, period); assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), stats);
  const count = calls.length; info.querySelector(".history-charts").dispatchEvent({ type: "click" }); await flush();
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 1); assert.equal(card.shadowRoot.querySelector(".history-info").open, true);
  assert.equal(card._historyId, period); assert.equal(calls.length, count + 1);
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: period });
  const refresh = card.shadowRoot.querySelector(".history-refresh"); assert.equal(refresh.getAttribute("aria-label"), card.t("refresh"));
  refresh.dispatchEvent({ type: "click" }); await flush();
  assert.deepEqual(calls.at(-2).service_data, { remi_id: "REMI1", limit: 60, include_series: false, refresh: true, sync: true });
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: period });
  assert.equal(card._historyId, period); assert.equal(card.shadowRoot.querySelector(".history-info").open, true);
});

test("partial series keep a fixed noon-to-noon horizontal scale and isolated points remain visible", () => {
  const { card } = setupHistory();
  const partial = card._chart("noise", { samples: [historySample(0, 1), historySample(1, 2)] });
  const points = partial.querySelector("polyline").getAttribute("points").split(" ").map(point => point.split(",").map(Number));
  assert.equal(points[0][0], 32); assert.ok(points[1][0] < 33, "two minutes must not stretch to the full 24-hour axis");
  assert.match(partial.textContent, /12:0000:0011:58/); assert.doesNotMatch(partial.textContent, /unexpected/);
  const isolated = card._chart("noise", { samples: [historySample(719, 0)] });
  assert.equal(isolated.querySelector("circle").getAttribute("cx"), "292");
});

test("zero noise and zero light remain valid readings, while unavailable series remain empty", () => {
  const { card } = setupHistory();
  for (const kind of ["noise", "light"]) {
    const chart = card._chart(kind, { samples: [historySample(0, 0), historySample(1, 0)] });
    assert.equal(chart.querySelectorAll("polyline").length, 1); assert.doesNotMatch(chart.textContent, /Aucune courbe/);
    if (kind === "light") assert.ok(chart.querySelector("polyline").getAttribute("points").split(" ").every(point => point.endsWith(",103")));
  }
  for (const samples of [[], [historySample(0, null)], [historySample(-1, 20)], [historySample(720, 20)], [{ ...historySample(2, 20), valid: false }]]) {
    const chart = card._chart("temperature", { samples });
    assert.equal(chart.querySelectorAll("svg").length, 0); assert.match(chart.textContent, /Aucune courbe/);
  }
});

const displayKeys = ["show_face", "show_brightness", "show_face_brightness", "show_temperature", "show_connection", "show_music", "show_alarms", "show_sleep", "show_naps"];
const displayInput = (editor, key) => editor.shadowRoot.querySelectorAll("input").find(input => input.dataset.option === key);

test("all display controls default to visible and preserve the compact music disclosure", () => {
  const { card, calls } = setup(); card.setConfig({ type: "custom:urbanhello-remi-card" });
  assert.ok(card.shadowRoot.querySelector(".faces")); assert.ok(card.shadowRoot.querySelector(".temperature"));
  assert.ok(card.shadowRoot.querySelector(".connection-status")); assert.equal(card.shadowRoot.querySelector(".music").open, false);
  assert.equal(card.shadowRoot.querySelector(".tabs").querySelectorAll("button").length, 4);
  assert.equal(calls.length, 0);
});

test("display settings remove selected controls and collapse a single remaining tab", () => {
  const { card, calls } = setup(); card.setConfig(Object.fromEntries(displayKeys.map(key => [key, false])));
  for (const selector of [".faces", ".face-toggle", ".temperature", ".connection-status", ".music", ".tabs", ".hero-top"]) assert.equal(card.shadowRoot.querySelector(selector), undefined);
  const labels = card.shadowRoot.querySelectorAll("input,select").map(input => input.getAttribute("aria-label"));
  for (const key of ["face", "brightness", "face_brightness", "volume", "musicMode"]) assert.ok(!labels.includes(card.t(key)), key);
  assert.ok(card.shadowRoot.querySelector(".face-art"), "hiding the selector does not misrepresent the observed face illustration");
  assert.equal(calls.length, 0);
});

for (const [locale, heading, connectionLabel] of [["fr", "Afficher sur la carte", "État de connexion"], ["en", "Show on the card", "Connection status"]]) {
  test(`${locale} visual editor saves false booleans and preserves device, title and other options`, async () => {
    const { hass } = setup(); const editor = new UrbanhelloRemiCardEditor();
    editor.setConfig({ type: "custom:urbanhello-remi-card", device_id: "device-1", title: "Child", extra_option: 123 }); editor.hass = { ...hass, language: locale }; await flush();
    assert.match(editor.shadowRoot.textContent, new RegExp(heading));
    assert.equal(displayInput(editor, "show_connection").getAttribute("aria-label"), connectionLabel);
    assert.ok(displayKeys.every(key => displayInput(editor, key).checked));
    let saved; editor.addEventListener("config-changed", event => { saved = event.detail.config; });
    const toggle = displayInput(editor, "show_music"); toggle.checked = false; toggle.dispatchEvent({ type: "change" });
    assert.equal(saved.show_music, false); assert.equal(saved.device_id, "device-1"); assert.equal(saved.title, "Child"); assert.equal(saved.extra_option, 123);
    editor.setConfig(saved); assert.equal(displayInput(editor, "show_music").checked, false);
    displayInput(editor, "show_music").checked = true; displayInput(editor, "show_music").dispatchEvent({ type: "change" });
    assert.equal(saved.show_music, true);
  });
}

test("display configuration rejects strings, numbers, nulls and arrays without replacing valid settings", () => {
  const { card } = setup(); card.setConfig({ show_music: false });
  for (const value of ["false", 0, 1, null, undefined, [], {}]) assert.throws(() => card.setConfig({ show_music: value }), /activées ou désactivées/);
  assert.equal(card._config.show_music, false);
  for (const value of [null, [], "wrong"]) assert.throws(() => card.setConfig(value));
  const editor = new UrbanhelloRemiCardEditor(); assert.throws(() => editor.setConfig({ show_sleep: "true" }));
});

test("an in-progress card form survives same-device config and Home Assistant state updates", () => {
  const entry = registryEntity("switch", "alarm_original", "switch.alarm");
  const { card, hass } = setup([entry], { [entry.entity_id]: { state: "on", attributes: { event_id: "cloud1", time: "07:00", alarm_name: "Wake" } } });
  card._openForm("alarm", { event_id: "cloud1", time: "07:00", alarm_name: "Wake" }, entry.entity_id);
  const draft = card._form; draft.inputs.get("time").value = "08:45"; draft.inputs.get("time").dispatchEvent({ type: "change" });
  card.setConfig({ title: "Compact", show_temperature: false });
  card.hass = { ...hass, states: { [entry.entity_id]: { state: "off", attributes: { event_id: "cloud2", time: "07:00" } } } };
  assert.equal(card._form, draft); assert.equal(card.shadowRoot.querySelector("form"), draft.element);
  assert.equal(draft.inputs.get("time").value, "08:45"); assert.ok(draft.dirty.has("time"));
});

test("the visual editor retains a focused unfinished text edit across state updates", async () => {
  const { hass } = setup(); const editor = new UrbanhelloRemiCardEditor(); editor.setConfig({ title: "Initial" }); editor.hass = hass; await flush();
  const input = editor.shadowRoot.querySelectorAll("input").find(node => node.type === "text");
  input.value = "Unfinished"; editor.shadowRoot.activeElement = input; editor.hass = { ...hass, states: { changed: true } };
  assert.equal(editor.shadowRoot.querySelectorAll("input").find(node => node.type === "text"), input);
  assert.equal(input.value, "Unfinished");
  input.dispatchEvent({ type: "change" }); editor.shadowRoot.activeElement = null; editor.shadowRoot.dispatchEvent({ type: "focusout" }); await flush();
  assert.equal(editor._config.title, "Unfinished");
});

test("hiding the active tab returns to REMI and detached tab handlers cannot load hidden content", async () => {
  const { card, calls } = setup(); const oldTabs = card.shadowRoot.querySelector(".tabs").querySelectorAll("button");
  card._tab = "sleep"; card.setConfig({ show_alarms: false, show_sleep: false, show_naps: false });
  assert.equal(card._tab, "remi"); assert.equal(card.shadowRoot.querySelector(".tabs"), undefined);
  for (const tab of oldTabs.slice(1)) tab.dispatchEvent({ type: "click" });
  await card._loadNaps(); await card._loadHistory({ refresh: true }); card._toggleHistoryCharts(); card._openForm("alarm"); card._openForm("nap");
  assert.equal(card._tab, "remi"); assert.equal(card._form, null); assert.equal(calls.length, 0);
});

test("a hidden draft remains saved but cannot submit or delete until its tab is shown again", async () => {
  const { card, calls } = setup(); card._tab = "alarms"; card._openForm("alarm", { event_id: "cloud1", time: "07:00", alarm_name: "Wake" });
  const draft = card._form; draft.inputs.get("time").value = "08:15"; draft.inputs.get("time").dispatchEvent({ type: "change" });
  card._confirmDelete(draft, draft.element); const deleteButton = draft.element.querySelector(".confirm").querySelector(".danger");
  card.setConfig({ show_alarms: false }); assert.equal(card._tab, "remi"); assert.equal(card._form, draft); assert.equal(card.shadowRoot.querySelector("form"), undefined);
  draft.element.dispatchEvent({ type: "submit", preventDefault() {} }); deleteButton.dispatchEvent({ type: "click" }); await flush();
  assert.equal(calls.length, 0);
  card.setConfig({ show_alarms: true }); assert.equal(card._tab, "alarms"); assert.equal(card._form, draft); assert.equal(draft.inputs.get("time").value, "08:15");
});

test("detached face, brightness and music controls cannot execute after being hidden", async () => {
  const faceEntry = registryEntity("select", "face", "select.face"), playerEntry = registryEntity("media_player", "music_player", "media_player.remi");
  const { card, calls } = setup([faceEntry, playerEntry], { "select.face": { state: "awake", attributes: { options: FACE_OPTIONS } }, "media_player.remi": { state: "unknown", attributes: {} } });
  const faceButton = card.shadowRoot.querySelector(".faces").querySelector("button"), musicButton = card.shadowRoot.querySelector(".music-actions").querySelector("button");
  const slider = card.shadowRoot.querySelectorAll("input").find(input => input.getAttribute("aria-label") === card.t("brightness"));
  card.setConfig({ show_face: false, show_brightness: false, show_face_brightness: false, show_music: false });
  faceButton.dispatchEvent({ type: "click" }); musicButton.dispatchEvent({ type: "click" }); slider.value = "55"; slider.dispatchEvent({ type: "change" });
  card._entityAction("number", "face_brightness", "set_value", { value: 6 }); card._entityAction("number", "volume", "set_value", { value: 70 }); card._entityAction("select", "music_mode", "select_option", { option: "normal" }); card._browse(); await flush();
  assert.equal(calls.length, 0);
});

test("music is collapsed again after hiding it and a late browser response cannot reopen it", async () => {
  const player = registryEntity("media_player", "music_player"); const { card, hass } = setup([player]);
  disclosure(card, "remi:music").open = true; card.setConfig({ show_music: false }); card.setConfig({ show_music: true });
  assert.equal(disclosure(card, "remi:music").open, false);
  let finish; hass.callWS = () => new Promise(resolve => { finish = resolve; }); card._browse(); card.setConfig({ show_music: false });
  finish({ children: [{ title: "Track", can_play: true }] }); await flush();
  assert.equal(card._library, null); assert.equal(card.shadowRoot.querySelector(".library"), undefined);
});

test("alarm edits use the current cloud event_id even if it rotates while the form is open", async () => {
  const entry = registryEntity("switch", "alarm_original", "switch.user_alarm");
  const { card, hass, calls } = setup([entry], { [entry.entity_id]: { state: "on", attributes: { event_id: "current1", time: "07:00", alarm_name: "Wake" } } });
  card._tab = "alarms"; card._render(); card.shadowRoot.querySelector(".schedule").querySelector("button").dispatchEvent({ type: "click" });
  const draft = card._form; assert.equal(draft.id, "current1"); assert.equal(draft.alarmEntityId, entry.entity_id);
  draft.inputs.get("time").value = "08:30"; draft.inputs.get("time").dispatchEvent({ type: "change" });
  card.hass = { ...hass, states: { [entry.entity_id]: { state: "on", attributes: { event_id: "current2", time: "07:00", alarm_name: "Wake" } } } };
  draft.element.dispatchEvent({ type: "submit", preventDefault() {} }); await flush();
  assert.deepEqual(calls[0].service_data, { remi_id: "REMI1", event_id: "current2", time: "08:30" });
  assert.equal(entry.unique_id, "REMI1_alarm_original"); assert.equal(card._device().id, "device-1");
});

test("alarm deletion re-resolves the event_id after its confirmation was opened", async () => {
  const entry = registryEntity("switch", "alarm_original", "switch.user_alarm");
  const { card, hass, calls } = setup([entry], { [entry.entity_id]: { state: "on", attributes: { event_id: "current1" } } });
  card._openForm("alarm", { event_id: "current1", time: "07:00" }, entry.entity_id); const draft = card._form; card._confirmDelete(draft, draft.element);
  card.hass = { ...hass, states: { [entry.entity_id]: { state: "on", attributes: { event_id: "current2" } } } };
  draft.element.querySelector(".confirm").querySelector(".danger").dispatchEvent({ type: "click" }); await flush();
  assert.deepEqual(calls[0].service_data, { remi_id: "REMI1", event_id: "current2" });
});

test("alarm IDs use scoped time attributes or legacy suffixes only when the current attribute is absent", () => {
  const main = registryEntity("switch", "alarm_original", "switch.alarm"), time = registryEntity("time", "alarm_original_time", "time.alarm");
  const { card } = setup([main, time], { "switch.alarm": { state: "on", attributes: {} }, "time.alarm": { state: "07:00:00", attributes: { event_id: "current" } } });
  assert.equal(card._alarmEventId("switch.alarm"), "current"); assert.equal(card._alarmEventId("time.alarm"), "current");
  delete card._hass.states["time.alarm"].attributes.event_id; assert.equal(card._alarmEventId("switch.alarm"), "original"); assert.equal(card._alarmEventId("time.alarm"), "original");
  for (const invalid of [null, "", 42, "../other", "a".repeat(129)]) { card._hass.states["switch.alarm"].attributes.event_id = invalid; assert.equal(card._alarmEventId("switch.alarm"), null); }
  assert.equal(card._alarmEventId("switch.outside_registry"), null);
});

test("a removed or foreign-device alarm cannot be targeted from an old edit form", async () => {
  const entry = registryEntity("switch", "alarm_original", "switch.alarm"), { card, calls } = setup([entry], { "switch.alarm": { state: "on", attributes: { event_id: "current" } } });
  card._openForm("alarm", { event_id: "current", time: "07:00" }, entry.entity_id); const draft = card._form;
  draft.inputs.get("time").value = "09:30"; draft.inputs.get("time").dispatchEvent({ type: "change" });
  entry.device_id = "device-2";
  draft.element.dispatchEvent({ type: "submit", preventDefault() {} }); await flush();
  assert.equal(calls.length, 0); assert.equal(card._message.error, true); assert.match(card._message.text, /n’est plus disponible/);
  assert.equal(card._form, draft);
});

test("a suspended alarm draft does not freeze REMI states or deferred focusout rendering", async () => {
  const temperature = registryEntity("sensor", "temperature", "sensor.temperature"), online = registryEntity("binary_sensor", "online", "binary_sensor.online");
  const alive = registryEntity("binary_sensor", "alive", "binary_sensor.alive");
  const { card, hass } = setup([temperature, online, alive], {
    "sensor.temperature": { state: "21.7", attributes: { unit_of_measurement: "°C" } },
    "binary_sensor.online": { state: "on", attributes: {} }, "binary_sensor.alive": { state: "on", attributes: {} }
  });
  card._tab = "alarms"; card._openForm("alarm", { event_id: "cloud1", time: "07:00", alarm_name: "Wake" });
  const draft = card._form; draft.inputs.get("time").value = "08:15"; draft.inputs.get("time").dispatchEvent({ type: "change" });
  card.setConfig({ show_alarms: false });
  card.hass = { ...hass, states: { ...hass.states, "sensor.temperature": { state: "22.3", attributes: { unit_of_measurement: "°C" } }, "binary_sensor.online": { state: "off", attributes: {} } } };
  assert.equal(card.shadowRoot.querySelector(".temperature").textContent, "22.3 °C");
  assert.match(card.shadowRoot.querySelector(".connection-status").textContent, /Déconnecté/);
  assert.equal(card._form, draft); assert.equal(draft.inputs.get("time").value, "08:15");
  card.shadowRoot.activeElement = card.shadowRoot.querySelector("input");
  card.hass = { ...card.hass, states: { ...card.hass.states, "sensor.temperature": { state: "22.8", attributes: { unit_of_measurement: "°C" } } } };
  assert.equal(card.shadowRoot.querySelector(".temperature").textContent, "22.3 °C");
  assert.equal(card._renderPending, true);
  card.shadowRoot.activeElement = null; card.shadowRoot.dispatchEvent({ type: "focusout" }); await flush();
  assert.equal(card.shadowRoot.querySelector(".temperature").textContent, "22.8 °C");
  assert.equal(card._form, draft); assert.equal(draft.inputs.get("time").value, "08:15"); assert.ok(draft.dirty.has("time"));
  card.setConfig({ show_alarms: true }); assert.equal(card.shadowRoot.querySelector("form"), draft.element);
});

const customEntity = "script.example_routine";
const customState = (state = "off", attributes = {}) => ({ state, attributes: { friendly_name: "Example routine", ...attributes } });
const writes = calls => calls.filter(call => call.type === "call_service");
const optionField = (editor, key) => editor.shadowRoot.querySelectorAll("input,select").find(node => node.dataset.option === key);
const visualChoice = (editor, key, value) => editor.shadowRoot.querySelectorAll("button").find(node => node.dataset.option === key && node.dataset.value === value);
const customField = (editor, key) => editor.shadowRoot.querySelectorAll("input,select").find(node => node.dataset.customOption === key);
function setupCustom(entity = customEntity, state = "off", config = {}) {
  const result = setup([], state === null ? {} : { [entity]: customState(state) });
  result.card.setConfig({ show_custom_button: true, custom_button: { entity }, ...config });
  return result;
}

test("presentation defaults preserve the existing HA theme and leave custom actions opt-in", () => {
  const { card, hass, calls } = setup([], { [customEntity]: customState() });
  const themes = { darkMode: true, theme: "example_theme", themes: { example_theme: { "primary-color": "#edab20" } } };
  card.hass = { ...hass, themes };
  const originalTheme = structuredClone(themes);
  card.setConfig({ custom_button: { entity: customEntity } });
  assert.ok(card.shadowRoot.querySelector("ha-card").matches(".appearance-theme"));
  assert.ok(card.shadowRoot.querySelector("ha-card").matches(".layout-full"));
  assert.equal(card.shadowRoot.querySelector(".custom-button"), undefined);
  const fullSize = card.getCardSize();
  card.setConfig({ appearance: "remi", layout: "compact" });
  assert.ok(card.shadowRoot.querySelector("ha-card").matches(".appearance-remi"));
  assert.ok(card.shadowRoot.querySelector("ha-card").matches(".layout-compact"));
  assert.ok(card.getCardSize() < fullSize);
  assert.equal(card.getGridOptions().rows, "auto");
  assert.deepEqual(themes, originalTheme, "per-card appearance must never change HA's theme object");
  card.setConfig({ appearance: "glass", layout: "compact" });
  assert.ok(card.shadowRoot.querySelector("ha-card").matches(".appearance-glass"));
  assert.deepEqual(themes, originalTheme, "dark-glass styling must remain scoped to this card");
  card.setConfig({ appearance: "theme", layout: "full" });
  assert.ok(card.shadowRoot.querySelector("ha-card").matches(".appearance-theme"));
  assert.equal(card.getCardSize(), fullSize);
  assert.equal(card.getGridOptions().rows, "auto");
  assert.equal(writes(calls).length, 0);
});

test("invalid presentation and custom-action settings never replace the last valid configuration", () => {
  const { card } = setupCustom();
  const invalid = [
    { appearance: "dark" }, { appearance: null }, { appearance: 1 },
    { layout: "horizontal" }, { layout: null }, { layout: true },
    { show_custom_button: "true" }, { show_custom_button: 1 }, { show_custom_button: null },
    { custom_button: [] }, { custom_button: null }, { custom_button: "script.example" },
    { custom_button: { entity: 42 } }, { custom_button: { entity: "sensor.example" } },
    { custom_button: { entity: "script.first,script.second" } },
    { custom_button: { entity: "script.first\nscript.second" } },
    { custom_button: { entity: "https://example.invalid/action" } },
    { custom_button: { name: { text: "Not a label" } } },
    { custom_button: { icon: "<img src=x onerror=alert(1)>" } },
    { custom_button: { icon: "javascript:alert(1)" } },
    { custom_button: { skip_conditions: "false" } }, { custom_button: { skip_conditions: 1 } },
  ];
  const previous = card._config;
  for (const config of invalid) {
    assert.throws(() => card.setConfig(config), JSON.stringify(config));
    assert.equal(card._config, previous);
  }
  const editor = new UrbanhelloRemiCardEditor();
  for (const config of invalid) assert.throws(() => editor.setConfig(config), JSON.stringify(config));
});

for (const [domain, state, service, data] of [
  ["script", "off", "turn_on", {}],
  ["automation", "off", "trigger", { skip_condition: false }],
  ["scene", "2026-01-01T00:00:00+00:00", "turn_on", {}],
  ["scene", "unknown", "turn_on", {}],
  ["button", "unknown", "press", {}],
  ["input_button", "unknown", "press", {}],
]) {
  test(`custom ${domain} in state ${state} dispatches its native service once to the explicit external entity`, async () => {
    const entity = `${domain}.example_action`;
    const { card, calls } = setupCustom(entity, state);
    const button = card.shadowRoot.querySelector(".custom-button");
    assert.ok(button); assert.equal(button.disabled, false); assert.equal(writes(calls).length, 0);
    button.dispatchEvent({ type: "click" }); await flush();
    assert.deepEqual(writes(calls), [{ type: "call_service", domain, service, service_data: data, target: { entity_id: entity } }]);
    assert.equal(card.hass.states[entity].state, state, "a successful action does not invent a new entity state");
  });
}

test("automation condition bypass is explicit and uses HA's singular skip_condition field", async () => {
  const entity = "automation.example_action";
  const { card, calls } = setupCustom(entity, "off", { custom_button: { entity, skip_conditions: true } });
  card.shadowRoot.querySelector(".custom-button").dispatchEvent({ type: "click" }); await flush();
  assert.deepEqual(writes(calls)[0].service_data, { skip_condition: true });
  assert.equal(writes(calls)[0].target.entity_id, entity);
  assert.equal(Object.hasOwn(writes(calls)[0].service_data, "skip_conditions"), false);
});

test("custom actions become unavailable for missing targets, unavailable entities and running scripts", async () => {
  for (const [entity, state] of [[customEntity, null], [customEntity, "unavailable"], [customEntity, "unknown"], [customEntity, "on"], ["button.example_action", "unavailable"], ["input_button.example_action", "unavailable"]]) {
    const { card, calls } = setupCustom(entity, state);
    const button = card.shadowRoot.querySelector(".custom-button");
    assert.ok(button); assert.equal(button.disabled, true, `${entity} ${state}`);
    button.dispatchEvent({ type: "click" }); await flush();
    assert.equal(writes(calls).length, 0, `${entity} ${state}`);
  }
});

test("external target updates refresh availability while unrelated HA entities do not rebuild the card", () => {
  const { card, hass } = setupCustom();
  card.hass = hass; // Establish dependencies as HA does after configuring a card.
  const initialButton = card.shadowRoot.querySelector(".custom-button");
  card.hass = { ...hass, states: { ...hass.states, "sensor.unrelated": customState("42") } };
  assert.equal(card.shadowRoot.querySelector(".custom-button"), initialButton);
  card.hass = { ...card.hass, states: { ...card.hass.states, [customEntity]: customState("on") } };
  assert.equal(card.shadowRoot.querySelector(".custom-button").disabled, true);
  card.hass = { ...card.hass, states: { ...card.hass.states, [customEntity]: customState("off") } };
  assert.equal(card.shadowRoot.querySelector(".custom-button").disabled, false);
  const withoutTarget = { ...card.hass.states }; delete withoutTarget[customEntity];
  card.hass = { ...card.hass, states: withoutTarget };
  assert.equal(card.shadowRoot.querySelector(".custom-button").disabled, true);
});

test("custom labels stay literal text and untrusted entity metadata cannot inject markup", () => {
  const malicious = '<img src=x onerror="globalThis.customActionInjected=true">';
  const { card } = setupCustom(customEntity, "off", { custom_button: { entity: customEntity, name: malicious, icon: "mdi:play" } });
  assert.ok(card.shadowRoot.querySelector(".custom-button").textContent.includes(malicious));
  assert.equal(card.shadowRoot.querySelectorAll("img").length, 0);
  const icon = card.shadowRoot.querySelector(".custom-button").querySelector("ha-icon");
  assert.ok(icon); assert.equal(icon.getAttribute("icon") || icon.icon, "mdi:play");
  card.hass = { ...card.hass, states: { [customEntity]: customState("off", { friendly_name: malicious }) } };
  card.setConfig({ show_custom_button: true, custom_button: { entity: customEntity } });
  assert.equal(card.shadowRoot.querySelectorAll("img").length, 0);
  assert.equal(globalThis.customActionInjected, undefined);
});

test("custom actions reject double presses and surface a failed write without retry", async () => {
  const { card, hass, calls } = setupCustom();
  let reject;
  hass.callWS = request => { calls.push(request); return new Promise((_, fail) => { reject = fail; }); };
  const button = card.shadowRoot.querySelector(".custom-button");
  button.dispatchEvent({ type: "click" }); button.dispatchEvent({ type: "click" });
  assert.equal(writes(calls).length, 1);
  assert.equal(card.shadowRoot.querySelector(".custom-button").disabled, true);
  reject(new Error("Example action rejected")); await flush();
  assert.equal(writes(calls).length, 1);
  assert.equal(card._message.error, true); assert.match(card._message.text, /Example action rejected/);
  assert.equal(card.shadowRoot.querySelector(".custom-button").disabled, false);
  assert.equal(card.hass.states[customEntity].state, "off");
});

test("detached custom handlers cannot execute after changing the target or hiding the action", async () => {
  const other = "script.other_example";
  const { card, hass, calls } = setupCustom();
  hass.states[other] = customState("off");
  const first = card.shadowRoot.querySelector(".custom-button");
  card.setConfig({ show_custom_button: true, custom_button: { entity: other } });
  first.dispatchEvent({ type: "click" }); await flush();
  assert.equal(writes(calls).length, 0);
  const second = card.shadowRoot.querySelector(".custom-button");
  card.setConfig({ show_custom_button: false, custom_button: { entity: other } });
  second.dispatchEvent({ type: "click" }); await flush();
  assert.equal(writes(calls).length, 0);
  card.setConfig({ show_custom_button: true, custom_button: { entity: other } });
  second.dispatchEvent({ type: "click" }); await flush();
  assert.equal(writes(calls).length, 0, "re-enabling does not revive a detached handler");
  card.shadowRoot.querySelector(".custom-button").dispatchEvent({ type: "click" }); await flush();
  assert.equal(writes(calls).length, 1); assert.equal(writes(calls)[0].target.entity_id, other);
});

for (const outcome of ["resolve", "reject"]) {
  test(`a late custom action ${outcome} cannot place feedback on a newly configured target`, async () => {
    const { card, hass, calls } = setupCustom(); let finish;
    hass.callWS = request => { calls.push(request); return new Promise((resolve, reject) => { finish = outcome === "resolve" ? resolve : reject; }); };
    card.shadowRoot.querySelector(".custom-button").dispatchEvent({ type: "click" });
    const other = "script.other_example"; hass.states[other] = customState("off");
    card.setConfig({ show_custom_button: true, custom_button: { entity: other } });
    finish(outcome === "resolve" ? {} : new Error("Old target failed")); await flush();
    assert.equal(writes(calls).length, 1); assert.equal(card._message, null);
    assert.equal(card.shadowRoot.querySelector(".custom-button").disabled, false);
  });
}

test("disconnect invalidates a custom action's detached handler and late response", async () => {
  const { card, hass, calls } = setupCustom(); let finish;
  hass.callWS = request => { calls.push(request); return new Promise(resolve => { finish = resolve; }); };
  const button = card.shadowRoot.querySelector(".custom-button"); button.dispatchEvent({ type: "click" });
  card.isConnected = false; card.disconnectedCallback();
  button.dispatchEvent({ type: "click" }); finish({}); await flush();
  assert.equal(writes(calls).length, 1); assert.equal(card._message, null);
});

test("presentation and custom-action edits preserve an existing unsaved alarm draft", () => {
  const { card } = setupCustom(); card._openForm("alarm");
  const draft = card._form; const input = draft.inputs.get("name"); input.value = "Unsaved alarm"; input.dispatchEvent({ type: "change" });
  card.setConfig({ appearance: "remi", layout: "compact", show_custom_button: true, custom_button: { entity: "button.example_action", name: "My action" } });
  assert.equal(card._form, draft); assert.equal(card.shadowRoot.querySelector("form"), draft.element);
  assert.equal(input.value, "Unsaved alarm"); assert.ok(draft.dirty.has("name"));
});

function setupFirmware(value) {
  const online = registryEntity("binary_sensor", "online", "binary_sensor.device_online");
  const alive = registryEntity("binary_sensor", "alive", "binary_sensor.device_alive");
  const firmware = registryEntity("binary_sensor", "firmware_update", "binary_sensor.firmware_renamed");
  return { ...setup([online, alive, firmware], {
    [online.entity_id]: { state: "on", attributes: {} }, [alive.entity_id]: { state: "on", attributes: {} },
    ...(value === null ? {} : { [firmware.entity_id]: { state: value, attributes: {} } }),
  }), firmware };
}

test("a confirmed firmware alert opens only the current HA more-info entity beside connection status", () => {
  const { card, calls, firmware } = setupFirmware("on"); let event;
  card.addEventListener("hass-more-info", value => { event = value; });
  const alert = card.shadowRoot.querySelector(".firmware-update");
  assert.ok(alert); assert.ok(card.shadowRoot.querySelector(".connection-status"));
  assert.ok(alert.getAttribute("title") || alert.getAttribute("aria-label"), "the icon needs an accessible explanation");
  alert.dispatchEvent({ type: "click" });
  assert.equal(event.detail.entityId, firmware.entity_id);
  assert.equal(event.bubbles, true); assert.equal(event.composed, true);
  assert.equal(writes(calls).length, 0, "firmware information is never an install or update command");
});

test("firmware alerts are absent for off, unknown, unavailable, missing or hidden connection status", () => {
  for (const value of ["off", "unknown", "unavailable", null]) {
    const { card, calls } = setupFirmware(value);
    assert.equal(card.shadowRoot.querySelector(".firmware-update"), undefined, String(value));
    assert.equal(writes(calls).length, 0);
  }
  const { card, calls } = setupFirmware("on");
  card.setConfig({ show_connection: false });
  assert.equal(card.shadowRoot.querySelector(".firmware-update"), undefined);
  assert.equal(writes(calls).length, 0);
});

test("firmware status changes update the indicator using the registry's renamed entity", () => {
  const { card, hass, firmware } = setupFirmware("off");
  card.hass = { ...hass, states: { ...hass.states, [firmware.entity_id]: { state: "on", attributes: {} } } };
  assert.ok(card.shadowRoot.querySelector(".firmware-update"));
  card.hass = { ...card.hass, states: { ...card.hass.states, [firmware.entity_id]: { state: "unknown", attributes: {} } } };
  assert.equal(card.shadowRoot.querySelector(".firmware-update"), undefined);
});

for (const [locale, labels] of [
  ["fr", ["Thème Home Assistant", "Normale", "Compacte", "Afficher une action personnalisée", "Verre sombre"]],
  ["en", ["Home Assistant theme", "Normal", "Compact", "Show a custom action", "Dark glass"]],
]) {
  test(`${locale} editor saves independent presentation choices and a custom action without rewriting other settings`, async () => {
    const entity = "automation.example_action";
    const { hass } = setup([], { [entity]: customState("off") });
    const editor = new UrbanhelloRemiCardEditor();
    editor.setConfig({ type: "custom:urbanhello-remi-card", device_id: device.id, title: "Existing title", extra_option: 123, show_music: false, show_custom_button: true, custom_button: { entity, name: "Existing action", icon: "mdi:play" } });
    editor.hass = { ...hass, language: locale }; await flush();
    for (const label of labels) assert.ok(editor.shadowRoot.textContent.includes(label), label);
    assert.equal(visualChoice(editor, "appearance", "theme").getAttribute("aria-pressed"), "true");
    assert.equal(visualChoice(editor, "layout", "full").getAttribute("aria-pressed"), "true");
    assert.equal(optionField(editor, "show_custom_button").checked, true);
    assert.equal(customField(editor, "skip_conditions").checked, false);
    let saved;
    editor.addEventListener("config-changed", event => { saved = event.detail.config; });
    for (const [key, value] of [["appearance", "remi"], ["layout", "compact"]]) {
      visualChoice(editor, key, value).dispatchEvent({ type: "click" });
    }
    const name = customField(editor, "name"); name.value = "My revised action"; name.dispatchEvent({ type: "change" });
    const skip = customField(editor, "skip_conditions"); skip.checked = true; skip.dispatchEvent({ type: "change" });
    assert.equal(saved.appearance, "remi"); assert.equal(saved.layout, "compact");
    assert.deepEqual(saved.custom_button, { entity, name: "My revised action", icon: "mdi:play", skip_conditions: true });
    assert.equal(saved.title, "Existing title"); assert.equal(saved.device_id, device.id);
    assert.equal(saved.extra_option, 123); assert.equal(saved.show_music, false);
    const enabled = optionField(editor, "show_custom_button"); enabled.checked = false; enabled.dispatchEvent({ type: "change" });
    assert.equal(saved.show_custom_button, false);
    assert.equal(saved.custom_button.entity, entity, "hiding a button does not erase its saved target");
    const verifier = new UrbanhelloRemiCard(); assert.doesNotThrow(() => verifier.setConfig(saved));
  });
}

test("visual editor starts with the custom action disabled and allows incomplete configuration", async () => {
  const { hass } = setup(); const editor = new UrbanhelloRemiCardEditor();
  editor.setConfig({}); editor.hass = hass; await flush();
  assert.equal(optionField(editor, "show_custom_button").checked, false);
  assert.doesNotThrow(() => editor.setConfig({ show_custom_button: true, custom_button: {} }));
  assert.doesNotThrow(() => editor.setConfig({ show_custom_button: true, custom_button: { entity: "", name: "", icon: "", skip_conditions: false } }));
  const { card, calls } = setup();
  card.setConfig({ show_custom_button: true, custom_button: {} });
  const button = card.shadowRoot.querySelector(".custom-button");
  if (button) { assert.equal(button.disabled, true); button.dispatchEvent({ type: "click" }); }
  assert.equal(writes(calls).length, 0);
});

test("a focused custom-label draft survives unrelated HA updates and a locale change", async () => {
  const { hass } = setup([], { [customEntity]: customState() }); const editor = new UrbanhelloRemiCardEditor();
  editor.setConfig({ title: "Keep title", layout: "compact", show_custom_button: true, custom_button: { entity: customEntity, name: "Initial", icon: "mdi:play" } });
  editor.hass = hass; await flush();
  const input = customField(editor, "name"); input.value = "Unfinished label"; editor.shadowRoot.activeElement = input;
  editor.hass = { ...hass, language: "en", states: { ...hass.states, "sensor.unrelated": customState("99") } };
  assert.equal(customField(editor, "name"), input); assert.equal(input.value, "Unfinished label");
  input.dispatchEvent({ type: "change" }); editor.shadowRoot.activeElement = null;
  editor.shadowRoot.dispatchEvent({ type: "focusout" }); await flush();
  assert.equal(editor._config.custom_button.name, "Unfinished label");
  assert.equal(editor._config.custom_button.entity, customEntity); assert.equal(editor._config.custom_button.icon, "mdi:play");
  assert.equal(editor._config.title, "Keep title"); assert.equal(editor._config.layout, "compact");
  assert.ok(editor.shadowRoot.textContent.includes("Home Assistant theme"));
});

const nestedAction = () => ({
  type: "button", entity: customEntity, name: "Example embedded action", icon: "mdi:play",
  tap_action: { action: "perform-action", perform_action: "script.turn_on", target: { entity_id: customEntity } },
  hold_action: { action: "fire-dom-event", browser_mod: { service: "browser_mod.popup", data: { title: "Example options", content: { type: "entities", entities: ["input_number.example_duration"] } } } },
});
function nestedHelper(t, factory) {
  const previous = globalThis.loadCardHelpers;
  globalThis.loadCardHelpers = factory;
  t.after(() => { if (previous === undefined) delete globalThis.loadCardHelpers; else globalThis.loadCardHelpers = previous; });
}

test("embedded Lovelace action preserves tap and hold definitions and delegates interaction to the native child", async t => {
  const created = [];
  nestedHelper(t, async () => ({ createCardElement: config => { const child = new Node("native-action-card"); created.push({ config, child }); return child; } }));
  const definition = nestedAction(), original = structuredClone(definition);
  const { card, hass, calls } = setup();
  card.setConfig({ show_custom_button: true, custom_button: { mode: "card", card: definition } });
  await flush(); await flush();
  assert.equal(created.length, 1); assert.deepEqual(created[0].config, original);
  assert.deepEqual(definition, original, "the parent must not rewrite a nested Browser Mod definition");
  const child = created[0].child;
  assert.equal(child.hass, hass); assert.equal(card.shadowRoot.querySelector("native-action-card"), child);
  child.dispatchEvent({ type: "click" }); child.dispatchEvent({ type: "contextmenu" });
  assert.equal(writes(calls).length, 0, "the parent must not duplicate or replace the child's action handling");
});

test("an embedded card is reused across presentation changes and receives unrelated external states", async t => {
  let creates = 0;
  nestedHelper(t, async () => ({ createCardElement: () => { creates++; return new Node("native-action-card"); } }));
  const definition = nestedAction(), { card, hass, calls } = setup();
  card.setConfig({ show_custom_button: true, custom_button: { card: definition } });
  await flush(); await flush();
  const child = card.shadowRoot.querySelector("native-action-card"); assert.ok(child);
  const updated = { ...hass, states: { ...hass.states, "input_number.example_duration": customState("15") } };
  card.hass = updated;
  assert.equal(child.hass, updated, "nested cards have their own dependencies outside REMI's registry");
  card.setConfig({ appearance: "remi", layout: "compact", show_custom_button: true, custom_button: { card: definition } });
  await flush();
  assert.equal(creates, 1); assert.equal(card.shadowRoot.querySelector("native-action-card"), child);
  assert.equal(writes(calls).length, 0);
});

test("a late Lovelace-helper result cannot insert a former card after configuration changes", async t => {
  let finish; const created = [];
  nestedHelper(t, () => new Promise(resolve => { finish = resolve; }));
  const { card, calls } = setup();
  card.setConfig({ show_custom_button: true, custom_button: { card: nestedAction() } });
  await flush();
  assert.equal(typeof finish, "function");
  card.setConfig({ show_custom_button: true, custom_button: { mode: "entity", entity: customEntity } });
  finish({ createCardElement: config => { created.push(config); return new Node("native-action-card"); } });
  await flush(); await flush();
  assert.equal(created.length, 0); assert.equal(card.shadowRoot.querySelector("native-action-card"), undefined);
  assert.equal(writes(calls).length, 0);
});

test("a late embedded-card load does nothing after the parent disconnects", async t => {
  let finish; let creates = 0;
  nestedHelper(t, () => new Promise(resolve => { finish = resolve; }));
  const { card, calls } = setup(); card.setConfig({ show_custom_button: true, custom_button: { card: nestedAction() } });
  await flush();
  card.isConnected = false; card.disconnectedCallback();
  finish({ createCardElement: () => { creates++; return new Node("native-action-card"); } });
  await flush(); await flush();
  assert.equal(creates, 0); assert.equal(card.shadowRoot.querySelector("native-action-card"), undefined);
  assert.equal(writes(calls).length, 0);
});

test("visual-editor changes leave an advanced nested card and its hold action untouched", async () => {
  const { hass, calls } = setup(), definition = nestedAction(), original = structuredClone(definition);
  const editor = new UrbanhelloRemiCardEditor();
  editor.setConfig({ title: "Existing title", show_custom_button: true, custom_button: { mode: "card", card: definition } });
  editor.hass = hass; await flush(); let saved;
  editor.addEventListener("config-changed", event => { saved = event.detail.config; });
  visualChoice(editor, "layout", "compact").dispatchEvent({ type: "click" });
  visualChoice(editor, "appearance", "remi").dispatchEvent({ type: "click" });
  assert.deepEqual(saved.custom_button, { mode: "card", card: original });
  assert.equal(saved.layout, "compact"); assert.equal(saved.appearance, "remi"); assert.equal(saved.title, "Existing title");
  assert.equal(writes(calls).length, 0);
});

test("a replaced HA connection invalidates a pending custom action without retrying it", async () => {
  const { card, hass, calls } = setupCustom(); const originalCallWS = hass.callWS; let finish;
  hass.callWS = request => { calls.push(request); return new Promise(resolve => { finish = resolve; }); };
  const oldButton = card.shadowRoot.querySelector(".custom-button"); oldButton.dispatchEvent({ type: "click" });
  card.hass = { ...hass, callWS: originalCallWS, connection: { subscribeEvents: async () => () => {} } };
  await flush();
  oldButton.dispatchEvent({ type: "click" });
  assert.equal(writes(calls).length, 1);
  finish({}); await flush();
  assert.equal(card._message, null, "the old connection's acknowledgement is not feedback for the new connection");
  assert.equal(writes(calls).length, 1);
  card.shadowRoot.querySelector(".custom-button").dispatchEvent({ type: "click" }); await flush();
  assert.equal(writes(calls).length, 2, "only a new explicit press may send another action");
  assert.deepEqual(writes(calls)[1].target, { entity_id: customEntity });
});

test("a failed embedded-card helper shows an error and retries only on an explicit press", async t => {
  let attempts = 0;
  nestedHelper(t, async () => {
    attempts++;
    if (attempts === 1) throw new Error("Example helper unavailable");
    return { createCardElement: () => new Node("native-action-card") };
  });
  const { card, calls } = setup(); card.setConfig({ show_custom_button: true, custom_button: { card: nestedAction() } });
  await flush(); await flush();
  assert.equal(attempts, 1); assert.equal(card.shadowRoot.querySelector("native-action-card"), undefined);
  assert.match(card.shadowRoot.querySelector(".custom-card").textContent, /n’a pas pu être chargée/);
  card.hass = { ...card.hass, states: { "sensor.unrelated": customState("2") } };
  await flush(); assert.equal(attempts, 1, "normal state updates do not create a loader retry loop");
  card.shadowRoot.querySelector(".custom-card").querySelector("button").dispatchEvent({ type: "click" });
  await flush(); await flush();
  assert.equal(attempts, 2); assert.ok(card.shadowRoot.querySelector("native-action-card"));
  assert.equal(writes(calls).length, 0);
});

test("a late obsolete nested-card load cannot replace the newer child", async t => {
  const pending = [], created = [];
  nestedHelper(t, () => new Promise(resolve => pending.push(resolve)));
  const { card } = setup(); card.setConfig({ show_custom_button: true, custom_button: { card: nestedAction() } });
  await flush();
  const replacement = { type: "button", entity: "button.other_example", name: "New embedded card" };
  card.setConfig({ show_custom_button: true, custom_button: { card: replacement } }); await flush();
  assert.equal(pending.length, 2);
  const helpers = { createCardElement: config => { const child = new Node("native-action-card"); created.push({ config, child }); return child; } };
  pending[1](helpers); await flush(); await flush();
  const child = card.shadowRoot.querySelector("native-action-card"); assert.ok(child);
  pending[0](helpers); await flush(); await flush();
  assert.equal(created.length, 1); assert.deepEqual(created[0].config, replacement);
  assert.equal(card.shadowRoot.querySelector("native-action-card"), child);
});

test("embedded-card failure while receiving HA state cannot break the REMI controls", async t => {
  let attempts = 0, assignments = 0;
  nestedHelper(t, async () => ({ createCardElement: () => {
    attempts++; const child = new Node("native-action-card");
    Object.defineProperty(child, "hass", { set() { if (++assignments > 1) throw new Error("Example child error"); } });
    return child;
  } }));
  const { card, hass, calls } = setup(); card.setConfig({ show_custom_button: true, custom_button: { card: nestedAction() } });
  await flush(); await flush(); assert.ok(card.shadowRoot.querySelector("native-action-card"));
  assert.doesNotThrow(() => { card.hass = { ...hass, states: { "input_number.example_duration": customState("20") } }; });
  assert.equal(card.shadowRoot.querySelector("native-action-card"), undefined);
  assert.match(card.shadowRoot.querySelector(".custom-card").textContent, /n’a pas pu être chargée/);
  assert.ok(card.shadowRoot.querySelector(".faces"));
  await flush(); assert.equal(attempts, 1); assert.equal(writes(calls).length, 0);
});

test("the editor validates nested cards without accepting executable or unserializable configuration", () => {
  const { card } = setup(); const editor = new UrbanhelloRemiCardEditor();
  for (const definition of [null, [], {}, { type: "" }, { type: "button", callback() {} }, { type: "button", value: Infinity }]) {
    const config = { show_custom_button: true, custom_button: { mode: "card", card: definition } };
    assert.throws(() => card.setConfig(config)); assert.throws(() => editor.setConfig(config));
  }
  assert.throws(() => card.setConfig({ custom_button: { mode: "other" } }));
});

test("REMI updates and layout changes never detach an embedded card or its ancestor containers", async t => {
  let creates = 0;
  nestedHelper(t, async () => ({ createCardElement: () => { creates++; return new Node("native-action-card"); } }));
  const temperature = registryEntity("sensor", "temperature", "sensor.example_temperature");
  const { card, hass } = setup([temperature], { [temperature.entity_id]: { state: "21.7", attributes: { unit_of_measurement: "°C" } } });
  const config = { show_custom_button: true, custom_button: { card: nestedAction() } };
  card.setConfig(config); await flush(); await flush();
  const child = card.shadowRoot.querySelector("native-action-card"), slot = child.parentNode, body = slot.parentNode, haCard = body.parentNode;
  assert.equal(slot.className, "custom-card"); assert.ok(body.matches(".body")); assert.equal(haCard.tagName, "ha-card");
  const protectedNodes = new Set([child, slot, body, haCard]), movements = [];
  for (const operation of ["append", "insertBefore", "remove", "replaceChildren"]) {
    const original = Node.prototype[operation];
    t.mock.method(Node.prototype, operation, function (...nodes) {
      if (operation === "remove" && protectedNodes.has(this)) movements.push(operation);
      else if (operation === "replaceChildren" && this.children.some(node => protectedNodes.has(node))) movements.push(operation);
      else if (operation === "append" && nodes.some(node => protectedNodes.has(node))) movements.push(operation);
      else if (operation === "insertBefore" && protectedNodes.has(nodes[0])) movements.push(operation);
      return original.apply(this, nodes);
    });
  }
  card.hass = { ...hass, states: { [temperature.entity_id]: { state: "22.4", attributes: { unit_of_measurement: "°C" } } } };
  assert.equal(card.shadowRoot.querySelector(".temperature").textContent, "22.4 °C");
  card.setConfig({ ...config, appearance: "glass", layout: "compact" });
  await flush();
  assert.equal(card.shadowRoot.querySelector("native-action-card"), child);
  assert.equal(card.shadowRoot.querySelector(".custom-card"), slot);
  assert.equal(card.shadowRoot.querySelector(".body"), body);
  assert.equal(card.shadowRoot.querySelector("ha-card"), haCard);
  assert.ok(haCard.matches(".appearance-glass")); assert.ok(haCard.matches(".layout-compact"));
  for (const layout of ["full", "compact", "full"]) {
    card.setConfig({ ...config, appearance: "glass", layout }); await flush();
    assert.equal(card.shadowRoot.querySelector("native-action-card"), child);
    assert.equal(card.shadowRoot.querySelector(".custom-card"), slot);
    assert.equal(card.shadowRoot.querySelector(".body"), body);
    assert.equal(card.shadowRoot.querySelector("ha-card"), haCard);
    assert.ok(haCard.matches(`.layout-${layout}`));
  }
  assert.deepEqual(movements, [], "a native hold gesture must not be interrupted by disconnection/reconnection");
  assert.equal(creates, 1);
});

test("embedded cards receive the Lovelace context without rewriting it or their actions", async t => {
  nestedHelper(t, async () => ({ createCardElement: () => new Node("native-action-card") }));
  const { card } = setup(); const first = { config: { title: "Example dashboard" } };
  card.lovelace = first;
  card.setConfig({ show_custom_button: true, custom_button: { card: nestedAction() } });
  await flush(); await flush();
  const child = card.shadowRoot.querySelector("native-action-card");
  assert.equal(child.lovelace, first);
  const second = { config: { title: "Updated example dashboard" } }; card.lovelace = second;
  assert.equal(child.lovelace, second); assert.equal(card.shadowRoot.querySelector("native-action-card"), child);
  assert.deepEqual(second, { config: { title: "Updated example dashboard" } });
});

for (const layout of ["full", "compact"]) {
  test(`${layout} keeps both brightness scales, face controls, personal action and informational firmware access`, async () => {
    const face = registryEntity("select", "face", "select.example_expression");
    const brightness = registryEntity("number", "brightness", "number.example_nightlight");
    const faceBrightness = registryEntity("number", "face_brightness", "number.example_face_brightness");
    const online = registryEntity("binary_sensor", "online", "binary_sensor.example_online");
    const alive = registryEntity("binary_sensor", "alive", "binary_sensor.example_alive");
    const firmware = registryEntity("binary_sensor", "firmware_update", "binary_sensor.example_firmware");
    const { card, calls } = setup([face, brightness, faceBrightness, online, alive, firmware], {
      [face.entity_id]: faceState("sleepy"), [brightness.entity_id]: customState("42"),
      [faceBrightness.entity_id]: customState("8"), [online.entity_id]: customState("on"),
      [alive.entity_id]: customState("on"), [firmware.entity_id]: customState("on"),
      [customEntity]: customState("off"),
    });
    card.setConfig({ layout, show_custom_button: true, custom_button: { entity: customEntity } });
    assert.equal(card.shadowRoot.querySelector(".tabs").querySelectorAll("button").length, 4);
    assert.equal(card.shadowRoot.querySelector(".face-toggle"), undefined);
    assert.equal(card.shadowRoot.querySelector(".music").open, false);
    assert.ok(card.shadowRoot.querySelector(".connection-status"));
    const slider = label => card.shadowRoot.querySelectorAll("input").find(node => node.type === "range" && node.getAttribute("aria-label") === card.t(label));
    assert.equal(slider("brightness").getAttribute("min"), "0");
    assert.equal(slider("brightness").getAttribute("max"), "100");
    assert.equal(slider("face_brightness").getAttribute("min"), "0");
    assert.equal(slider("face_brightness").getAttribute("max"), "10");
    assert.equal(writes(calls).length, 0);
    card.shadowRoot.querySelector(".faces").querySelector("button").dispatchEvent({ type: "click" }); await flush();
    let input = slider("brightness"); input.value = "55"; input.dispatchEvent({ type: "change" }); await flush();
    input = slider("face_brightness"); input.value = "7"; input.dispatchEvent({ type: "change" }); await flush();
    card.shadowRoot.querySelector(".custom-button").dispatchEvent({ type: "click" }); await flush();
    assert.deepEqual(writes(calls).map(({ domain, service, service_data, target }) => ({ domain, service, service_data, target })), [
      { domain: "select", service: "select_option", service_data: { option: "awake" }, target: { entity_id: face.entity_id } },
      { domain: "number", service: "set_value", service_data: { value: 55 }, target: { entity_id: brightness.entity_id } },
      { domain: "number", service: "set_value", service_data: { value: 7 }, target: { entity_id: faceBrightness.entity_id } },
      { domain: "script", service: "turn_on", service_data: {}, target: { entity_id: customEntity } },
    ]);
    let moreInfo; card.addEventListener("hass-more-info", event => { moreInfo = event.detail; });
    card.shadowRoot.querySelector(".firmware-update").dispatchEvent({ type: "click" });
    assert.deepEqual(moreInfo, { entityId: firmware.entity_id });
    assert.equal(writes(calls).length, 4, "viewing firmware details must not start an update");
    card.setConfig({ layout, show_face: false, show_brightness: false, show_face_brightness: false, show_connection: false, show_custom_button: false });
    for (const selector of [".face-toggle", ".faces", ".connection-status", ".firmware-update", ".custom-button"]) assert.equal(card.shadowRoot.querySelector(selector), undefined);
    assert.equal(slider("brightness"), undefined); assert.equal(slider("face_brightness"), undefined);
    assert.equal(writes(calls).length, 4);
  });
}
