import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

// Small DOM double: variable HTML parsing is deliberately forbidden, so an
// unsafe text insertion fails instead of becoming a permissive mock operation.
class Node {
  constructor(tag = "div") { this.tagName = tag; this.children = []; this.listeners = new Map(); this.dataset = {}; this.attributes = {}; this.type = ""; this.value = ""; this.checked = false; this.disabled = false; this.open = false; this.className = ""; this.isConnected = false; this._text = ""; }
  set innerHTML(_) { throw new Error("HTML parsing is forbidden"); }
  get childNodes() { return this.children; }
  get textContent() { return this._text + this.children.map(node => node.textContent).join(""); }
  set textContent(text) { this._text = String(text); this.children = []; }
  append(...nodes) { for (let node of nodes) { if (typeof node === "string") node = Object.assign(new Node("#text"), { textContent: node }); if (node.tagName === "#fragment") { this.append(...node.children); continue; } node.parentNode = this; this.children.push(node); } }
  replaceChildren(...nodes) { this.children = []; this._text = ""; this.append(...nodes); }
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter(node => node !== this); }
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
  const card = new UrbanhelloRemiCard(); card._hass = hass; card._devices = [device]; card._entities = entries; card._registryReady = true; card.isConnected = true; card._sourcesChanged(); card._render();
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
  assert.equal(ranges[1].getAttribute("min"), "1"); assert.equal(ranges[1].getAttribute("max"), "10");
  card.hass = { ...hass, language: "en" }; assert.match(card.shadowRoot.textContent, /Face brightness/);
  assert.equal(card._state("number", "face_brightness").state, "8");
});

const FACE_OPTIONS = ["off", "awake", "sleepy", "semi_awake", "smiley"];
const faceState = value => ({ state: value, attributes: { options: FACE_OPTIONS } });
function setupFace(value) {
  const entry = registryEntity("select", "face", "select.bedroom_expression");
  return { ...setup([entry], value === undefined ? {} : { [entry.entity_id]: faceState(value) }), entry };
}
function reportFace(card, entry, value) {
  card.hass = { ...card.hass, states: { ...card.hass.states, [entry.entity_id]: faceState(value) } };
}
function changeFaceToggle(card, checked) {
  const input = card.shadowRoot.querySelector(".face-toggle");
  input.checked = checked;
  input.dispatchEvent({ type: "change" });
}
function faceCommands(calls) {
  return calls.filter(call => call.type === "call_service" && call.domain === "select" && call.service === "select_option");
}
function disclosure(card, key) {
  return card.shadowRoot.querySelectorAll("details").find(node => node.dataset.key === key);
}

test("face toggle switches off then restores the last observed expression without optimistic state", async () => {
  const { card, calls, entry } = setupFace("sleepy");
  changeFaceToggle(card, false);
  await flush();
  assert.deepEqual(faceCommands(calls)[0].service_data, { option: "off" });
  assert.deepEqual(faceCommands(calls)[0].target, { entity_id: entry.entity_id });
  assert.equal(card.shadowRoot.querySelector(".face-toggle").checked, true, "a command ACK is not an observed face");
  reportFace(card, entry, "off");
  assert.equal(card.shadowRoot.querySelector(".face-toggle").checked, false);
  changeFaceToggle(card, true);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["off", "sleepy"]);
  assert.equal(card.shadowRoot.querySelector(".face-toggle").checked, false, "restoration waits for reported state too");
  reportFace(card, entry, "sleepy");
  assert.equal(card.shadowRoot.querySelector(".face-toggle").checked, true);
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
  changeFaceToggle(card, true);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["awake", "sleepy"]);
});

test("starting with an off face uses awake only after an explicit turn-on action", async () => {
  const { card, calls } = setupFace("off");
  assert.equal(faceCommands(calls).length, 0);
  assert.equal(card.shadowRoot.querySelector(".face-toggle").checked, false);
  changeFaceToggle(card, true);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["awake"]);
  assert.equal(card._state("select", "face").state, "off");
});

test("last observed expression and command target remain isolated between two REMI", async () => {
  const { card, calls, entry } = setupFace("sleepy");
  const secondDevice = { id: "device-2", remiId: "REMI2", name: "Other bedroom" };
  const secondEntry = { ...registryEntity("select", "face", "select.second_expression"), device_id: secondDevice.id, unique_id: "REMI2_face" };
  card._devices.push(secondDevice);
  card._entities.push(secondEntry);
  card.hass = { ...card.hass, states: { ...card.hass.states, [secondEntry.entity_id]: faceState("smiley") } };
  card.setConfig({ device_id: secondDevice.id });
  reportFace(card, secondEntry, "off");
  reportFace(card, entry, "off");
  changeFaceToggle(card, true);
  await flush();
  card.setConfig({ device_id: device.id });
  changeFaceToggle(card, true);
  await flush();
  assert.deepEqual(faceCommands(calls).map(call => [call.target.entity_id, call.service_data.option]), [
    [secondEntry.entity_id, "smiley"], [entry.entity_id, "sleepy"],
  ]);
});

for (const unknown of [undefined, "unknown", "unavailable", "future_face"]) {
  test(`unreported face ${String(unknown)} creates no expression or main-control command`, async () => {
    const { card, calls } = setupFace(unknown);
    const toggle = card.shadowRoot.querySelector(".face-toggle");
    const buttons = card.shadowRoot.querySelector(".faces").querySelectorAll("button");
    assert.equal(toggle.disabled, true);
    assert.equal(toggle.checked, false);
    assert.equal(buttons.length, 2);
    assert.ok(buttons.every(button => button.disabled && button.getAttribute("aria-pressed") === "false"));
    assert.match(card.shadowRoot.querySelector(".face-title").textContent, /Non communiqué/);
    assert.equal(card.shadowRoot.querySelector(".face-art").querySelectorAll("path").length, 2, "unknown data must not draw awake or sleepy eyes");
    // Even stale/programmatic UI events cannot bypass the state guard.
    changeFaceToggle(card, true);
    for (const button of buttons) button.dispatchEvent({ type: "click" });
    await flush();
    assert.equal(faceCommands(calls).length, 0);
    assert.equal(card._lastFaces.size, 0);
  });
}

for (const [lang, labels, displayLabel] of [
  ["fr", ["Réveillé", "Endormi"], "Affichage du visage"],
  ["en", ["Awake", "Sleepy"], "Face display"],
]) {
  test(`${lang}: two quick expressions and all five advanced options preserve stable state values`, () => {
    const { card } = setupFace("awake");
    card.hass = { ...card.hass, language: lang };
    const buttons = card.shadowRoot.querySelector(".faces").querySelectorAll("button");
    assert.deepEqual(buttons.map(button => button.textContent), labels);
    assert.deepEqual(buttons.map(button => button.getAttribute("aria-pressed")), ["true", "false"]);
    assert.equal(card.shadowRoot.querySelector(".face-toggle").getAttribute("aria-label"), displayLabel);
    assert.match(card.shadowRoot.querySelector(".face-title").textContent, lang === "fr" ? /Allumé/ : /On/);
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
    assert.equal(card.shadowRoot.querySelector(".face-toggle").checked, true);
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
  changeFaceToggle(card, true);
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
  changeFaceToggle(card, false);
  assert.equal(card._busy, true);
  assert.ok(card.shadowRoot.querySelector(".faces").querySelectorAll("button").every(button => button.disabled));
  card.shadowRoot.querySelector(".faces").querySelectorAll("button")[0].dispatchEvent({ type: "click" });
  changeFaceToggle(card, true);
  assert.equal(faceCommands(calls).length, 1);
  finish({});
  await flush();
  assert.equal(card._busy, false);
  assert.deepEqual(faceCommands(calls).map(call => call.service_data.option), ["off"]);
});

const historyReport = (report_id, period_end, extra = {}) => ({
  report_id, period_start: period_end === "2026-11-08" ? "2026-11-07" : "2026-11-04", period_end,
  updated_at: "2026-11-07T14:00:00Z", report_status: "completed", sleep_status: "available", stale: false,
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
    if (data?.report_id) return { response: { logs: [{ ...reports.find(report => report.report_id === data.report_id), series: { temperature: { samples: [historySample(0, 20), historySample(1, 21)] } } }] } };
    return { response: { logs: reports, ...extra } };
  };
  card._tab = "sleep"; card._render();
  return { ...context, reports, stateEntry };
}

test("opening Sleep reads a bounded catalogue without exporting or downloading chart files", async () => {
  const { card, calls, hass, stateEntry } = setupHistory(); card._tab = "remi"; card._render();
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[2].dispatchEvent({ type: "click" });
  await flush();
  assert.deepEqual(calls.map(call => call.service_data), [{ remi_id: "REMI1", limit: 60, include_series: false }]);
  assert.equal(calls[0].return_response, true);
  assert.equal(card._historyId, "recent");
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["—", "—", "—", "—"]);
  assert.match(card.shadowRoot.textContent, /Enregistrement en cours/);
  assert.doesNotMatch(card.shadowRoot.textContent, /Cet export cloud est ancien/);
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 0);
  card._render(); card.hass = { ...hass, states: { [stateEntry.entity_id]: { state: "1000", attributes: {} } } };
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[0].dispatchEvent({ type: "click" });
  card.shadowRoot.querySelector(".tabs").querySelectorAll("button")[2].dispatchEvent({ type: "click" });
  assert.equal(calls.length, 1, "render, entity updates and return to the tab must not request an export");
});

test("date selection navigates actual journals and never invents missing calendar days", async () => {
  const { card, calls } = setupHistory(); await card._loadHistory();
  assert.equal(card.shadowRoot.querySelectorAll("option").length, 2);
  assert.equal(card.shadowRoot.querySelector(".history-next").disabled, true);
  card.shadowRoot.querySelector(".history-previous").dispatchEvent({ type: "click" });
  assert.equal(card._historyId, "older");
  assert.equal(card.shadowRoot.querySelector(".history-previous").disabled, true);
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["8 h 30", "86/100", "21:15", "06:45"]);
  assert.equal(calls.length, 1, "changing an unopened chart uses catalogue metadata only");
  assert.doesNotMatch(card.shadowRoot.textContent, /999|Enregistrement en cours/);
  card.shadowRoot.querySelector(".history-next").dispatchEvent({ type: "click" });
  assert.equal(card._historyId, "recent");
  const select = card.shadowRoot.querySelector(".history-date"); select.value = "older"; select.dispatchEvent({ type: "change" });
  assert.equal(card._historyId, "older");
  card._selectHistory("missing-date"); assert.equal(card._historyId, "older");
});

test("charts and all four statistics come from the same selected detailed journal", async () => {
  const { card, hass, calls, reports } = setupHistory(); await card._loadHistory();
  hass.callWS = async request => {
    calls.push(request);
    return { response: { logs: [{ ...reports.find(report => report.report_id === request.service_data.report_id), sleep_duration: 600, sleep_score: 90, sleep_bedtime: "20:00", sleep_wake_time: "06:00", series: { noise: { samples: [historySample(0, 0), historySample(1, 7)] } } }] } };
  };
  card._selectHistory("older"); await card._toggleHistoryCharts();
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "older" });
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["10 h 00", "90/100", "20:00", "06:00"]);
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 3);
  assert.equal(card.shadowRoot.querySelectorAll("polyline").length, 1);
  await card._selectHistory("recent");
  assert.equal(card._historyCharts, true);
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "recent" });
  assert.equal(card._selectedHistory().report_id, "recent");
  await card._toggleHistoryCharts();
  assert.equal(card.shadowRoot.querySelectorAll(".chart").length, 0);
  assert.equal(calls.length, 3);
});

test("explicit Refresh requests one export, announces the wait, then reloads the selected journal", async () => {
  const { card, hass, calls, reports } = setupHistory(); await card._loadHistory(); card._selectHistory("older");
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
  assert.equal(calls.length, 2); assert.equal(card._historyId, "older");
  finish({ response: { logs: reports, sync_status: "cooldown" } }); await flush();
  assert.deepEqual(calls.at(-1).service_data, { remi_id: "REMI1", limit: 1, report_id: "older" });
  assert.equal(card._busy, false); assert.match(card.shadowRoot.textContent, /demandé récemment/);
  assert.match(card._message.text, /Journal cloud relu/);
  assert.doesNotMatch(card._message.text, /envoyé|récupéré/);
});

test("failed refresh retains the previous journal and its export date without claiming success", async () => {
  const { card, hass, calls } = setupHistory(); await card._loadHistory(); card._selectHistory("older"); await card._toggleHistoryCharts();
  const oldDetail = card._historyDetail;
  hass.callWS = async request => { calls.push(request); throw new Error("Cloud unavailable"); };
  await card._loadHistory({ refresh: true });
  assert.equal(card._historyDetail, oldDetail); assert.equal(card._historyId, "older");
  assert.equal(card._message.error, true); assert.match(card._message.text, /Cloud unavailable/);
  assert.ok(card.shadowRoot.querySelector(".history-export")); assert.equal(calls.length, 3);
});

test("a delayed catalogue cannot populate another REMI", async () => {
  const { card, hass, reports } = setupHistory(); let finish;
  hass.callWS = () => new Promise(resolve => { finish = resolve; });
  const pending = card._loadHistory(); card.setConfig({ device_id: "other" });
  finish({ response: { logs: reports } }); await pending;
  assert.equal(card._history, null); assert.equal(card._historyId, null); assert.equal(card._historyDetail, null); assert.equal(card._message, null);
});

test("a delayed chart response is ignored after the selected report changes", async () => {
  const { card, hass, reports } = setupHistory(); await card._loadHistory(); let finish;
  hass.callWS = () => new Promise(resolve => { finish = resolve; });
  const pending = card._toggleHistoryCharts(); card._historyId = "older";
  finish({ response: { logs: [{ ...reports[0], series: { temperature: { samples: [historySample(0, 21)] } } }] } }); await pending;
  assert.equal(card._historyDetail, null); assert.equal(card._selectedHistory().report_id, "older");
});

test("a mismatched detailed response cannot replace selected statistics", async () => {
  const { card, hass, reports } = setupHistory(); await card._loadHistory(); card._selectHistory("older");
  hass.callWS = async () => ({ response: { logs: [reports[0]] } }); await card._toggleHistoryCharts();
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
    assert.deepEqual(calls[0].service_data, { remi_id: "REMI1", limit: 60, include_series: false });
  });
}

test("no journal and undated metadata do not invent zero statistics or an old-report warning", async () => {
  const { card, hass } = setupHistory(); hass.callWS = async () => ({ response: { logs: [] } }); await card._loadHistory();
  assert.match(card.shadowRoot.textContent, /Aucun bilan disponible/); assert.equal(card.shadowRoot.querySelectorAll(".stat-value").length, 0);
  assert.doesNotMatch(card.shadowRoot.textContent, /ancien/);
  card._history = { logs: [{ report_id: "undated", period_start: '<img onerror="fail">', period_end: "2026-02-31", report_status: "unknown" }] }; card._historyId = "undated"; card._render();
  assert.match(card.shadowRoot.textContent, /Période non datée|non communiqué/); assert.equal(card.shadowRoot.querySelectorAll("img").length, 0);
  assert.deepEqual(card.shadowRoot.querySelectorAll(".stat-value").map(node => node.textContent), ["—", "—", "—", "—"]);
});

test("temperature chart breaks at null readings and missing indexes without drawing minus ten", () => {
  const { card } = setupHistory();
  const chart = card._chart("temperature", { samples: [historySample(0, 20), historySample(1, 21), { ...historySample(2, null), raw_value: 0 }, historySample(3, 22), historySample(4, 22), historySample(7, 23)] });
  assert.equal(chart.querySelectorAll("polyline").length, 2); assert.equal(chart.querySelectorAll("circle").length, 1);
  assert.ok(chart.querySelectorAll("polyline").every(line => line.getAttribute("points").split(" ").length === 2));
  assert.doesNotMatch(chart.textContent, /-10/); assert.match(chart.textContent, /20\.0/);
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
