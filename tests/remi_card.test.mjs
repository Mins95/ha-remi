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
const { DOMAIN, UrbanhelloRemiCard, discoverRemiDevices, indexEntities, makeAlarmPayload, makeNapPayload, serviceRequest } = cardModule;
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
  card.hass = { ...hass, language: "en" }; assert.match(card.shadowRoot.textContent, /Night face brightness/);
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
