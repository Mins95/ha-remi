/* Execute the shipped loader with only its browser/import boundaries mocked. */
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {test} from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../custom_components/urbanhello_remi_unofficial/www/remi-loader.js", import.meta.url), "utf8");
const CARD = "urbanhello-remi-card";
const tick = () => new Promise(resolve => setImmediate(resolve));

function fixture({failures = 0, empty = false, timeout = false, importHook, registered = false} = {}) {
  const definitions = new Map();
  const requests = [];
  const warnings = [];
  const timers = new Set();
  const existing = class ExistingCard {};
  if (registered) definitions.set(CARD, existing);
  const register = () => {
    if (!definitions.has(CARD)) definitions.set(CARD, class RemiCard {});
  };
  const state = {failures, empty};
  const context = vm.createContext({
    URL, Date, Promise, Error,
    window: {},
    customElements: {get: name => definitions.get(name)},
    console: {warn: message => warnings.push(message)},
    setTimeout(callback, ms) {
      const timer = setTimeout(() => {timers.delete(timer); callback();}, ms === 15000 ? (timeout ? 2 : 15000) : 0);
      timers.add(timer);
      return timer;
    },
    clearTimeout(timer) {timers.delete(timer); clearTimeout(timer);},
    async loadModule(url) {
      requests.push(url);
      if (importHook) return importHook(requests.length, register);
      if (state.failures-- > 0) throw new Error("simulated module failure");
      if (!state.empty) register();
    },
  });
  const execute = (query = "?v=0.5.0-beta.1&card=initial") => {
    const instrumented = source
      .replaceAll("import.meta.url", JSON.stringify("https://ha.invalid/urbanhello-remi/remi-loader.js" + query))
      .replace("import(url.href)", "loadModule(url.href)")
      .replace("export function loadRemiCard", "function loadRemiCard");
    // Separate module scope, with the same browser window for repeat imports.
    vm.runInContext("(() => {" + instrumented + "})()", context);
    return context.window.loadRemiCard;
  };
  const load = execute();
  return {load, execute, context, state, requests, warnings, definitions, existing,
    cleanup: () => {for (const timer of timers) clearTimeout(timer);}};
}

test("loader retries a failed module with unique content-versioned URLs", async t => {
  const f = fixture({failures: 1});
  t.after(f.cleanup);
  const card = await f.load();
  assert.equal(card, f.definitions.get(CARD));
  assert.equal(f.requests.length, 2);
  assert.equal(new Set(f.requests).size, 2);
  for (const request of f.requests) {
    const url = new URL(request);
    assert.equal(url.pathname, "/urbanhello-remi/remi-card.js");
    assert.equal(url.searchParams.get("v"), "0.5.0-beta.1");
    assert.equal(url.searchParams.get("card"), "initial");
    assert.ok(url.searchParams.get("load"));
  }
});

test("duplicate imports and consumers share one active load", async t => {
  let finish;
  const f = fixture({importHook: (attempt, register) => new Promise(resolve => {finish = () => {register(); resolve();};})});
  t.after(f.cleanup);
  const first = f.load();
  const secondLoader = f.execute("?v=0.5.0-beta.1&card=initial&duplicate=1");
  assert.equal(first, secondLoader());
  assert.equal(f.requests.length, 1);
  finish();
  await first;
});

test("three failures stop; only an explicit later call retries", async t => {
  const f = fixture({failures: 3});
  t.after(f.cleanup);
  await assert.rejects(f.load(), /after 3 attempts/);
  await tick();
  assert.equal(f.requests.length, 3);
  assert.equal(f.warnings.length, 1);
  await tick();
  assert.equal(f.requests.length, 3);
  await f.load();
  assert.equal(f.requests.length, 4);
  assert.equal(new Set(f.requests).size, 4);
});

test("HTTP success without a registered card is an error and can recover", async t => {
  const f = fixture({empty: true});
  t.after(f.cleanup);
  await assert.rejects(f.load(), /did not register urbanhello-remi-card/);
  assert.equal(f.requests.length, 3);
  f.state.empty = false;
  await f.load();
  assert.equal(f.requests.length, 4);
});

test("timeout retry tolerates late completion without starting another loop", async t => {
  let finishFirst;
  const f = fixture({timeout: true, importHook: (attempt, register) => {
    if (attempt === 1) return new Promise(resolve => {finishFirst = () => {register(); resolve();};});
    register();
    return Promise.resolve();
  }});
  t.after(f.cleanup);
  await f.load();
  assert.equal(f.requests.length, 2);
  finishFirst();
  await tick();
  assert.equal(f.requests.length, 2);
  assert.equal(f.warnings.length, 0);
});

test("existing cards and remounts are preserved without downloads or forced reload", async t => {
  const f = fixture({registered: true});
  t.after(f.cleanup);
  assert.equal(await f.load(), f.existing);
  assert.equal(await f.execute("?v=next&card=changed")(), f.existing);
  assert.equal(f.requests.length, 0);
  assert.equal(f.warnings.length, 0);
  assert.doesNotMatch(source, /location\s*\.\s*(reload|replace|assign)\s*\(/);
});
