/* REMI companion card. No account data, external scripts or automatic writes. */
export const DOMAIN = "urbanhello_remi_unofficial";
const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const FACES = ["off", "awake", "sleepy", "semi_awake", "smiley"];
const DISPLAY_OPTIONS = [["show_face", "face"], ["show_brightness", "brightness"], ["show_face_brightness", "face_brightness"], ["show_temperature", "temperature"], ["show_connection", "connection"], ["show_music", "music"], ["show_alarms", "alarms"], ["show_sleep", "sleep"], ["show_naps", "naps"]];
const validObjectId = value => typeof value === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(value);
const TEXT = {
  en: {
    appearance: "Show on the card", connection: "Connection status", displayHelp: "Keep only the controls you use. Music starts collapsed.", invalidDisplay: "Display options must be enabled or disabled.", invalidAlarm: "This schedule is no longer available. Refresh before editing it.",
    historyPeriod: "Recorded period", previousReport: "Previous available day", nextReport: "Next available day", historyInProgress: "Recording in progress", historyStatusUnknown: "Recording status not reported", historySleepUnavailable: "No sleep estimate for this period", historyExport: "Cloud export", historyOld: "This cloud export is older or undated.", historyNote: "Estimates for the selected period, not live readings.", historySyncWait: "Requesting a new export from REMI… This takes about 12 seconds.", historyRead: "Cloud journal read", historyCooldown: "An export was requested recently. The available cloud journal was read again.", historyMismatch: "The returned journal does not match the selected period.", hideCharts: "Hide environmental charts", historyChoose: "Open the available journals", historyUndated: "Undated period",
    remi: "REMI", alarms: "Schedules", sleep: "Sleep", naps: "Timers", choose: "Choose your REMI", loading: "Loading…", unavailable: "Unavailable", unknown: "Not reported", online: "Connected", offline: "Disconnected", statusUnknown: "Connection not reported", face: "Expression", faceDisplay: "Face display", on: "On", off: "Off", awake: "Awake", sleepy: "Sleepy", semi_awake: "Half awake", smiley: "Smiling", brightness: "Display brightness", face_brightness: "Night face brightness", volume: "Volume", music: "Music", play: "Play", pause: "Pause", stop: "Stop", browse: "Choose music", more: "More controls", musicNote: "REMI does not report whether music is playing.", advanced: "More settings", clock: "Clock format", musicMode: "Playback mode", normal: "Normal", single_track: "Single track", repeat_track: "Repeat track", repeat_playlist: "Repeat playlist", nightlight: "App background color", noise: "Noise alert threshold", addAlarm: "Add a schedule", edit: "Edit", delete: "Delete", confirmDelete: "Delete this item?", cancel: "Cancel", save: "Save", name: "Name", time: "Time", enabled: "Enabled", repeat: "Repeat", once: "Once", mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun", alarmFace: "Expression at this time", music_path: "Music file on REMI", music_duration_minutes: "Music duration (minutes)", play_button_enabled: "Enable play button", musicHelp: "Advanced: use a file path already present on this REMI. Leave unchanged to keep the app setting.", emptyAlarms: "No schedules yet", refresh: "Refresh", addNap: "Add a timer profile", napNote: "Saved profiles shared with the REMI app. Start a timer using REMI’s physical button.", emptyNaps: "No saved profiles", duration_minutes: "Duration (minutes)", sleep_aid: "Sleep aid", music_path_start: "Music at the start", music_path_end: "Music at the end", volume_start: "Start volume", volume_end: "End volume", music_duration_start_minutes: "Start music duration (minutes)", music_duration_end_minutes: "End music duration (minutes)", sleep_duration: "Sleep duration", sleep_score: "Sleep score", sleep_bedtime: "Bedtime", sleep_wake_time: "Wake-up", sleep_report_timestamp: "Report date", oldReport: "Older or undated report", sleepNote: "Estimates from the latest cloud report, not live readings.", charts: "Show environmental charts", chartNote: "App clock grid, from noon to the following morning. Sample dates are not inferred.", temperature: "Temperature", noiseChart: "Noise · relative level", light: "Light detected", noHistory: "No report available", noSeries: "No series available", sent: "Command sent", saved: "Saved", deleted: "Deleted", error: "The action could not be completed", noDevices: "No REMI device found. Add the integration first.", missingDevice: "The configured REMI is not available. Choose it in the card editor.", title: "Card title", auto: "Automatic (only if one REMI)", device: "REMI device", chooseFirst: "Select a REMI in the card editor.", close: "Close", minutes: "min", libraryEmpty: "No music files found", registryError: "Cannot read the device registry", changes: "Unsaved changes", disabled: "Disabled", successRead: "Updated", pending: "Sending…"
  },
  fr: {
    appearance: "Afficher sur la carte", connection: "État de connexion", displayHelp: "Gardez les commandes utiles. La musique est repliée à l’ouverture.", invalidDisplay: "Les options d’affichage doivent être activées ou désactivées.", invalidAlarm: "Cet horaire n’est plus disponible. Actualisez avant de le modifier.",
    historyPeriod: "Période enregistrée", previousReport: "Jour disponible précédent", nextReport: "Jour disponible suivant", historyInProgress: "Enregistrement en cours", historyStatusUnknown: "État de l’enregistrement non communiqué", historySleepUnavailable: "Aucune estimation de sommeil pour cette période", historyExport: "Export cloud", historyOld: "Cet export cloud est ancien ou non daté.", historyNote: "Estimations de la période sélectionnée, et non mesures en direct.", historySyncWait: "Demande d’un nouvel export au Rémi… Comptez environ 12 secondes.", historyRead: "Journal cloud relu", historyCooldown: "Un export a été demandé récemment. Le journal cloud disponible a été relu.", historyMismatch: "Le journal reçu ne correspond pas à la période sélectionnée.", hideCharts: "Masquer les courbes de la chambre", historyChoose: "Consulter les journaux disponibles", historyUndated: "Période non datée",
    remi: "Rémi", alarms: "Horaires", sleep: "Sommeil", naps: "Minuteurs", choose: "Choisissez votre Rémi", loading: "Chargement…", unavailable: "Indisponible", unknown: "Non communiqué", online: "Connecté", offline: "Déconnecté", statusUnknown: "Connexion non communiquée", face: "Visage", faceDisplay: "Affichage du visage", on: "Allumé", off: "Éteint", awake: "Réveillé", sleepy: "Endormi", semi_awake: "À moitié éveillé", smiley: "Souriant", brightness: "Luminosité de l’affichage", face_brightness: "Luminosité du visage la nuit", volume: "Volume", music: "Musique", play: "Lire", pause: "Pause", stop: "Arrêter", browse: "Choisir une musique", more: "Autres commandes", musicNote: "Rémi ne confirme pas si la musique est en cours de lecture.", advanced: "Autres réglages", clock: "Format de l’heure", musicMode: "Mode de lecture", normal: "Normal", single_track: "Un seul morceau", repeat_track: "Répéter le morceau", repeat_playlist: "Répéter la liste", nightlight: "Couleur de fond de l’application", noise: "Seuil d’alerte sonore", addAlarm: "Ajouter un horaire", edit: "Modifier", delete: "Supprimer", confirmDelete: "Supprimer cet élément ?", cancel: "Annuler", save: "Enregistrer", name: "Nom", time: "Heure", enabled: "Activé", repeat: "Répétition", once: "Une seule fois", mon: "Lun", tue: "Mar", wed: "Mer", thu: "Jeu", fri: "Ven", sat: "Sam", sun: "Dim", alarmFace: "Visage à cette heure", music_path: "Fichier musical sur Rémi", music_duration_minutes: "Durée de la musique (minutes)", play_button_enabled: "Activer le bouton lecture", musicHelp: "Réglage avancé : indiquez le chemin d’un fichier déjà présent sur ce Rémi. Ne le modifiez pas pour conserver le réglage de l’application.", emptyAlarms: "Aucun horaire pour le moment", refresh: "Actualiser", addNap: "Ajouter un profil de minuteur", napNote: "Profils enregistrés partagés avec l’application Rémi. Démarrez un minuteur avec le bouton physique du Rémi.", emptyNaps: "Aucun profil enregistré", duration_minutes: "Durée (minutes)", sleep_aid: "Aide à l’endormissement", music_path_start: "Musique au début", music_path_end: "Musique à la fin", volume_start: "Volume au début", volume_end: "Volume à la fin", music_duration_start_minutes: "Durée de la musique au début (minutes)", music_duration_end_minutes: "Durée de la musique à la fin (minutes)", sleep_duration: "Durée de sommeil", sleep_score: "Score de sommeil", sleep_bedtime: "Coucher", sleep_wake_time: "Réveil", sleep_report_timestamp: "Date du bilan", oldReport: "Bilan ancien ou non daté", sleepNote: "Estimations du dernier bilan cloud, et non des mesures en direct.", charts: "Afficher les courbes de la chambre", chartNote: "Heures de l’application, de midi au lendemain matin. Les dates des mesures ne sont pas déduites.", temperature: "Température", noiseChart: "Bruit · niveau relatif", light: "Lumière détectée", noHistory: "Aucun bilan disponible", noSeries: "Aucune courbe disponible", sent: "Commande envoyée", saved: "Enregistré", deleted: "Supprimé", error: "L’action n’a pas pu aboutir", noDevices: "Aucun Rémi trouvé. Ajoutez d’abord l’intégration.", missingDevice: "Le Rémi configuré est indisponible. Sélectionnez-le dans l’éditeur de la carte.", title: "Titre de la carte", auto: "Automatique (si un seul Rémi)", device: "Appareil Rémi", chooseFirst: "Sélectionnez un Rémi dans l’éditeur de la carte.", close: "Fermer", minutes: "min", libraryEmpty: "Aucun fichier musical trouvé", registryError: "Impossible de lire le registre des appareils", changes: "Modifications non enregistrées", disabled: "Désactivé", successRead: "Actualisé", pending: "Envoi…"
  }
};
export const language = hass => (hass?.language || hass?.locale?.language || "en").startsWith("fr") ? "fr" : "en";
export const usable = state => !!state && !["unknown", "unavailable"].includes(state.state);

function cardConfig(config, locale = "en") {
  if (!config || typeof config !== "object" || Array.isArray(config) || DISPLAY_OPTIONS.some(([key]) => Object.hasOwn(config, key) && typeof config[key] !== "boolean")) throw new Error(TEXT[locale].invalidDisplay);
  return { ...config };
}

export function discoverRemiDevices(devices) {
  return (Array.isArray(devices) ? devices : []).flatMap(device => {
    const identifier = device.identifiers?.find(pair => pair[0] === DOMAIN && typeof pair[1] === "string" && pair[1]);
    return identifier ? [{ id: device.id, remiId: identifier[1], name: device.name_by_user || device.name || "REMI" }] : [];
  });
}

export function indexEntities(entities, device) {
  const index = new Map();
  if (!device) return index;
  const prefix = `${device.remiId}_`;
  for (const entity of entities || []) {
    if (entity.platform !== DOMAIN || entity.device_id !== device.id || entity.disabled_by || !entity.unique_id?.startsWith(prefix)) continue;
    const domain = entity.entity_id.split(".", 1)[0];
    const suffix = entity.unique_id.slice(prefix.length);
    index.set(`${domain}:${suffix}`, entity.entity_id);
  }
  return index;
}

export function serviceRequest(domain, service, data = {}, entityId, response = false) {
  const request = { type: "call_service", domain, service, service_data: data };
  if (entityId) request.target = { entity_id: entityId };
  if (response) request.return_response = true;
  return request;
}

function integer(value, min, max) {
  if (value === "" || value === null || typeof value === "boolean") throw new Error("Invalid number");
  const number = Number(value);
  if (!Number.isInteger(number) || number < min || number > max) throw new Error("Invalid number");
  return number;
}

export function makeAlarmPayload(values, remiId, eventId) {
  const result = { remi_id: remiId };
  if (eventId) result.event_id = eventId;
  for (const [key, value] of Object.entries(values)) {
    // The editor is Monday-first (1..7); the service contract uses Sunday=0.
    if (key === "repeat") result.repeat = [...new Set(value)].map(day => integer(day, 1, 7) % 7).sort((a, b) => a - b);
    else if (["brightness", "volume"].includes(key)) result[key] = integer(value, 0, 100);
    else if (key === "music_duration_minutes") result[key] = integer(value, 0, 1440);
    else if (["enabled", "play_button_enabled"].includes(key)) result[key] = !!value;
    else if (key === "face_define") { if (!FACES.includes(value)) throw new Error("Invalid face"); result[key] = value; }
    else if (key === "time") { if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) throw new Error("Invalid time"); result.time = value; }
    else if (["name", "music_path"].includes(key)) result[key] = String(value);
  }
  return result;
}

export function makeNapPayload(values, remiId, napId) {
  const result = { remi_id: remiId };
  if (napId) result.nap_id = napId;
  for (const [key, value] of Object.entries(values)) {
    if (key === "duration_minutes") result[key] = integer(value, 1, 1439);
    else if (["brightness", "volume_start", "volume_end"].includes(key)) result[key] = integer(value, 0, 100);
    else if (["music_duration_start_minutes", "music_duration_end_minutes"].includes(key)) result[key] = integer(value, 0, 1440);
    else if (key === "sleep_aid") result[key] = !!value;
    else if (key === "face") { if (!FACES.includes(value)) throw new Error("Invalid face"); result.face = value; }
    else if (["name", "music_path_start", "music_path_end"].includes(key)) result[key] = String(value);
  }
  return result;
}

// All variable text is assigned with textContent / DOM properties, never parsed as HTML.
function el(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (key === "text") node.textContent = String(value);
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "class") node.className = value;
    else if (key in node) node[key] = value;
    else node.setAttribute(key, String(value));
  }
  for (const child of children.flat()) if (child != null) node.append(typeof child === "string" ? document.createTextNode(child) : child);
  return node;
}
function svg(tag, attrs = {}, children = []) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
  children.forEach(child => node.append(child));
  return node;
}
function faceDrawing(face, miniature = false) {
  const art = svg("svg", { viewBox: miniature ? "40 48 120 85" : "0 0 200 195", class: miniature ? "face-symbol" : "face-art", "aria-hidden": "true" });
  if (!miniature) art.append(svg("path", { d: "M14 185 L21 91 Q25 7 100 7 Q175 7 179 91 L186 185 Z", fill: "currentColor", opacity: ".7" }), svg("path", { d: "M15 180 H185", stroke: "white", "stroke-width": "2", opacity: ".5" }));
  if (!FACES.includes(face) || face === "off") return art;
  const eyes = face === "sleepy" ? "M53 67 Q65 80 77 67 M123 67 Q135 80 147 67" : face === "semi_awake" ? "M53 67 H77 Q65 85 53 67 M123 67 H147 Q135 85 123 67" : "M62 64 L62 77 M138 64 L138 77";
  const stroke = miniature ? "currentColor" : "white";
  art.append(svg("path", { d: eyes, fill: "none", stroke, "stroke-width": "7", "stroke-linecap": "round", "stroke-linejoin": "round" }), svg("path", { d: face === "smiley" ? "M78 103 Q100 129 122 103" : "M85 108 Q100 120 115 108", fill: "none", stroke, "stroke-width": "6", "stroke-linecap": "round" }));
  return art;
}
const STYLE = `
:host{display:block;color:var(--primary-text-color,#193f46);font-family:var(--paper-font-body1_-_font-family,system-ui,sans-serif)}*{box-sizing:border-box}ha-card{display:block;overflow:hidden;border-radius:var(--ha-card-border-radius,24px);background:var(--ha-card-background,var(--card-background-color,#fff));border:1px solid var(--divider-color,#dfe9e9);box-shadow:var(--ha-card-box-shadow,0 5px 24px #123c4210)}.head{padding:24px 24px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}.eyebrow{font-size:11px;letter-spacing:2px;font-weight:700;color:var(--secondary-text-color,#647d82);text-transform:uppercase;margin-bottom:5px}h2{font-size:24px;line-height:1.2;letter-spacing:-.6px;margin:0}h3{font-size:16px;margin:0 0 14px}p{margin:0}button,input,select{font:inherit;color:inherit}button{cursor:pointer;border:0;border-radius:12px;background:var(--secondary-background-color,#f1f6f6);padding:11px 14px;line-height:1.25;transition:background .15s}button:hover{filter:brightness(.97)}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid var(--primary-color,#39aebb);outline-offset:2px}button:disabled,input:disabled,select:disabled{cursor:default;opacity:.45}button.primary{background:var(--primary-color,#38aab9);color:var(--text-primary-color,#fff)}button.danger{background:#b3261e;color:white}button.subtle{background:transparent;color:var(--secondary-text-color,#647d82)}.tabs{display:grid;grid-template-columns:repeat(4,1fr);padding:0 15px 14px;gap:4px;border-bottom:1px solid var(--divider-color,#e4eded)}.tabs button{background:transparent;font-size:12px;padding:10px 3px}.tabs .selected{background:color-mix(in srgb,var(--primary-color,#38aab9) 12%,transparent);color:var(--primary-color,#248897);font-weight:700}.tabicon{display:block;font-size:18px;margin-bottom:5px}.body{padding:20px 24px 24px}.hero{border-radius:22px;padding:12px 16px 0;background:linear-gradient(140deg,color-mix(in srgb,var(--primary-color,#3cabb8) 16%,var(--card-background-color,#fff)),color-mix(in srgb,var(--primary-color,#3cabb8) 5%,var(--card-background-color,#fff)));text-align:center;overflow:hidden;margin-bottom:18px}.hero-top{display:flex;justify-content:space-between;align-items:center;gap:8px}.pill{border-radius:20px;font-size:11px;background:var(--card-background-color,#fff);padding:7px 10px;white-space:nowrap}.temperature{font-size:20px;font-weight:600}.face-art{display:block;width:140px;height:137px;margin:6px auto 0;color:var(--primary-color,#39aebb)}.control{margin:18px 0}.control-title{display:flex;justify-content:space-between;gap:10px;font-size:13px;margin-bottom:10px}.value{font-weight:600;white-space:nowrap}input[type=range]{width:100%;accent-color:var(--primary-color,#38aab9);cursor:pointer;height:18px}.faces{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.faces button{display:flex;align-items:center;justify-content:center;gap:10px;padding:10px;font-size:13px;min-height:48px}.face-title{align-items:center}.current-face{margin-top:-8px}.faces .selected{outline:2px solid var(--primary-color,#38aab9);background:color-mix(in srgb,var(--primary-color,#38aab9) 10%,transparent)}.face-symbol{display:block;width:32px;height:24px;flex-shrink:0}.music{border:1px solid var(--divider-color,#e4eded);border-radius:14px;padding:14px 16px;margin-top:18px}.music summary{font-weight:600;color:var(--primary-text-color,#193f46)}.music-heading{margin-top:12px}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.spread{justify-content:space-between}.muted{color:var(--secondary-text-color,#647d82);font-size:12px;line-height:1.6}.note{margin:12px 0}.music-actions{margin:14px 0;display:flex;justify-content:center;gap:10px}.music-actions button{min-width:62px}.line{height:1px;background:var(--divider-color,#e4eded);margin:20px 0}.schedule{border:1px solid var(--divider-color,#e4eded);border-radius:16px;padding:15px;margin-bottom:10px}.clock{font-size:28px;font-weight:500;letter-spacing:-1px}.schedule-name{font-size:13px;margin-top:4px;font-weight:600}.days{display:flex;gap:5px;flex-wrap:wrap;margin:12px 0}.day{font-size:10px;padding:5px 7px;border-radius:7px;color:var(--secondary-text-color,#647d82);background:var(--secondary-background-color,#f0f4f4)}.day.active{background:color-mix(in srgb,var(--primary-color,#38aab9) 14%,transparent);color:var(--primary-color,#298593)}.toggle{appearance:none;width:41px;height:24px;border-radius:15px;background:var(--disabled-color,#bccacd);position:relative;cursor:pointer;flex-shrink:0}.toggle:before{content:'';position:absolute;top:3px;left:3px;width:18px;height:18px;background:#fff;border-radius:50%;transition:transform .15s}.toggle:checked{background:var(--primary-color,#38aab9)}.toggle:checked:before{transform:translateX(17px)}.full{width:100%;margin-top:12px}.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.stat{padding:16px;border-radius:15px;background:var(--secondary-background-color,#f2f6f6)}.stat-value{font-size:24px;font-weight:500;margin-top:9px;overflow-wrap:anywhere}.stat:last-child{grid-column:1/-1}.stat:last-child .stat-value{font-size:16px}.warning{color:var(--warning-color,#996400)}.feedback{font-size:12px;padding:12px 24px;line-height:1.5;overflow-wrap:anywhere;background:color-mix(in srgb,var(--primary-color,#38aab9) 10%,transparent)}.feedback.error{color:var(--error-color,#b3261e);background:color-mix(in srgb,var(--error-color,#b3261e) 8%,transparent)}details{border-top:1px solid var(--divider-color,#e4eded);margin-top:20px;padding-top:16px}summary{cursor:pointer;font-size:13px;color:var(--secondary-text-color,#647d82)}.field{display:block;margin:16px 0}.field-label{display:block;font-size:12px;font-weight:600;margin-bottom:7px}.field input:not([type=checkbox]),.field select,.device-select{width:100%;padding:11px 12px;background:var(--secondary-background-color,#f3f7f7);border:1px solid var(--divider-color,#dfe9e9);border-radius:10px;min-height:42px}.field input[type=checkbox]{accent-color:var(--primary-color,#38aab9)}.form-head{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:16px}.form-head h3{margin:0}.day-check{display:flex;flex-direction:column;align-items:center;gap:7px;font-size:11px}.confirm{padding:13px;border-radius:12px;background:color-mix(in srgb,var(--error-color,#b3261e) 8%,transparent);margin-top:12px}.chart{border:1px solid var(--divider-color,#e4eded);padding:14px;border-radius:14px;margin-top:14px}.chart svg{width:100%;height:auto;display:block;overflow:visible}.chart h3{font-size:12px;margin-bottom:20px}.chart-label{fill:var(--secondary-text-color,#647d82);font-size:10px}.empty{padding:28px 8px;text-align:center}.library{display:grid;gap:8px}.library button{text-align:left;overflow-wrap:anywhere}.spin{opacity:.7}.badge{font-size:10px;padding:5px 7px;background:var(--secondary-background-color,#f1f5f5);border-radius:7px}@media(max-width:380px){.head{padding:20px 16px 14px}.body{padding:18px 16px 20px}.tabs{padding-left:10px;padding-right:10px}.faces button{font-size:12px}.face-art{width:125px;height:122px}.temperature{font-size:18px}.music-actions button{min-width:54px}}
.history-navigation{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:8px;align-items:center;margin:8px 0 12px}.history-date{min-width:0;width:100%;font:inherit;font-size:12px;padding:11px 8px;border:1px solid var(--divider-color,#dfe9e9);border-radius:10px;background:var(--secondary-background-color,#f3f7f7);color:inherit}.history-status{margin:12px 0}.sleep-stats .stat:last-child{grid-column:auto}.sleep-stats .stat:last-child .stat-value{font-size:24px}.display-options{margin-top:24px}.display-option{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:12px 0;border-bottom:1px solid var(--divider-color,#e4eded);font-size:14px}.display-option input{accent-color:var(--primary-color,#38aab9);width:18px;height:18px}.display-options h3{margin-bottom:6px}
`;

export class UrbanhelloRemiCard extends (globalThis.HTMLElement || class {}) {
  constructor() {
    super();
    this.attachShadow?.({ mode: "open" });
    this._config = {}; this._tab = "remi"; this._devices = []; this._entities = []; this._registryReady = false;
    this._unsub = []; this._generation = 0; this._busy = false; this._form = null; this._message = null;
    this._details = new Map(); this._sourceStates = new Map(); this._lastFaces = new Map();
    this._history = null; this._historyId = null; this._historyDetail = null; this._historyCharts = false;
    this.shadowRoot?.addEventListener("focusout", () => queueMicrotask(() => {
      if (this._renderPending && !this._formVisible(this._form) && !this.shadowRoot.activeElement?.matches("input,select")) this._render();
    }));
  }
  static getConfigElement() { return document.createElement("urbanhello-remi-card-editor"); }
  static getStubConfig() { return { type: "custom:urbanhello-remi-card" }; }
  getCardSize() { return 9; }
  getGridOptions() { return { columns: 12, rows: 9, min_columns: 6, min_rows: 4 }; }
  setConfig(config) {
    const next = cardConfig(config, language(this._hass)), previousDevice = this._config.device_id || "", formWasVisible = this._formVisible(this._form);
    this._config = next;
    if (previousDevice !== (next.device_id || "")) this._resetContext();
    if (!this._shown("show_music")) { this._library = null; this._details.delete("remi:music"); }
    if (!this._tabVisible(this._tab)) this._tab = "remi";
    if (!formWasVisible && this._formVisible(this._form)) this._tab = this._form.kind === "alarm" ? "alarms" : "naps";
    this._render();
  }
  set hass(hass) {
    const connectionChanged = this._hass && this._hass.connection !== hass.connection;
    this._hass = hass;
    if (connectionChanged) {
      this._lastFaces.clear();
      this._unsub.splice(0).forEach(fn => fn()); this._registryReady = false; this._resetContext();
    }
    if (this.isConnected && !this._registryReady && !this._registryLoading) this._loadRegistry();
    const changed = this._sourcesChanged();
    if (changed) {
      this._renderPending = true;
      if (!this._formVisible(this._form) && !this.shadowRoot?.activeElement?.matches("input,select")) this._render();
    }
  }
  get hass() { return this._hass; }
  connectedCallback() { if (this._hass) this._loadRegistry(); }
  disconnectedCallback() { this._resetContext(); this._unsub.splice(0).forEach(fn => fn()); this._registryReady = false; }
  _resetContext() {
    this._generation++; this._form = null; this._naps = null; this._history = null; this._library = null; this._confirm = null; this._message = null;
    this._historyId = null; this._historyDetail = null; this._historyCharts = false;
    this._sourceStates.clear(); this._renderPending = true;
  }
  _sourcesChanged() {
    this._rememberFace();
    const ids = [...this._index().values()];
    let changed = this._lastLanguage !== language(this._hass) || ids.length !== this._sourceStates.size;
    this._lastLanguage = language(this._hass);
    const next = new Map();
    for (const id of ids) { const state = this._hass.states?.[id]; if (this._sourceStates.get(id) !== state) changed = true; next.set(id, state); }
    this._sourceStates = next;
    return changed;
  }
  t(key) { return TEXT[language(this._hass)][key] || key; }
  _shown(key) { return this._config[key] !== false; }
  _tabVisible(tab) { return tab === "remi" || ["alarms", "sleep", "naps"].includes(tab) && this._shown(`show_${tab}`); }
  _formVisible(context) { return !!context && ["alarm", "nap"].includes(context.kind) && this._shown(context.kind === "alarm" ? "show_alarms" : "show_naps"); }
  _switchTab(tab) {
    if (this._busy || !this._tabVisible(tab)) return;
    this._tab = tab;
    if (this._form && tab !== (this._form.kind === "alarm" ? "alarms" : "naps")) this._form = null;
    this._library = null; this._confirm = null; this._message = null; this._render();
    if (tab === "naps" && !this._naps) this._loadNaps();
    if (tab === "sleep" && !this._history) this._loadHistory();
  }
  _device() {
    if (this._config.device_id) return this._devices.find(device => device.id === this._config.device_id);
    return this._devices.length === 1 ? this._devices[0] : undefined;
  }
  _index() { return indexEntities(this._entities, this._device()); }
  _entity(domain, key) { return this._index().get(`${domain}:${key}`); }
  _state(domain, key) { return this._hass?.states?.[this._entity(domain, key)]; }
  _alarmEventId(entityId) {
    const index = this._index(), entry = [...index].find(([key, id]) => id === entityId && (key.startsWith("switch:alarm_") || key.startsWith("time:alarm_") && key.endsWith("_time")));
    if (!entry || !usable(this._hass?.states?.[entityId])) return null;
    const [key] = entry, isTime = key.startsWith("time:"), suffix = key.slice(isTime ? "time:alarm_".length : "switch:alarm_".length), logicalId = isTime ? suffix.slice(0, -"_time".length) : suffix;
    const attributes = this._hass.states[entityId].attributes || {};
    if (Object.hasOwn(attributes, "event_id")) return validObjectId(attributes.event_id) ? attributes.event_id : null;
    const timeAttributes = !isTime ? this._hass.states?.[index.get(`time:alarm_${logicalId}_time`)]?.attributes : null;
    if (timeAttributes && Object.hasOwn(timeAttributes, "event_id")) return validObjectId(timeAttributes.event_id) ? timeAttributes.event_id : null;
    return validObjectId(logicalId) ? logicalId : null;
  }
  _textState(domain, key) {
    const state = this._state(domain, key);
    if (!usable(state)) return "—";
    return this._hass.formatEntityState ? this._hass.formatEntityState(state) : `${state.state}${state.attributes?.unit_of_measurement ? ` ${state.attributes.unit_of_measurement}` : ""}`;
  }
  async _loadRegistry() {
    if (!this._hass) return;
    if (this._registryLoading) { this._registryQueued = true; return; }
    this._registryLoading = true;
    const connection = this._hass.connection;
    try {
      const [devices, entities] = await Promise.all([this._hass.callWS({ type: "config/device_registry/list" }), this._hass.callWS({ type: "config/entity_registry/list" })]);
      if (!this.isConnected || connection !== this._hass.connection) { this._registryQueued = this.isConnected; return; }
      const previousDevice = this._device()?.remiId;
      this._devices = discoverRemiDevices(devices); this._entities = entities; this._registryReady = true;
      if (previousDevice !== this._device()?.remiId) this._resetContext();
      this._sourcesChanged();
      if (!this._unsub.length && this._hass.connection?.subscribeEvents) {
        for (const event of ["device_registry_updated", "entity_registry_updated"]) {
          const unsub = await this._hass.connection.subscribeEvents(() => this._loadRegistry(), event);
          if (this.isConnected) this._unsub.push(unsub); else unsub();
        }
        if (connection.addEventListener) {
          const onReady = () => this._loadRegistry();
          connection.addEventListener("ready", onReady);
          this._unsub.push(() => connection.removeEventListener("ready", onReady));
        }
      }
    } catch (error) { this._message = { error: true, text: `${this.t("registryError")}: ${error.message || error}` }; }
    finally {
      this._registryLoading = false; if (!this._formVisible(this._form)) this._render();
      if (this._registryQueued && this.isConnected) { this._registryQueued = false; this._loadRegistry(); }
    }
  }
  _button(label, action, className = "", disabled = false) {
    return el("button", { type: "button", text: label, class: className, disabled: this._busy || disabled, onclick: action });
  }
  async _run(action, success = "sent", pending = "pending") {
    if (this._busy) return;
    const generation = this._generation;
    this._busy = true; this._pendingText = pending; this._message = null; this._render();
    try {
      const result = await action();
      if (generation === this._generation) this._message = { text: this.t(success) };
      return result;
    } catch (error) {
      if (generation === this._generation) this._message = { error: true, text: `${this.t("error")}: ${error.message || error}` };
      throw error;
    } finally { this._busy = false; this._render(); }
  }
  _call(domain, service, data = {}, entityId, response = false) {
    return this._hass.callWS(serviceRequest(domain, service, data, entityId, response));
  }
  _entityAction(domain, key, service, data = {}) {
    const option = ({ "select:face": "show_face", "number:brightness": "show_brightness", "number:face_brightness": "show_face_brightness", "number:volume": "show_music", "select:music_mode": "show_music", "media_player:music_player": "show_music" })[`${domain}:${key}`];
    if (option && !this._shown(option)) return;
    const entityId = this._entity(domain, key);
    if (!entityId) return;
    this._run(() => this._call(domain, service, data, entityId)).catch(() => {});
  }
  _rememberFace() {
    const face = this._state("select", "face")?.state, remiId = this._device()?.remiId;
    if (remiId && FACES.includes(face) && face !== "off") this._lastFaces.set(remiId, face);
  }
  _setFace(option) {
    if (this._busy || !this._shown("show_face") || !FACES.includes(this._state("select", "face")?.state) || !FACES.includes(option)) return;
    this._entityAction("select", "face", "select_option", { option });
  }
  _more(entityId) {
    if (entityId) this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }
  _render() {
    if (!this.shadowRoot || !this._hass) return;
    this._renderPending = false;
    for (const detail of this.shadowRoot.querySelectorAll("details")) if (detail.dataset.key !== "remi:music" || this._shown("show_music")) this._details.set(detail.dataset.key, detail.open);
    if (!this._tabVisible(this._tab)) this._tab = "remi";
    const device = this._device();
    const card = el("ha-card");
    card.append(el("header", { class: "head" }, [el("div", {}, [el("div", { class: "eyebrow", text: "UrbanHello" }), el("h2", { text: this._config.title || device?.name || this.t("remi") })]), el("span", { class: "badge", text: "REMI" })]));
    if (!this._registryReady || !device) {
      const message = !this._registryReady ? this.t("loading") : this._config.device_id ? this.t("missingDevice") : this._devices.length ? this.t("chooseFirst") : this.t("noDevices");
      card.append(el("div", { class: "body empty muted", text: message }));
      if (!this._registryReady && this._message?.error) card.append(this._button(this.t("refresh"), () => this._loadRegistry(), "full"));
    } else {
      const visibleTabs = [["remi", "◡"], ["alarms", "◷"], ["sleep", "☾"], ["naps", "◴"]].filter(([tab]) => this._tabVisible(tab));
      const tabs = el("nav", { class: "tabs", "aria-label": this.t("remi"), style: `grid-template-columns:repeat(${visibleTabs.length},1fr)` });
      visibleTabs.forEach(([tab, icon]) => {
        const button = this._button("", () => this._switchTab(tab), tab === this._tab ? "selected" : "");
        button.setAttribute("aria-pressed", String(tab === this._tab)); button.append(el("span", { class: "tabicon", text: icon }), document.createTextNode(this.t(tab))); tabs.append(button);
      });
      if (visibleTabs.length > 1) card.append(tabs);
      const body = el("div", { class: "body" });
      if (this._formVisible(this._form)) body.append(this._form.element);
      else if (this._library && this._shown("show_music")) body.append(this._renderLibrary());
      else if (this._tab === "remi") body.append(this._renderRemi());
      else if (this._tab === "alarms") body.append(this._renderAlarms());
      else if (this._tab === "sleep") body.append(this._renderSleep());
      else body.append(this._renderNaps());
      card.append(body);
    }
    if (this._message) card.append(el("div", { class: `feedback${this._message.error ? " error" : ""}`, role: this._message.error ? "alert" : "status", text: this._message.text }));
    if (this._busy) card.append(el("div", { class: "feedback", role: "status", text: this.t(this._pendingText || "pending") }));
    const style = el("style", { text: STYLE });
    this.shadowRoot.replaceChildren(style, card);
    for (const [index, detail] of [...this.shadowRoot.querySelectorAll("details")].entries()) {
      detail.dataset.key ||= `${this._tab}:${!!this._form}:${index}`;
      if (this._details.has(detail.dataset.key)) detail.open = this._details.get(detail.dataset.key);
    }
    if (this._busy && this._form) this._form.element.querySelectorAll("button,input,select").forEach(node => { node.disabled = true; });
    else if (this._form) this._form.element.querySelectorAll("button,input,select").forEach(node => { node.disabled = false; });
  }
  _renderRemi() {
    const fragment = document.createDocumentFragment();
    const online = this._state("binary_sensor", "online"), alive = this._state("binary_sensor", "alive");
    const status = online?.state === "off" || alive?.state === "off" ? "offline" : online?.state === "on" && alive?.state === "on" ? "online" : "statusUnknown";
    const face = this._state("select", "face")?.state;
    const knownFace = FACES.includes(face), faceOn = knownFace && face !== "off";
    this._rememberFace();
    const art = faceDrawing(face);
    const indicators = [];
    if (this._shown("show_connection")) indicators.push(el("span", { class: "pill connection-status", text: `${status === "online" ? "● " : "○ "}${this.t(status)}` }));
    if (this._shown("show_temperature")) indicators.push(el("span", { class: "temperature", text: this._textState("sensor", "temperature") }));
    fragment.append(el("div", { class: "hero" }, [...(indicators.length ? [el("div", { class: "hero-top" }, indicators)] : []), art]));
    const choices = el("div", { class: "faces" });
    ["awake", "sleepy"].forEach(value => {
      const button = this._button("", () => this._setFace(value), value === face ? "selected" : "", !knownFace);
      button.setAttribute("aria-pressed", String(value === face)); button.append(faceDrawing(value, true), document.createTextNode(this.t(value))); choices.append(button);
    });
    const toggle = el("input", { type: "checkbox", class: "toggle face-toggle", role: "switch", checked: faceOn, disabled: this._busy || !knownFace, "aria-label": this.t("faceDisplay"), onchange: event => this._setFace(event.target.checked ? this._lastFaces.get(this._device()?.remiId) || "awake" : "off") });
    const faceStatus = !knownFace ? this.t("unknown") : this.t(faceOn ? "on" : "off");
    if (this._shown("show_face")) {
      fragment.append(el("div", { class: "control" }, [el("div", { class: "control-title face-title" }, [el("span", { text: this.t("face") }), el("label", { class: "row" }, [el("span", { class: "muted", text: faceStatus }), toggle])]), choices]));
      if (faceOn && !["awake", "sleepy"].includes(face)) fragment.append(el("p", { class: "muted current-face", text: this.t(face) }));
    }
    if (this._shown("show_brightness")) fragment.append(this._slider("brightness", 0, 100, "%"));
    if (this._shown("show_face_brightness")) fragment.append(this._slider("face_brightness", 1, 10, "/10"));
    const player = this._state("media_player", "music_player"), playerId = this._entity("media_player", "music_player");
    const music = el("details", { class: "music" }, [el("summary", { text: this.t("music") }), el("div", { class: "row spread music-heading" }, [el("span", { class: "muted", text: this.t("music") }), this._button("⋯", () => { if (this._shown("show_music")) this._more(playerId); }, "subtle", !playerId)])]);
    music.dataset.key = "remi:music";
    if (player?.attributes?.media_title) music.append(el("p", { class: "muted", text: player.attributes.media_title }));
    music.append(el("div", { class: "music-actions" }, [["play", "▶"], ["pause", "Ⅱ"], ["stop", "■"]].map(([action, icon]) => { const button = this._button(icon, () => this._entityAction("media_player", "music_player", `media_${action}`), action === "play" ? "primary" : "", !playerId || player?.state === "unavailable"); button.title = this.t(action); button.setAttribute("aria-label", this.t(action)); return button; })), this._slider("volume", 0, 100, "%"), this._button(this.t("browse"), () => this._browse(), "full", !playerId || player?.state === "unavailable"), el("p", { class: "muted note", text: this.t("musicNote") }));
    if (this._shown("show_music")) fragment.append(music);
    const advanced = el("details", {}, [el("summary", { text: this.t("advanced") })]);
    advanced.dataset.key = "remi:advanced";
    if (this._shown("show_face")) advanced.append(this._selectControl("face", "face"));
    advanced.append(this._selectControl("clock_format", "clock"));
    if (this._shown("show_music")) advanced.append(this._selectControl("music_mode", "musicMode"));
    advanced.append(this._slider("noise_threshold", 0, 250, ""), this._button(this.t("nightlight"), () => this._more(this._entity("light", "background_color")), "full", !this._entity("light", "background_color")));
    fragment.append(advanced); return fragment;
  }
  _slider(key, min, max, unit) {
    const state = this._state("number", key), valid = usable(state) && Number.isFinite(Number(state.state));
    const value = el("span", { class: "value", text: valid ? `${state.state}${unit}` : "—" });
    const input = el("input", { type: "range", min, max, step: 1, value: valid ? state.state : min, disabled: this._busy || !valid, "aria-label": this.t(key), oninput: event => { value.textContent = `${event.target.value}${unit}`; }, onchange: event => this._entityAction("number", key, "set_value", { value: Number(event.target.value) }) });
    return el("div", { class: "control" }, [el("div", { class: "control-title" }, [el("span", { text: this.t(key) }), value]), input]);
  }
  _selectControl(key, label) {
    const state = this._state("select", key);
    const select = el("select", { disabled: this._busy || !usable(state), onchange: event => this._entityAction("select", key, "select_option", { option: event.target.value }), "aria-label": this.t(label) });
    (state?.attributes?.options || []).forEach(option => select.append(el("option", { value: option, text: this.t(option), selected: option === state.state })));
    return el("label", { class: "field" }, [el("span", { class: "field-label", text: this.t(label) }), select]);
  }
  _renderAlarms() {
    const fragment = document.createDocumentFragment(), alarms = [];
    for (const [key, entityId] of this._index()) if (key.startsWith("switch:alarm_")) alarms.push({ eventId: this._alarmEventId(entityId), entityId, state: this._hass.states[entityId] });
    alarms.sort((a, b) => String(a.state?.attributes?.time || "99:99").localeCompare(b.state?.attributes?.time || "99:99"));
    if (!alarms.length) fragment.append(el("p", { class: "empty muted", text: this.t("emptyAlarms") }));
    alarms.forEach(alarm => {
      const attrs = alarm.state?.attributes || {}, disabled = !usable(alarm.state) || !alarm.eventId, name = attrs.alarm_name ?? attrs.friendly_name ?? this.t("alarms");
      const toggle = el("input", { type: "checkbox", class: "toggle", checked: alarm.state?.state === "on", disabled: this._busy || disabled, "aria-label": `${this.t("enabled")} ${name}`, onchange: event => { const enabled = event.target.checked; event.target.checked = alarm.state?.state === "on"; if (!this._shown("show_alarms") || !this._alarmEventId(alarm.entityId)) return; this._run(() => this._call("switch", enabled ? "turn_on" : "turn_off", {}, alarm.entityId)).catch(() => {}); } });
      const item = el("section", { class: "schedule" }, [el("div", { class: "row spread" }, [el("div", {}, [el("div", { class: "clock", text: attrs.time || "—:—" }), el("div", { class: "schedule-name", text: name })]), toggle]), el("div", { class: "days" }, DAYS.map(day => el("span", { class: `day${attrs.recurrence?.includes(day) ? " active" : ""}`, text: this.t(day) })))]);
      if (disabled) item.append(el("p", { class: "muted", text: this.t("unavailable") }));
      item.append(el("div", { class: "row spread" }, [el("span", { class: "muted", text: attrs.face ? this.t(attrs.face) : "" }), this._button(this.t("edit"), () => this._openForm("alarm", { ...attrs, event_id: alarm.eventId, enabled: alarm.state?.state === "on" }, alarm.entityId), "subtle", disabled)]));
      fragment.append(item);
    });
    fragment.append(this._button(`+ ${this.t("addAlarm")}`, () => this._openForm("alarm"), "primary full")); return fragment;
  }
  async _loadNaps() {
    const device = this._device(); if (!device || this._busy || !this._shown("show_naps")) return;
    const generation = this._generation;
    await this._run(async () => { const result = await this._call(DOMAIN, "list_naps", { remi_id: device.remiId }, undefined, true); if (!Array.isArray(result.response?.profiles)) throw new Error(this.t("error")); if (generation === this._generation) this._naps = result.response.profiles; }, "successRead").catch(() => {});
  }
  _renderNaps() {
    const fragment = document.createDocumentFragment();
    fragment.append(el("p", { class: "muted note", text: this.t("napNote") }));
    if (!this._naps) fragment.append(this._button(this.t("refresh"), () => this._loadNaps(), "full"));
    else if (!this._naps.length) fragment.append(el("p", { class: "empty muted", text: this.t("emptyNaps") }));
    (this._naps || []).forEach(profile => fragment.append(el("section", { class: "schedule" }, [el("div", { class: "row spread" }, [el("div", {}, [el("div", { class: "clock", text: profile.duration_minutes == null ? "—" : `${profile.duration_minutes} ${this.t("minutes")}` }), el("div", { class: "schedule-name", text: profile.name || "—" })]), this._button(this.t("edit"), () => this._openForm("nap", profile), "subtle")])])));
    fragment.append(this._button(`+ ${this.t("addNap")}`, () => this._openForm("nap"), "primary full"));
    if (this._naps) fragment.append(this._button(this.t("refresh"), () => this._loadNaps(), "subtle full")); return fragment;
  }
  _openForm(kind, record = {}, alarmEntityId) {
    const device = this._device(); if (!device || this._busy || !this._formVisible({ kind })) return;
    const id = alarmEntityId ? this._alarmEventId(alarmEntityId) : record.event_id || record.nap_id;
    if (alarmEntityId && !id) return;
    const create = !id, dirty = new Set(), inputs = new Map();
    const form = el("form"), context = { kind, id, alarmEntityId, remiId: device.remiId, deviceId: device.id, generation: this._generation, element: form, dirty, inputs };
    this._form = context; this._message = null;
    form.append(el("div", { class: "form-head" }, [el("div", {}, [el("h3", { text: this.t(create ? kind === "alarm" ? "addAlarm" : "addNap" : "edit") }), el("p", { class: "muted", text: device.name })]), this._button("×", () => { this._form = null; this._render(); }, "subtle")]));
    const add = (key, type, initial, min, max, parent = form, required = false) => {
      const input = type === "face" ? el("select") : el("input", { type, ...(min != null ? { min } : {}), ...(max != null ? { max } : {}) });
      if (type === "face") { if (initial == null) input.append(el("option", { value: "", text: "—" })); FACES.forEach(face => input.append(el("option", { value: face, text: this.t(face) }))); }
      if (type === "checkbox") input.checked = !!initial; else input.value = initial ?? "";
      input.name = key; input.required = required; if (type === "number") input.step = "1"; if (type === "text") input.maxLength = 500;
      input.addEventListener("input", () => dirty.add(key)); input.addEventListener("change", () => dirty.add(key)); inputs.set(key, input);
      parent.append(el("label", { class: "field" }, [el("span", { class: "field-label", text: this.t(key === "face_define" ? "alarmFace" : key) }), input])); return input;
    };
    add("name", "text", kind === "alarm" ? record.alarm_name ?? (create ? "" : record.friendly_name) : record.name ?? "", null, null, form, true);
    if (kind === "alarm") {
      add("time", "time", record.time ?? "07:00", null, null, form, true); add("enabled", "checkbox", record.enabled ?? true);
      const days = el("div", { class: "days" });
      DAYS.forEach((day, index) => { const input = el("input", { type: "checkbox", value: String(index + 1), checked: record.recurrence?.includes(day) ?? false, onchange: () => dirty.add("repeat") }); inputs.set(`day_${index}`, input); days.append(el("label", { class: "day-check" }, [el("span", { text: this.t(day) }), input])); });
      form.append(el("div", { class: "field" }, [el("span", { class: "field-label", text: this.t("repeat") }), days]));
      add("face_define", "face", record.face ?? (create ? "awake" : null));
    } else { add("duration_minutes", "number", record.duration_minutes ?? 30, 1, 1439, form, true); add("face", "face", record.face ?? (create ? "sleepy" : null)); }
    const advanced = el("details", {}, [el("summary", { text: this.t("advanced") })]); form.append(advanced);
    add("brightness", "number", record.brightness ?? (create ? 0 : null), 0, 100, advanced);
    if (kind === "alarm") {
      add("volume", "number", record.volume ?? (create ? 50 : null), 0, 100, advanced);
      add("music_path", "text", record.music_path ?? "", null, null, advanced);
      add("music_duration_minutes", "number", record.length_min ?? (create ? 0 : null), 0, 1440, advanced);
      add("play_button_enabled", "checkbox", record.play_button_enabled ?? true, null, null, advanced);
    } else {
      add("sleep_aid", "checkbox", record.sleep_aid ?? false, null, null, advanced);
      for (const phase of ["start", "end"]) {
        add(`volume_${phase}`, "number", record[`volume_${phase}`] ?? (create ? 50 : null), 0, 100, advanced);
        add(`music_path_${phase}`, "text", record[`music_path_${phase}`] ?? "", null, null, advanced);
        add(`music_duration_${phase}_minutes`, "number", record[`music_duration_${phase}_minutes`] ?? (create ? 0 : null), 0, 1440, advanced);
      }
    }
    advanced.append(el("p", { class: "muted", text: this.t("musicHelp") }));
    form.append(el("button", { type: "submit", class: "primary full", text: this.t("save") }));
    if (!create) form.append(this._button(this.t("delete"), () => this._confirmDelete(context, form), "subtle full"));
    form.addEventListener("submit", event => {
      event.preventDefault(); if (this._busy || !this._formVisible(context) || context.generation !== this._generation || !form.reportValidity()) return;
      const values = {};
      for (const [key, input] of inputs) { if (key.startsWith("day_")) continue; if (!create && !dirty.has(key)) continue; if (input.type !== "checkbox" && input.value === "" && !["name", "music_path", "music_path_start", "music_path_end"].includes(key)) continue; values[key] = input.type === "checkbox" ? input.checked : input.value; }
      if (kind === "alarm" && (create || dirty.has("repeat"))) values.repeat = DAYS.flatMap((_, index) => inputs.get(`day_${index}`).checked ? [index + 1] : []);
      if (!create && !Object.keys(values).length) { this._form = null; this._render(); return; }
      let payload;
      try {
        const currentId = alarmEntityId ? this._alarmEventId(alarmEntityId) : id;
        if (alarmEntityId && !currentId) { this._message = { error: true, text: this.t("invalidAlarm") }; this._render(); return; }
        payload = kind === "alarm" ? makeAlarmPayload(values, context.remiId, currentId) : makeNapPayload(values, context.remiId, id);
      }
      catch (error) { this._message = { error: true, text: this.t("error") }; this._render(); return; }
      this._run(async () => { await this._call(DOMAIN, `${create ? "create" : "update"}_${kind}`, payload); if (context.generation === this._generation) { this._form = null; if (kind === "nap") this._naps = null; } }, "saved").then(() => { if (kind === "nap" && context.generation === this._generation) this._loadNaps(); }).catch(() => {});
    }); this._render();
  }
  _confirmDelete(context, form) {
    if (form.querySelector(".confirm")) return;
    const box = el("div", { class: "confirm" }, [el("p", { class: "note", text: this.t("confirmDelete") })]);
    box.append(el("div", { class: "row" }, [this._button(this.t("cancel"), () => box.remove()), this._button(this.t("delete"), () => {
      if (!this._formVisible(context) || context.generation !== this._generation) return;
      const currentId = context.alarmEntityId ? this._alarmEventId(context.alarmEntityId) : context.id;
      if (context.alarmEntityId && !currentId) { this._message = { error: true, text: this.t("invalidAlarm") }; this._render(); return; }
      const data = { remi_id: context.remiId, [context.kind === "alarm" ? "event_id" : "nap_id"]: currentId };
      this._run(async () => { await this._call(DOMAIN, `delete_${context.kind}`, data); if (context.generation === this._generation) { this._form = null; if (context.kind === "nap") this._naps = null; } }, "deleted").then(() => { if (context.kind === "nap" && context.generation === this._generation) this._loadNaps(); }).catch(() => {});
    }, "danger")])); form.append(box);
  }
  _renderSleep() {
    const fragment = document.createDocumentFragment(), logs = this._history?.logs || [];
    const report = this._selectedHistory(), index = logs.findIndex(item => item.report_id === this._historyId);
    fragment.append(el("div", { class: "row spread" }, [el("span", { class: "muted", text: this.t("historyPeriod") }), this._button(this.t("refresh"), () => this._loadHistory({ refresh: true }), "history-refresh")]));
    if (logs.length) {
      const select = el("select", { class: "history-date", "aria-label": this.t("historyPeriod"), disabled: this._busy, onchange: event => this._selectHistory(event.target.value) });
      logs.forEach(item => select.append(el("option", { value: item.report_id, selected: item.report_id === this._historyId, text: this._periodLabel(item) })));
      const previous = this._button("‹", () => this._selectHistory(logs[index + 1]?.report_id), "history-previous", index < 0 || index >= logs.length - 1);
      const next = this._button("›", () => this._selectHistory(logs[index - 1]?.report_id), "history-next", index <= 0);
      previous.setAttribute("aria-label", this.t("previousReport")); next.setAttribute("aria-label", this.t("nextReport"));
      fragment.append(el("div", { class: "history-navigation" }, [previous, select, next]));
    }
    if (!report) {
      fragment.append(el("p", { class: "empty muted", text: this.t(this._busy ? "loading" : "noHistory") }));
      if (!this._history && !this._busy) fragment.append(this._button(this.t("historyChoose"), () => this._loadHistory(), "full"));
      return fragment;
    }
    if (report.report_status !== "completed") fragment.append(el("p", { class: "history-status muted", text: this.t(report.report_status === "in_progress" ? "historyInProgress" : "historyStatusUnknown") }));
    const stats = el("div", { class: "stats sleep-stats" });
    for (const key of ["sleep_duration", "sleep_score", "sleep_bedtime", "sleep_wake_time"]) {
      const value = report[key]; let text = "—";
      if (key === "sleep_duration" && Number.isFinite(value) && value >= 0) text = `${Math.floor(value / 60)} h ${String(value % 60).padStart(2, "0")}`;
      else if (key === "sleep_score" && Number.isFinite(value) && value >= 0 && value <= 100) text = `${value}/100`;
      else if (["sleep_bedtime", "sleep_wake_time"].includes(key) && typeof value === "string" && /^([01]\d|2[0-3]):[0-5]\d$/.test(value)) text = value;
      stats.append(el("div", { class: "stat" }, [el("p", { class: "muted", text: this.t(key) }), el("div", { class: "stat-value", text })]));
    }
    fragment.append(stats);
    if (report.sleep_status === "unavailable") fragment.append(el("p", { class: "muted note", text: this.t("historySleepUnavailable") }));
    if (report.stale === true) fragment.append(el("p", { class: "muted note warning", text: this.t("historyOld") }));
    if (report.updated_at && Number.isFinite(Date.parse(report.updated_at))) fragment.append(el("p", { class: "muted note history-export", text: `${this.t("historyExport")} · ${new Date(report.updated_at).toLocaleString(language(this._hass))}` }));
    fragment.append(el("p", { class: "muted note", text: this.t("historyNote") }));
    if (this._history?.sync_status === "cooldown") fragment.append(el("p", { class: "muted note", text: this.t("historyCooldown") }));
    fragment.append(this._button(this.t(this._historyCharts ? "hideCharts" : "charts"), () => this._toggleHistoryCharts(), "full history-charts"));
    if (this._historyCharts) {
      for (const kind of ["temperature", "noise", "light"]) fragment.append(this._chart(kind, report.series?.[kind]));
      fragment.append(el("p", { class: "muted note", text: this.t("chartNote") }));
    }
    return fragment;
  }
  _periodLabel(report) {
    const format = value => {
      if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
      const date = new Date(`${value}T12:00:00Z`);
      return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value ? date.toLocaleDateString(language(this._hass), { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }) : null;
    };
    const start = format(report.period_start), end = format(report.period_end);
    return start && end ? `${start} → ${end}` : this.t("historyUndated");
  }
  _selectedHistory() {
    return this._historyDetail?.report_id === this._historyId ? this._historyDetail : this._history?.logs?.find(item => item.report_id === this._historyId);
  }
  async _readHistoryDetail(generation, remiId, reportId) {
    if (!this._shown("show_sleep") || generation !== this._generation || reportId !== this._historyId) return;
    const result = await this._call(DOMAIN, "get_history", { remi_id: remiId, limit: 1, report_id: reportId }, undefined, true);
    if (generation !== this._generation || reportId !== this._historyId) return;
    const report = result?.response?.logs?.[0];
    if (!report || report.report_id !== reportId) throw new Error(this.t("historyMismatch"));
    this._historyDetail = report;
  }
  _loadHistory({ refresh = false } = {}) {
    const device = this._device(), generation = this._generation; if (!device || this._busy || !this._shown("show_sleep")) return;
    const selectedId = this._historyId;
    return this._run(async () => {
      const data = { remi_id: device.remiId, limit: 60, include_series: false };
      if (refresh) Object.assign(data, { refresh: true, sync: true });
      const result = await this._call(DOMAIN, "get_history", data, undefined, true);
      if (generation !== this._generation || selectedId !== this._historyId) return;
      if (!Array.isArray(result?.response?.logs)) throw new Error(this.t("historyMismatch"));
      const seen = new Set(), logs = result.response.logs.filter(report => {
        if (!report || typeof report.report_id !== "string" || !report.report_id || seen.has(report.report_id)) return false;
        seen.add(report.report_id); return true;
      }).slice(0, 60);
      this._history = { ...result.response, logs };
      this._historyId = logs.some(item => item.report_id === selectedId) ? selectedId : logs[0]?.report_id || null;
      this._historyDetail = null;
      if ((refresh || this._historyCharts) && this._historyId) await this._readHistoryDetail(generation, device.remiId, this._historyId);
    }, "historyRead", refresh ? "historySyncWait" : "loading").catch(() => {});
  }
  _selectHistory(reportId) {
    if (this._busy || !this._shown("show_sleep") || !this._history?.logs?.some(item => item.report_id === reportId)) return;
    if (reportId === this._historyId) return;
    this._historyId = reportId; this._historyDetail = null; this._message = null; this._render();
    if (this._historyCharts) {
      const generation = this._generation, remiId = this._device()?.remiId;
      if (remiId) return this._run(() => this._readHistoryDetail(generation, remiId, reportId), "historyRead", "loading").catch(() => {});
    }
  }
  _toggleHistoryCharts() {
    if (this._busy || !this._shown("show_sleep") || !this._historyId || !this._device()) return;
    this._historyCharts = !this._historyCharts;
    if (!this._historyCharts) { this._render(); return; }
    const generation = this._generation, remiId = this._device().remiId, reportId = this._historyId;
    return this._run(() => this._readHistoryDetail(generation, remiId, reportId), "historyRead", "loading").catch(() => {});
  }
  _chart(kind, series) {
    const title = `${this.t(kind === "noise" ? "noiseChart" : kind)}${kind === "temperature" ? " · °C" : ""}`;
    const section = el("section", { class: "chart" }, [el("h3", { text: title })]);
    const valid = sample => sample && sample.valid !== false && Number.isInteger(sample.index) && sample.index >= 0 && sample.index < 720 && Number.isFinite(sample.value) && (kind !== "light" || Number.isFinite(sample.graph_value));
    const rawSamples = Array.isArray(series?.samples) ? series.samples : [], samples = rawSamples.filter(valid);
    if (!samples.length) { section.append(el("p", { class: "muted", text: this.t("noSeries") })); return section; }
    const value = sample => kind === "light" ? sample.graph_value : sample.value;
    const values = samples.map(value), min = kind === "light" ? 0 : Math.min(...values), max = kind === "light" ? 100 : Math.max(min + 1, ...values);
    const chart = svg("svg", { viewBox: "0 0 300 135", role: "img", "aria-label": this.t(kind === "noise" ? "noiseChart" : kind) });
    const position = sample => [32 + sample.index / 719 * 260, 103 - (value(sample) - min) / (max - min) * 92];
    chart.append(svg("line", { x1: 32, y1: 103, x2: 292, y2: 103, stroke: "var(--divider-color,#dde6e8)" }));
    const segments = []; let segment = [], previous = null;
    for (const sample of rawSamples) {
      if (!valid(sample)) { if (segment.length) segments.push(segment); segment = []; previous = null; continue; }
      if (previous !== null && sample.index !== previous + 1) { if (segment.length) segments.push(segment); segment = []; }
      segment.push(sample); previous = sample.index;
    }
    if (segment.length) segments.push(segment);
    for (const points of segments) {
      if (points.length === 1) { const [cx, cy] = position(points[0]); chart.append(svg("circle", { cx, cy, r: 2, fill: "var(--primary-color,#38aab9)" })); }
      else chart.append(svg("polyline", { points: points.map(sample => position(sample).join(",")).join(" "), fill: "none", stroke: "var(--primary-color,#38aab9)", "stroke-width": 1.8, "stroke-linejoin": "round" }));
    }
    const label = (text, x, y, anchor = "start") => { const node = svg("text", { x, y, class: "chart-label", "text-anchor": anchor }); node.textContent = String(text); chart.append(node); };
    label(kind === "light" ? "1" : max.toFixed(kind === "temperature" ? 1 : 0), 27, 14, "end"); label(kind === "light" ? "0" : min.toFixed(kind === "temperature" ? 1 : 0), 27, 105, "end"); label("12:00", 32, 126); label("00:00", 32 + 360 / 719 * 260, 126, "middle"); label("11:58", 292, 126, "end");
    section.append(chart); return section;
  }
  _browse() {
    const entityId = this._entity("media_player", "music_player"), generation = this._generation; if (!entityId || !this._shown("show_music")) return;
    this._run(async () => { const media = await this._hass.callWS({ type: "media_player/browse_media", entity_id: entityId }); if (generation === this._generation && this._shown("show_music")) this._library = { entityId, tracks: media.children || [], generation }; }, "successRead").catch(() => {});
  }
  _renderLibrary() {
    const library = this._library, fragment = document.createDocumentFragment();
    fragment.append(el("div", { class: "form-head" }, [el("h3", { text: this.t("browse") }), this._button("×", () => { this._library = null; this._render(); }, "subtle")]));
    const list = el("div", { class: "library" });
    library.tracks.filter(track => track.can_play).forEach(track => list.append(this._button(track.title, () => { if (library.generation !== this._generation || !this._shown("show_music")) return; this._run(() => this._call("media_player", "play_media", { media_content_id: track.media_content_id, media_content_type: track.media_content_type || "music" }, library.entityId)).catch(() => {}); })));
    if (!list.childNodes.length) list.append(el("p", { class: "empty muted", text: this.t("libraryEmpty") })); fragment.append(list); return fragment;
  }
}

export class UrbanhelloRemiCardEditor extends (globalThis.HTMLElement || class {}) {
  constructor() { super(); this.attachShadow?.({ mode: "open" }); this._devices = []; this._config = {}; this.shadowRoot?.addEventListener("focusout", () => queueMicrotask(() => { if (this._renderPending) this._render(); })); }
  setConfig(config) { this._config = cardConfig(config, language(this._hass)); this._render(); }
  set hass(hass) { this._hass = hass; this._render(); if (!this._loaded) { this._loaded = true; hass.callWS({ type: "config/device_registry/list" }).then(devices => { this._devices = discoverRemiDevices(devices); this._render(); }).catch(() => { this._loaded = false; }); } }
  _update(key, value) { this._config = { ...this._config, [key]: typeof value === "boolean" ? value : value || undefined }; this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true })); }
  _render() {
    if (!this.shadowRoot || !this._hass) return;
    if (this.shadowRoot.activeElement?.matches("input,select")) { this._renderPending = true; return; }
    this._renderPending = false;
    const t = key => TEXT[language(this._hass)][key], select = el("select", { class: "device-select", onchange: event => this._update("device_id", event.target.value) });
    select.append(el("option", { value: "", text: t("auto"), selected: !this._config.device_id }));
    this._devices.forEach(device => select.append(el("option", { value: device.id, text: device.name, selected: this._config.device_id === device.id })));
    const options = el("section", { class: "display-options" }, [el("h3", { text: t("appearance") }), el("p", { class: "muted note", text: t("displayHelp") })]);
    for (const [key, label] of DISPLAY_OPTIONS) {
      const input = el("input", { type: "checkbox", checked: this._config[key] !== false, "aria-label": t(label), onchange: event => this._update(key, event.target.checked) });
      input.dataset.option = key;
      options.append(el("label", { class: "display-option" }, [el("span", { text: t(label) }), input]));
    }
    this.shadowRoot.replaceChildren(el("style", { text: STYLE }), el("label", { class: "field" }, [el("span", { class: "field-label", text: t("device") }), select]), el("label", { class: "field" }, [el("span", { class: "field-label", text: t("title") }), el("input", { type: "text", value: this._config.title || "", onchange: event => this._update("title", event.target.value) })]), options);
  }
}
if (globalThis.customElements) {
  if (!customElements.get("urbanhello-remi-card")) customElements.define("urbanhello-remi-card", UrbanhelloRemiCard);
  if (!customElements.get("urbanhello-remi-card-editor")) customElements.define("urbanhello-remi-card-editor", UrbanhelloRemiCardEditor);
  globalThis.customCards = globalThis.customCards || [];
  if (!globalThis.customCards.some(card => card.type === "urbanhello-remi-card")) globalThis.customCards.push({ type: "urbanhello-remi-card", name: "REMI", description: "REMI controls, schedules and sleep · Commandes, horaires et sommeil", preview: true });
}
