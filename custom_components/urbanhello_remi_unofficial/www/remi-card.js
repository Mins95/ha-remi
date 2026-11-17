/* REMI companion card. No account data, external scripts or automatic writes. */
export const DOMAIN = "urbanhello_remi_unofficial";
const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const FACES = ["off", "awake", "sleepy", "semi_awake", "smiley"];
const CUSTOM_BUTTON_DOMAINS = ["script", "automation", "scene", "button", "input_button"];
const CUSTOM_BUTTON_FIELDS = ["entity", "name", "icon", "skip_conditions", "mode", "card"];
const DISPLAY_OPTIONS = [["show_face", "face"], ["show_brightness", "brightness"], ["show_face_brightness", "face_brightness"], ["show_temperature", "temperature"], ["show_connection", "connection"], ["show_music", "music"], ["show_alarms", "alarms"], ["show_sleep", "sleep"], ["show_naps", "naps"]];
const validObjectId = value => typeof value === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(value);
const TEXT = {
  en: {
    everyDay: "Every day", historySleepUnavailableShort: "Sleep estimate unavailable", historyLatestShort: "Latest estimate",
    faceBrightnessUnconfirmed: "The setting was not confirmed. The face has not been turned on.",
    appearanceGlass: "Dark glass",
    historyLatest: "Latest available sleep estimate", historyInfo: "About these data", historySleepUpdated: "Sleep estimate updated", historyChartKind: "Environmental chart", lightReference: "Light reference (app)", faceEvents: "Recorded face changes — not detected sleep times",
    customMode: "Action type", customModeEntity: "Existing entity", customModeCard: "Existing Lovelace card", customCardHelp: "In the YAML editor, paste the existing card configuration under custom_button.card. Its tap, hold and popup actions are preserved. Install any required custom card separately.", customCardEmpty: "Add the existing card under custom_button.card in the YAML editor.", customCardLoading: "Loading the configured card…", customCardError: "The configured card could not be loaded.",
    cardAppearance: "Appearance", appearanceTheme: "Home Assistant theme", appearanceRemi: "REMI turquoise", cardLayout: "Layout", layoutFull: "Normal", layoutCompact: "Compact", customButton: "Custom action", showCustomButton: "Show a custom action", customEntity: "Action entity", customName: "Button label", customIcon: "MDI icon", customChoose: "Choose an entity", customMissing: "Entity not found", customHelp: "Choose an existing script, automation, scene or button. This card does not create or change it.", customAutomationHelp: "Runs the actions once, even if the automation is disabled. Its conditions are checked unless you choose to skip them.", skipConditions: "Skip automation conditions", customRunning: "Script already running", customSent: "Action requested", firmwareAvailable: "Firmware update available — view details", invalidAppearance: "Choose a supported appearance and layout.", invalidCustomButton: "Check the custom action entity, label, MDI icon and options.",
    appearance: "Show on the card", connection: "Connection status", displayHelp: "Keep only the controls you use. Music starts collapsed.", invalidDisplay: "Display options must be enabled or disabled.", invalidAlarm: "This schedule is no longer available. Refresh before editing it.",
    historyPeriod: "Recorded period", previousReport: "Previous available day", nextReport: "Next available day", historyInProgress: "Recording in progress", historyStatusUnknown: "Recording status not reported", historySleepUnavailable: "No sleep estimate for this period", historyExport: "Cloud export", historyOld: "This cloud export is older or undated.", historyNote: "Estimates for the selected period, not live readings.", historySyncWait: "Requesting a new export from REMI… This takes about 12 seconds.", historyRead: "Cloud journal read", historyCooldown: "An export was requested recently. The available cloud journal was read again.", historyMismatch: "The returned journal does not match the selected period.", hideCharts: "Hide environmental charts", historyChoose: "Open the available journals", historyUndated: "Undated period",
    remi: "REMI", alarms: "Schedules", sleep: "Sleep", naps: "Timers", choose: "Choose your REMI", loading: "Loading…", unavailable: "Unavailable", unknown: "Not reported", online: "Connected", offline: "Disconnected", statusUnknown: "Connection not reported", face: "Expression", faceDisplay: "Face display", on: "On", off: "Off", awake: "Awake", sleepy: "Sleepy", semi_awake: "Half awake", smiley: "Smiling", brightness: "Nightlight brightness", face_brightness: "Face brightness", volume: "Volume", music: "Music", play: "Play", pause: "Pause", stop: "Stop", browse: "Choose music", more: "More controls", musicNote: "REMI does not report whether music is playing.", advanced: "More settings", clock: "Clock format", musicMode: "Playback mode", normal: "Normal", single_track: "Single track", repeat_track: "Repeat track", repeat_playlist: "Repeat playlist", nightlight: "App background color", noise: "Noise alert threshold", addAlarm: "Add a schedule", edit: "Edit", delete: "Delete", confirmDelete: "Delete this item?", cancel: "Cancel", save: "Save", name: "Name", time: "Time", enabled: "Enabled", repeat: "Repeat", once: "Once", mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun", alarmFace: "Expression at this time", music_path: "Music file on REMI", music_duration_minutes: "Music duration (minutes)", play_button_enabled: "Enable play button", musicHelp: "Advanced: use a file path already present on this REMI. Leave unchanged to keep the app setting.", emptyAlarms: "No schedules yet", refresh: "Refresh", addNap: "Add a timer profile", napNote: "Saved profiles shared with the REMI app. Start a timer using REMI’s physical button.", emptyNaps: "No saved profiles", duration_minutes: "Duration (minutes)", sleep_aid: "Sleep aid", music_path_start: "Music at the start", music_path_end: "Music at the end", volume_start: "Start volume", volume_end: "End volume", music_duration_start_minutes: "Start music duration (minutes)", music_duration_end_minutes: "End music duration (minutes)", sleep_duration: "Sleep duration", sleep_score: "Sleep score", sleep_bedtime: "Bedtime", sleep_wake_time: "Wake-up", sleep_report_timestamp: "Report date", oldReport: "Older or undated report", sleepNote: "Estimates from the latest cloud report, not live readings.", charts: "Show environmental charts", chartNote: "App clock grid, from noon to the following morning. Sample dates are not inferred.", temperature: "Temperature", noiseChart: "Noise · relative level", light: "Light detected", noHistory: "No report available", noSeries: "No series available", sent: "Command sent", saved: "Saved", deleted: "Deleted", error: "The action could not be completed", noDevices: "No REMI device found. Add the integration first.", missingDevice: "The configured REMI is not available. Choose it in the card editor.", title: "Card title", auto: "Automatic (only if one REMI)", device: "REMI device", chooseFirst: "Select a REMI in the card editor.", close: "Close", minutes: "min", libraryEmpty: "No music files found", registryError: "Cannot read the device registry", changes: "Unsaved changes", disabled: "Disabled", successRead: "Updated", pending: "Sending…"
  },
  fr: {
    everyDay: "Tous les jours", historySleepUnavailableShort: "Estimation indisponible", historyLatestShort: "Voir le dernier bilan",
    faceBrightnessUnconfirmed: "Le réglage n’est pas confirmé. Le visage n’a pas été rallumé.",
    appearanceGlass: "Verre sombre",
    historyLatest: "Dernier bilan de sommeil disponible", historyInfo: "Informations sur ces données", historySleepUpdated: "Bilan de sommeil mis à jour", historyChartKind: "Courbe de la chambre", lightReference: "Repère de luminosité (application)", faceEvents: "Changements de visage enregistrés — pas les heures de sommeil détectées",
    customMode: "Type d’action", customModeEntity: "Entité existante", customModeCard: "Carte Lovelace existante", customCardHelp: "Dans l’éditeur YAML, collez la configuration de votre carte sous custom_button.card. Ses appuis simples, longs et fenêtres popup sont conservés. Installez séparément les cartes personnalisées nécessaires.", customCardEmpty: "Ajoutez votre carte sous custom_button.card dans l’éditeur YAML.", customCardLoading: "Chargement de la carte configurée…", customCardError: "La carte configurée n’a pas pu être chargée.",
    cardAppearance: "Apparence", appearanceTheme: "Thème Home Assistant", appearanceRemi: "Turquoise Rémi", cardLayout: "Disposition", layoutFull: "Normale", layoutCompact: "Compacte", customButton: "Action personnalisée", showCustomButton: "Afficher une action personnalisée", customEntity: "Entité à lancer", customName: "Libellé du bouton", customIcon: "Icône MDI", customChoose: "Choisir une entité", customMissing: "Entité introuvable", customHelp: "Choisissez un script, une automatisation, une scène ou un bouton existant. La carte ne le crée pas et ne le modifie pas.", customAutomationHelp: "Lance les actions une fois, même si l’automatisation est désactivée. Ses conditions sont respectées, sauf si vous choisissez de les ignorer.", skipConditions: "Ignorer les conditions de l’automatisation", customRunning: "Script déjà en cours", customSent: "Action demandée", firmwareAvailable: "Mise à jour du firmware disponible — voir les détails", invalidAppearance: "Choisissez une apparence et une disposition proposées.", invalidCustomButton: "Vérifiez l’entité, le libellé, l’icône MDI et les options de l’action personnalisée.",
    appearance: "Afficher sur la carte", connection: "État de connexion", displayHelp: "Gardez les commandes utiles. La musique est repliée à l’ouverture.", invalidDisplay: "Les options d’affichage doivent être activées ou désactivées.", invalidAlarm: "Cet horaire n’est plus disponible. Actualisez avant de le modifier.",
    historyPeriod: "Période enregistrée", previousReport: "Jour disponible précédent", nextReport: "Jour disponible suivant", historyInProgress: "Enregistrement en cours", historyStatusUnknown: "État de l’enregistrement non communiqué", historySleepUnavailable: "Aucune estimation de sommeil pour cette période", historyExport: "Export cloud", historyOld: "Cet export cloud est ancien ou non daté.", historyNote: "Estimations de la période sélectionnée, et non mesures en direct.", historySyncWait: "Demande d’un nouvel export au Rémi… Comptez environ 12 secondes.", historyRead: "Journal cloud relu", historyCooldown: "Un export a été demandé récemment. Le journal cloud disponible a été relu.", historyMismatch: "Le journal reçu ne correspond pas à la période sélectionnée.", hideCharts: "Masquer les courbes de la chambre", historyChoose: "Consulter les journaux disponibles", historyUndated: "Période non datée",
    remi: "Rémi", alarms: "Horaires", sleep: "Sommeil", naps: "Minuteurs", choose: "Choisissez votre Rémi", loading: "Chargement…", unavailable: "Indisponible", unknown: "Non communiqué", online: "Connecté", offline: "Déconnecté", statusUnknown: "Connexion non communiquée", face: "Visage", faceDisplay: "Affichage du visage", on: "Allumé", off: "Éteint", awake: "Réveillé", sleepy: "Endormi", semi_awake: "À moitié éveillé", smiley: "Souriant", brightness: "Luminosité de la veilleuse", face_brightness: "Luminosité du visage", volume: "Volume", music: "Musique", play: "Lire", pause: "Pause", stop: "Arrêter", browse: "Choisir une musique", more: "Autres commandes", musicNote: "Rémi ne confirme pas si la musique est en cours de lecture.", advanced: "Autres réglages", clock: "Format de l’heure", musicMode: "Mode de lecture", normal: "Normal", single_track: "Un seul morceau", repeat_track: "Répéter le morceau", repeat_playlist: "Répéter la liste", nightlight: "Couleur de fond de l’application", noise: "Seuil d’alerte sonore", addAlarm: "Ajouter un horaire", edit: "Modifier", delete: "Supprimer", confirmDelete: "Supprimer cet élément ?", cancel: "Annuler", save: "Enregistrer", name: "Nom", time: "Heure", enabled: "Activé", repeat: "Répétition", once: "Une seule fois", mon: "Lun", tue: "Mar", wed: "Mer", thu: "Jeu", fri: "Ven", sat: "Sam", sun: "Dim", alarmFace: "Visage à cette heure", music_path: "Fichier musical sur Rémi", music_duration_minutes: "Durée de la musique (minutes)", play_button_enabled: "Activer le bouton lecture", musicHelp: "Réglage avancé : indiquez le chemin d’un fichier déjà présent sur ce Rémi. Ne le modifiez pas pour conserver le réglage de l’application.", emptyAlarms: "Aucun horaire pour le moment", refresh: "Actualiser", addNap: "Ajouter un profil de minuteur", napNote: "Profils enregistrés partagés avec l’application Rémi. Démarrez un minuteur avec le bouton physique du Rémi.", emptyNaps: "Aucun profil enregistré", duration_minutes: "Durée (minutes)", sleep_aid: "Aide à l’endormissement", music_path_start: "Musique au début", music_path_end: "Musique à la fin", volume_start: "Volume au début", volume_end: "Volume à la fin", music_duration_start_minutes: "Durée de la musique au début (minutes)", music_duration_end_minutes: "Durée de la musique à la fin (minutes)", sleep_duration: "Durée de sommeil", sleep_score: "Score de sommeil", sleep_bedtime: "Coucher", sleep_wake_time: "Réveil", sleep_report_timestamp: "Date du bilan", oldReport: "Bilan ancien ou non daté", sleepNote: "Estimations du dernier bilan cloud, et non des mesures en direct.", charts: "Afficher les courbes de la chambre", chartNote: "Heures de l’application, de midi au lendemain matin. Les dates des mesures ne sont pas déduites.", temperature: "Température", noiseChart: "Bruit · niveau relatif", light: "Lumière détectée", noHistory: "Aucun bilan disponible", noSeries: "Aucune courbe disponible", sent: "Commande envoyée", saved: "Enregistré", deleted: "Supprimé", error: "L’action n’a pas pu aboutir", noDevices: "Aucun Rémi trouvé. Ajoutez d’abord l’intégration.", missingDevice: "Le Rémi configuré est indisponible. Sélectionnez-le dans l’éditeur de la carte.", title: "Titre de la carte", auto: "Automatique (si un seul Rémi)", device: "Appareil Rémi", chooseFirst: "Sélectionnez un Rémi dans l’éditeur de la carte.", close: "Fermer", minutes: "min", libraryEmpty: "Aucun fichier musical trouvé", registryError: "Impossible de lire le registre des appareils", changes: "Modifications non enregistrées", disabled: "Désactivé", successRead: "Actualisé", pending: "Envoi…"
  }
};
export const language = hass => (hass?.language || hass?.locale?.language || "en").startsWith("fr") ? "fr" : "en";
export const usable = state => !!state && !["unknown", "unavailable"].includes(state.state);

function cardConfig(config, locale = "en") {
  if (!config || typeof config !== "object" || Array.isArray(config) || DISPLAY_OPTIONS.some(([key]) => Object.hasOwn(config, key) && typeof config[key] !== "boolean")) throw new Error(TEXT[locale].invalidDisplay);
  if (Object.hasOwn(config, "appearance") && !["theme", "remi", "glass"].includes(config.appearance) || Object.hasOwn(config, "layout") && !["full", "compact"].includes(config.layout)) throw new Error(TEXT[locale].invalidAppearance);
  if (Object.hasOwn(config, "show_custom_button") && typeof config.show_custom_button !== "boolean") throw new Error(TEXT[locale].invalidCustomButton);
  const next = { ...config };
  if (Object.hasOwn(config, "custom_button")) {
    const button = config.custom_button;
    if (!button || typeof button !== "object" || Array.isArray(button) || Object.keys(button).some(key => !CUSTOM_BUTTON_FIELDS.includes(key))) throw new Error(TEXT[locale].invalidCustomButton);
    for (const key of ["entity", "name", "icon"]) if (Object.hasOwn(button, key) && (typeof button[key] !== "string" || button[key].length > (key === "entity" ? 255 : 100) || /[\u0000-\u001f\u007f]/.test(button[key]))) throw new Error(TEXT[locale].invalidCustomButton);
    if (button.entity && !/^(script|automation|scene|button|input_button)\.[a-z0-9_]+$/.test(button.entity)) throw new Error(TEXT[locale].invalidCustomButton);
    if (button.icon && !/^mdi:[a-z0-9]+(?:-[a-z0-9]+)*$/.test(button.icon)) throw new Error(TEXT[locale].invalidCustomButton);
    if (Object.hasOwn(button, "skip_conditions") && typeof button.skip_conditions !== "boolean") throw new Error(TEXT[locale].invalidCustomButton);
    if (Object.hasOwn(button, "mode") && !["entity", "card"].includes(button.mode)) throw new Error(TEXT[locale].invalidCustomButton);
    next.custom_button = { ...button };
    if (Object.hasOwn(button, "card")) {
      if (!button.card || typeof button.card !== "object" || Array.isArray(button.card) || typeof button.card.type !== "string" || !button.card.type.trim()) throw new Error(TEXT[locale].invalidCustomButton);
      try { next.custom_button.card = cloneCardConfig(button.card); } catch { throw new Error(TEXT[locale].invalidCustomButton); }
    }
  }
  return next;
}

function cloneCardConfig(config) {
  return JSON.parse(JSON.stringify(config, (_, value) => {
    if (["undefined", "function", "symbol", "bigint"].includes(typeof value) || typeof value === "number" && !Number.isFinite(value)) throw new Error("Invalid card configuration");
    return value;
  }));
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
ha-card{container-type:inline-size;container-name:remi-card;color:var(--primary-text-color,#193f46)}ha-card.appearance-remi{--primary-color:#087b88;--primary-text-color:#153e46;--secondary-text-color:#42666e;--text-primary-color:#fff;--ha-card-background:#e4f6f8;--card-background-color:#f4fcfd;--secondary-background-color:#d4edf0;--divider-color:#b5dce1;--disabled-color:#94bbc1;--warning-color:#7d4800;--error-color:#a01c16}ha-card.appearance-remi .hero{background:linear-gradient(140deg,#8fdbe3,#c8eef2)}button,summary,.field select,.field input:not([type=checkbox]),.history-date{min-height:48px}summary{display:flex;align-items:center}input[type=range]{height:48px;margin:0}.toggle{width:48px;height:48px;background:transparent!important;isolation:isolate}.toggle:after{content:'';position:absolute;inset:12px 0;border-radius:20px;background:var(--disabled-color,#bccacd);z-index:-1}.toggle:before{top:15px;left:3px}.toggle:checked:after{background:var(--primary-color,#38aab9)}.toggle:checked:before{transform:translateX(24px)}.connection-indicators{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.firmware-update{display:flex;align-items:center;justify-content:center;min-width:48px;padding:8px;color:var(--warning-color,#996400);background:var(--card-background-color,#fff);border-radius:50%}.firmware-update ha-icon{width:22px;height:22px}.custom-button{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:48px;margin:12px 0;overflow-wrap:anywhere}.custom-button ha-icon{flex:0 0 24px;width:24px;height:24px}.custom-button span{min-width:0}.appearance-options,.custom-button-options{margin-top:24px}.visual-choices{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:8px}.visual-choice{display:flex;flex-direction:column;align-items:flex-start;gap:6px;text-align:left;min-height:74px;border:1px solid var(--divider-color,#dfe9e9)}.visual-choice.selected{outline:2px solid var(--primary-color,#38aab9);outline-offset:-2px}.choice-preview{display:block;width:100%;height:22px;border-radius:6px;background:var(--secondary-background-color,#f1f6f6)}.choice-preview.remi{background:linear-gradient(110deg,#087b88,#8fdbe3)}.choice-preview.full{height:28px;border:1px solid var(--divider-color,#dfe9e9)}.choice-preview.compact{height:18px;margin-bottom:10px;border:1px solid var(--divider-color,#dfe9e9)}.display-option,.day-check{min-height:48px}.custom-button-options .field{margin:12px 0}
/* Normal is the former compact layout. Both modes keep every configured control. */
.remi-overview { display: contents; }
ha-card .head { padding: 16px 16px 10px; }
ha-card h2 { font-size: 21px; overflow-wrap: anywhere; }
ha-card .eyebrow { font-size: 10px; margin-bottom: 3px; }
ha-card .body { padding: 12px 16px 16px; }
ha-card .hero { padding: 8px 12px 0; margin-bottom: 10px; border-radius: 16px; }
ha-card .hero-top { min-height: 48px; }
ha-card .face-art { width: 100px; height: 98px; margin: 0 auto; }
ha-card .temperature { font-size: 18px; }
ha-card .control { margin: 8px 0; }
ha-card .control-title { margin-bottom: 2px; font-size: 12px; align-items: center; }
ha-card .brightness-controls { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 16px; }
ha-card .faces { gap: 6px; }
ha-card .faces button { padding: 8px; font-size: 12px; }
ha-card .current-face { margin: 0; font-size: 11px; line-height: 1.3; overflow-wrap: anywhere; }
ha-card .tabs { padding: 0 10px 8px; }
ha-card .tabs button { padding: 8px 3px; }
ha-card .tabicon { font-size: 16px; margin-bottom: 2px; }
ha-card details { margin-top: 12px; padding-top: 4px; }
ha-card .music { padding: 4px 12px; }
ha-card .schedule { padding: 10px; margin-bottom: 8px; }
ha-card .clock { font-size: 24px; }
ha-card .stats { gap: 8px; }
ha-card .stat { padding: 12px; }
ha-card .stat-value { font-size: 21px; }
ha-card .feedback { padding: 10px 16px; }
ha-card .field { margin: 12px 0; }
ha-card .custom-button, ha-card .custom-card { margin: 8px 0; }

/* Compact: horizontal bands, not a scaled or clipped copy of the normal card. */
ha-card.layout-compact {
  display: grid;
  grid-template-columns: minmax(68px, 1fr) auto;
  align-items: center;
}
ha-card.layout-compact .head { padding: 8px 10px; gap: 4px; }
ha-card.layout-compact .head .badge { font-size: 8px; padding: 3px; }
ha-card.layout-compact h2 { font-size: 17px; line-height: 1.15; }
ha-card.layout-compact .eyebrow { font-size: 8px; letter-spacing: 1px; margin-bottom: 2px; }
ha-card.layout-compact .tabs {
  padding: 0 6px 0 0;
  gap: 2px;
  border-bottom: 0;
  align-self: stretch;
}
ha-card.layout-compact .tabs button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 44px;
  padding: 6px;
  font-size: 10px;
}
ha-card.layout-compact .tabicon { display: inline; margin: 0; font-size: 15px; }
ha-card.layout-compact .body { grid-column: 1 / -1; padding: 4px 10px 10px; }
ha-card.layout-compact .feedback { grid-column: 1 / -1; padding: 8px 10px; }
ha-card.layout-compact .remi-overview {
  display: grid;
  grid-template-columns: minmax(94px, .65fr) minmax(0, 1.5fr);
  align-items: center;
  gap: 8px;
}
ha-card.layout-compact .hero {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px;
  margin: 0;
  border-radius: 12px;
  overflow: visible;
}
ha-card.layout-compact .face-art { order: -1; flex: 0 0 32px; width: 32px; height: 36px; }
ha-card.layout-compact .hero-top { flex-direction: column; justify-content: center; gap: 2px; min-height: 44px; }
ha-card.layout-compact .connection-indicators { justify-content: center; gap: 2px; }
ha-card.layout-compact .pill { font-size: 9px; padding: 3px 4px; white-space: normal; }
ha-card.layout-compact .temperature { font-size: 16px; line-height: 1.2; white-space: nowrap; }
ha-card.layout-compact .firmware-update { min-width: 44px; min-height: 44px; padding: 6px; }
ha-card.layout-compact .face-controls {
  margin: 0;
}
ha-card.layout-compact .face-title {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 0 0 2px;
}
ha-card.layout-compact .face-label { font-size: 11px; }
ha-card.layout-compact .faces { gap: 4px; }
ha-card.layout-compact .faces button { min-height: 44px; gap: 3px; padding: 5px 3px; font-size: 11px; }
ha-card.layout-compact .faces .face-symbol { width: 18px; height: 18px; }
ha-card.layout-compact .current-face { font-size: 10px; }
ha-card.layout-compact .brightness-controls { gap: 0 12px; }
ha-card.layout-compact .brightness-controls .control { margin: 6px 0 0; }
ha-card.layout-compact .brightness-controls .control-title { align-items: baseline; gap: 4px; font-size: 11px; line-height: 1.25; }
ha-card.layout-compact input[type=range] { height: 44px; }
ha-card.layout-compact .remi-disclosures { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); align-items: start; gap: 6px; }
ha-card.layout-compact .remi-disclosures > details { min-width: 0; margin-top: 4px; padding: 0 8px; border: 1px solid var(--divider-color, #e4eded); border-radius: 10px; }
ha-card.layout-compact .remi-disclosures > details[open] { grid-column: 1 / -1; }
ha-card.layout-compact .remi-disclosures summary { min-height: 44px; font-size: 11px; }
ha-card.layout-compact .remi-disclosures > details[open] summary { border-bottom: 1px solid var(--divider-color, #e4eded); margin-bottom: 8px; }
ha-card.layout-compact .custom-button, ha-card.layout-compact .custom-card { margin: 6px 0; }

/* Schedules share the concise grid in both layouts, with 44px touch targets. */
ha-card.layout-compact .schedule { padding: 8px 10px; margin-bottom: 6px; border-radius: 12px; }
ha-card.layout-compact .schedule .clock { font-size: 21px; letter-spacing: -.5px; }
ha-card.layout-compact .schedule .schedule-name { font-size: 11px; margin-top: 2px; }
ha-card.layout-compact .schedule .days { margin: 4px 0 0; gap: 3px; }
ha-card.layout-compact .schedule .day { font-size: 9px; padding: 3px 5px; }
ha-card.layout-compact .schedule button { min-height: 44px; padding: 5px 9px; }
ha-card.layout-compact .schedule .row { gap: 6px; }
ha-card .schedule-alarm { display: grid; grid-template-columns: minmax(0, 1fr) 44px auto; align-items: center; gap: 0 6px; padding: 8px 10px; margin-bottom: 6px; border-radius: 12px; }
ha-card .schedule-header, ha-card .schedule-footer { display: contents; }
ha-card .schedule-heading { grid-column: 1; grid-row: 1; display: flex; align-items: baseline; gap: 8px; min-width: 0; }
ha-card .schedule-heading .clock { flex-shrink: 0; font-size: 21px; letter-spacing: -.5px; white-space: nowrap; }
ha-card .schedule-heading .schedule-name { min-width: 0; font-size: 11px; margin-top: 2px; overflow-wrap: anywhere; }
ha-card .schedule-header .toggle { grid-column: 2; grid-row: 1 / 4; margin: 0; width: 44px; height: 44px; }
ha-card .schedule-header .toggle:after { inset: 10px 0; }
ha-card .schedule-header .toggle:before { top: 13px; }
ha-card .schedule-header .toggle:checked:before { transform: translateX(20px); }
ha-card .schedule-days { grid-column: 1; grid-row: 2; margin: 4px 0 0; gap: 3px; }
ha-card .schedule-days .day { font-size: 9px; padding: 3px 5px; }
ha-card .schedule-face { grid-column: 1; grid-row: 3; font-size: 10px; line-height: 1.3; }
ha-card .schedule-footer button { grid-column: 3; grid-row: 1 / 4; min-height: 44px; padding: 5px 9px; }
ha-card .schedule-unavailable { grid-column: 1 / -1; }

/* Sleep keeps a single navigation row and the same readable density in both layouts. */
ha-card .body-sleep > .row { gap: 4px; }
ha-card .history-navigation { margin: 4px 0 6px; gap: 5px; }
ha-card .history-navigation button, ha-card .history-date { min-height: 44px; padding: 6px; font-size: 11px; }
ha-card .history-navigation button { min-width: 44px; }
ha-card .sleep-stats { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }
ha-card .sleep-stats .stat { padding: 9px; border-radius: 10px; }
ha-card .sleep-stats .stat-value, ha-card .sleep-stats .stat:last-child .stat-value { font-size: 18px; margin-top: 4px; }
ha-card .sleep-stats .muted { font-size: 10px; line-height: 1.3; }
ha-card .history-status, ha-card .body-sleep > .note { margin: 6px 0; }
ha-card .chart { padding: 10px; margin-top: 8px; }
ha-card .history-controls { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 6px; align-items: center; }
ha-card .history-toolbar { grid-column: 2; grid-row: 1; }
ha-card .history-toolbar > span { display: none; }
ha-card .history-controls .history-navigation { grid-column: 1; grid-row: 1; margin: 0; }
ha-card .history-refresh { padding: 6px; min-height: 44px; font-size: 11px; }
.history-summary { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.history-summary > .note { flex: 1; }
.history-summary > button { flex: 0 1 45%; font-size: 11px; }
.history-chart-kind { margin-top: 6px; }
ha-card .history-info { margin-top: 6px; padding-top: 0; }
ha-card .history-info > summary { min-height: 44px; font-size: 11px; }
ha-card .chart h3 { margin-bottom: 8px; }
.chart-face-note { font-size: 10px; line-height: 1.3; margin-top: 4px; }

/* The compact schedules keep only active recurrence days, beside the controls. */
ha-card.layout-compact .schedule-compact {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) 44px 44px;
  align-items: center;
  gap: 0 6px;
  padding: 2px 6px;
  margin-bottom: 4px;
  border-radius: 10px;
}
ha-card.layout-compact .schedule-compact .clock { font-size: 20px; white-space: nowrap; }
ha-card.layout-compact .schedule-summary { min-width: 0; padding: 2px 0; }
ha-card.layout-compact .schedule-summary .schedule-name { margin: 0; font-size: 12px; line-height: 1.25; overflow-wrap: anywhere; }
ha-card.layout-compact .schedule-recurrence { font-size: 10px; line-height: 1.3; overflow-wrap: anywhere; }
ha-card.layout-compact .schedule-compact .toggle { width: 44px; height: 44px; margin: 0; }
ha-card.layout-compact .schedule-compact .toggle:after { inset: 10px 0; }
ha-card.layout-compact .schedule-compact .toggle:before { top: 13px; }
ha-card.layout-compact .schedule-compact .toggle:checked:before { transform: translateX(20px); }
ha-card.layout-compact .schedule-edit { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; padding: 8px; }
ha-card.layout-compact .schedule-edit ha-icon { width: 20px; height: 20px; }
ha-card.layout-compact .schedule-add { min-height: 44px; margin-top: 2px; padding: 8px; font-size: 12px; }

/* Compact sleep puts the chart selector and its information in one toolbar. */
ha-card.layout-compact .history-controls { gap: 4px; }
ha-card.layout-compact .history-controls .history-navigation { gap: 3px; }
ha-card.layout-compact .history-refresh { display: flex; align-items: center; justify-content: center; width: 44px; padding: 8px; }
ha-card.layout-compact .history-refresh ha-icon { width: 20px; height: 20px; }
ha-card.layout-compact .history-summary { gap: 6px; min-height: 44px; }
ha-card.layout-compact .history-summary > .note { margin: 3px 0; font-size: 11px; line-height: 1.3; }
ha-card.layout-compact .history-latest { min-height: 44px; padding: 4px 6px; font-size: 11px; line-height: 1.25; }
ha-card.layout-compact .sleep-stats { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px; margin: 4px 0; }
ha-card.layout-compact .sleep-stats .stat { padding: 5px 6px; border-radius: 8px; }
ha-card.layout-compact .sleep-stats .stat-value { font-size: 16px; line-height: 1.2; margin-top: 3px; }
ha-card.layout-compact .sleep-stats .stat:last-child .stat-value { font-size: 16px; margin-top: 3px; }
ha-card.layout-compact .history-chart-tools { display: grid; grid-template-columns: minmax(0, 1fr) 44px; align-items: start; gap: 0 4px; margin-top: 4px; }
ha-card.layout-compact .history-chart-tools > .history-chart-kind, ha-card.layout-compact .history-show-charts { grid-column: 1; grid-row: 1; min-height: 44px; margin: 0; z-index: 1; }
ha-card.layout-compact .history-chart-tools .history-info { position: relative; grid-column: 2; grid-row: 1; border: 0; margin: 0; padding: 0; }
ha-card.layout-compact .history-info-toggle { display: flex; align-items: center; justify-content: center; width: 44px; min-height: 44px; padding: 8px; border-radius: 10px; background: var(--secondary-background-color, #f3f7f7); }
ha-card.layout-compact .history-info-toggle ha-icon { width: 20px; height: 20px; }
ha-card.layout-compact .history-chart-tools .history-info[open] { grid-column: 1 / -1; padding-top: 44px; }
ha-card.layout-compact .history-info[open] > .history-info-toggle { position: absolute; top: 0; right: 0; }
ha-card.layout-compact .history-info > .note { margin: 6px 0; }
ha-card.layout-compact .history-info .history-charts { min-height: 44px; padding: 8px; margin-top: 6px; }
ha-card.layout-compact .chart { padding: 6px; margin-top: 4px; border-radius: 10px; }
ha-card.layout-compact .chart-label { font-size: 12px; }

@container remi-card (max-width: 420px) {
  ha-card.layout-full .brightness-controls { grid-template-columns: 1fr; gap: 0; }
  ha-card.layout-full .hero-top { flex-wrap: wrap; }
  .connection-indicators { min-width: 0; }
  ha-card.layout-compact .head { padding: 7px 6px; }
  ha-card.layout-compact .head .badge { display: none; }
  ha-card.layout-compact .tabs button { padding: 5px 4px; gap: 3px; font-size: 10px; }
  ha-card.layout-compact .tabicon { font-size: 14px; }
  ha-card .sleep-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@container remi-card (max-width: 340px) {
  ha-card.layout-compact .remi-overview { grid-template-columns: 1fr; gap: 4px; }
  ha-card.layout-compact .hero-top { flex-direction: row; flex: 1; justify-content: space-between; }
  ha-card.layout-compact .brightness-controls { grid-template-columns: 1fr; }
  ha-card.layout-compact .sleep-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) { button, .toggle:before { transition: none; } }

:host,ha-card,.body,.hero,.control,.custom-card,.custom-card>*{min-width:0}ha-card,.custom-card,.custom-card>*{width:100%}.custom-card{margin:12px 0}.custom-card .note{padding:8px}.choice-preview.glass{background:linear-gradient(120deg,#071827,#174557)}ha-card.appearance-glass{--ha-card-background:linear-gradient(145deg,rgba(7,24,39,.88),rgba(12,35,51,.78));--card-background-color:rgba(7,24,39,.82);--secondary-background-color:rgba(118,204,220,.09);--primary-color:#78d9e8;--primary-text-color:rgba(255,255,255,.98);--secondary-text-color:#b4ccd6;--text-primary-color:#072332;--divider-color:rgba(131,213,231,.2);--disabled-color:#466472;--warning-color:#ffd18a;--error-color:#ffb4ac;background:var(--ha-card-background);border-color:rgba(131,213,231,.24);box-shadow:0 10px 28px rgba(0,0,0,.2);backdrop-filter:blur(18px) saturate(135%);-webkit-backdrop-filter:blur(18px) saturate(135%)}ha-card.layout-compact .custom-card{margin:8px 0}
`;

export class UrbanhelloRemiCard extends (globalThis.HTMLElement || class {}) {
  constructor() {
    super();
    this.attachShadow?.({ mode: "open" });
    this._config = {}; this._tab = "remi"; this._devices = []; this._entities = []; this._registryReady = false;
    this._unsub = []; this._generation = 0; this._customRevision = 0; this._busy = false; this._form = null; this._message = null;
    this._controlRevision = 0; this._controlConnection = null; this._controlUnsub = [];
    this._details = new Map(); this._sourceStates = new Map(); this._lastFaces = new Map();
    this._history = null; this._historyId = null; this._historyDetail = null; this._historyCharts = true;
    this._historyKind = "temperature"; this._historyLoadedAt = 0; this._historyAttemptedAt = 0;
    this._customCard = null; this._customCardLoading = false; this._customCardError = false; this._customCardRequest = 0;
    this.shadowRoot?.addEventListener("focusout", () => queueMicrotask(() => {
      if (this._renderPending && !this._formVisible(this._form) && !this.shadowRoot.activeElement?.matches("input,select")) this._render();
    }));
  }
  static getConfigElement() { return document.createElement("urbanhello-remi-card-editor"); }
  static getStubConfig() { return { type: "custom:urbanhello-remi-card" }; }
  getCardSize() { return this._config.layout === "compact" ? 5 : 9; }
  getGridOptions() { return { columns: 12, rows: "auto", min_columns: 6, min_rows: this._config.layout === "compact" ? 3 : 4 }; }
  setConfig(config) {
    const next = cardConfig(config, language(this._hass)), previousDevice = this._config.device_id || "", formWasVisible = this._formVisible(this._form);
    const previousButton = JSON.stringify([this._config.show_custom_button, this._config.custom_button]);
    this._config = next; this._controlRevision++; this._notifyFaceBrightnessWait();
    if (previousButton !== JSON.stringify([next.show_custom_button, next.custom_button])) { this._customRevision++; this._message = null; this._invalidateCustomCard(); }
    if (previousDevice !== (next.device_id || "")) this._resetContext();
    if (!this._shown("show_music")) { this._library = null; this._details.delete("remi:music"); }
    if (!this._tabVisible(this._tab)) this._tab = "remi";
    if (!formWasVisible && this._formVisible(this._form)) this._tab = this._form.kind === "alarm" ? "alarms" : "naps";
    this._render();
  }
  set hass(hass) {
    const connectionChanged = this._hass && this._hass.connection !== hass.connection;
    this._hass = hass;
    if (this.isConnected) this._watchControlConnection(hass.connection);
    if (connectionChanged) {
      this._lastFaces.clear();
      this._unsub.splice(0).forEach(fn => fn()); this._registryReady = false; this._resetContext();
    }
    if (this._customCard) {
      try { this._customCard.hass = hass; } catch { this._invalidateCustomCard(); this._customCardError = true; this._renderPending = true; this._render(); }
    }
    if (this.isConnected && !this._registryReady && !this._registryLoading) this._loadRegistry();
    const changed = this._sourcesChanged();
    if (changed) {
      this._renderPending = true;
      if (!this._formVisible(this._form) && !this.shadowRoot?.activeElement?.matches("input,select")) this._render();
    }
    if (this.isConnected && this._tab === "sleep" && this._history && !this._busy && this._historyNeedsRefresh()) this._loadHistory({ revalidate: true });
    this._notifyFaceBrightnessWait();
  }
  get hass() { return this._hass; }
  set lovelace(value) {
    this._lovelace = value;
    if (this._customCard) {
      try { this._customCard.lovelace = value; } catch { this._invalidateCustomCard(); this._customCardError = true; this._render(); }
    }
  }
  get lovelace() { return this._lovelace; }
  connectedCallback() { if (this._hass) { this._watchControlConnection(this._hass.connection); this._loadRegistry(); } }
  disconnectedCallback() {
    this._controlRevision++; this._notifyFaceBrightnessWait(); this._controlUnsub.splice(0).forEach(fn => fn()); this._controlConnection = null;
    this._resetContext(); this._unsub.splice(0).forEach(fn => fn()); this._registryReady = false;
  }
  _watchControlConnection(connection) {
    if (connection === this._controlConnection) return;
    this._controlUnsub.splice(0).forEach(fn => fn());
    this._controlConnection = connection; this._controlConnectionReady = connection?.connected !== false; this._controlRevision++;
    this._notifyFaceBrightnessWait();
    if (!connection?.addEventListener || !connection?.removeEventListener) return;
    for (const event of ["ready", "disconnected"]) {
      const listener = () => {
        if (connection !== this._controlConnection || !this.isConnected) return;
        this._controlRevision++; this._controlConnectionReady = event === "ready";
        this._notifyFaceBrightnessWait();
        this._render();
      };
      connection.addEventListener(event, listener);
      this._controlUnsub.push(() => connection.removeEventListener(event, listener));
    }
  }
  _resetContext() {
    this._customRevision++;
    this._invalidateCustomCard();
    this._generation++; this._form = null; this._naps = null; this._history = null; this._library = null; this._confirm = null; this._message = null;
    this._notifyFaceBrightnessWait();
    this._historyId = null; this._historyDetail = null; this._historyCharts = true;
    this._historyKind = "temperature"; this._historyLoadedAt = 0; this._historyAttemptedAt = 0;
    this._sourceStates.clear(); this._renderPending = true;
  }
  _sourcesChanged() {
    this._rememberFace();
    const ids = [...new Set([...this._index().values(), ...(this._config.show_custom_button && this._config.custom_button?.entity ? [this._config.custom_button.entity] : [])])];
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
    if (tab === "sleep" && (!this._history || this._historyNeedsRefresh())) this._loadHistory({ revalidate: !!this._history });
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
      this._notifyFaceBrightnessWait();
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
  async _run(action, success = "sent", pending = "pending", isCurrent = () => true) {
    if (this._busy) return;
    const generation = this._generation;
    this._busy = true; this._pendingText = pending; this._message = null; this._render();
    try {
      const result = await action();
      if (generation === this._generation && isCurrent()) this._message = { text: this.t(success) };
      return result;
    } catch (error) {
      if (generation === this._generation && isCurrent()) this._message = { error: true, text: `${this.t("error")}: ${error.message || error}` };
      throw error;
    } finally { this._busy = false; this._render(); }
  }
  _call(domain, service, data = {}, entityId, response = false) {
    return this._hass.callWS(serviceRequest(domain, service, data, entityId, response));
  }
  _customButtonConfig() {
    return { entity: "", name: "", icon: "mdi:play-circle-outline", skip_conditions: false, ...this._config.custom_button };
  }
  _customButtonMode() { return this._config.custom_button?.mode || (this._config.custom_button?.card ? "card" : "entity"); }
  _customButtonAvailable() {
    const config = this._customButtonConfig(), domain = config.entity.split(".")[0], state = this._hass?.states?.[config.entity];
    if (!this._config.show_custom_button || this._customButtonMode() !== "entity" || !CUSTOM_BUTTON_DOMAINS.includes(domain) || !state || state.state === "unavailable") return false;
    if (domain === "script") return state.state === "off";
    if (domain === "automation") return ["on", "off"].includes(state.state);
    return typeof state.state === "string";
  }
  _activateCustomButton(button, context) {
    const current = () => this.isConnected && context.generation === this._generation && context.revision === this._customRevision && context.connection === this._hass?.connection;
    if (this._busy || this._tab !== "remi" || this._formVisible(this._form) || this._library || this.shadowRoot.querySelector(".custom-button") !== button || !current() || !this._customButtonAvailable()) return;
    const config = this._customButtonConfig(), domain = config.entity.split(".")[0];
    const service = domain === "automation" ? "trigger" : ["button", "input_button"].includes(domain) ? "press" : "turn_on";
    const data = domain === "automation" ? { skip_condition: config.skip_conditions } : {};
    this._run(() => this._call(domain, service, data, config.entity), "customSent", "pending", current).catch(() => {});
  }
  _renderCustomButton() {
    const config = this._customButtonConfig(), label = config.name || this.t("customButton");
    const context = { generation: this._generation, revision: this._customRevision, connection: this._hass.connection };
    const button = this._button("", () => this._activateCustomButton(button, context), "custom-button primary", !this._customButtonAvailable());
    const state = this._hass.states?.[config.entity];
    button.setAttribute("aria-label", label);
    button.title = state?.state === "on" && config.entity.startsWith("script.") ? this.t("customRunning") : this._customButtonAvailable() ? label : this.t("unavailable");
    button.append(el("ha-icon", { icon: config.icon || "mdi:play-circle-outline", "aria-hidden": "true" }), el("span", { text: label }));
    return button;
  }
  _invalidateCustomCard() {
    this._customCardRequest++;
    this._customCard?.remove(); this._customCard = null; this._customCardHost = null; this._customCardLoading = false; this._customCardError = false;
  }
  async _loadCustomCard() {
    if (this._customCardLoading || this._customCard || !this.isConnected || !this._config.show_custom_button || this._customButtonMode() !== "card" || !this._config.custom_button?.card) return;
    const request = ++this._customCardRequest, revision = this._customRevision, connection = this._hass?.connection;
    const current = () => this.isConnected && request === this._customCardRequest && revision === this._customRevision && connection === this._hass?.connection && this._config.show_custom_button && this._customButtonMode() === "card";
    const config = cloneCardConfig(this._config.custom_button.card);
    this._customCardLoading = true; this._customCardError = false;
    let timeout;
    try {
      const loadHelpers = globalThis.loadCardHelpers || globalThis.window?.loadCardHelpers;
      if (typeof loadHelpers !== "function") throw new Error("Card helpers unavailable");
      const helpers = await Promise.race([loadHelpers(), new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error("Card loading timed out")), 15000); })]);
      if (!current()) return;
      const child = helpers.createCardElement(config);
      if (!child || typeof child !== "object" || typeof child.remove !== "function") throw new Error("Invalid card element");
      if (!current()) { child.remove(); return; }
      if (this._lovelace !== undefined) child.lovelace = this._lovelace;
      child.hass = this._hass;
      this._customCard = child;
    } catch {
      if (current()) this._customCardError = true;
    } finally {
      clearTimeout(timeout);
      if (current()) { this._customCardLoading = false; this._render(); }
    }
  }
  _renderCustomCard() {
    const container = el("div", { class: "custom-card" });
    // Mount in _commitRender: moving an existing child here would interrupt
    // its native hold/double-tap handlers before our new DOM is ready.
    if (this._customCard) return container;
    else if (!this._config.custom_button?.card) container.append(el("p", { class: "muted note", text: this.t("customCardEmpty") }));
    else if (this._customCardError) {
      container.append(el("p", { class: "muted note", role: "alert", text: this.t("customCardError") }), this._button(this.t("refresh"), () => { if (this.shadowRoot.querySelector(".custom-card") === container) this._loadCustomCard(); }, "subtle"));
    } else {
      container.append(el("p", { class: "muted note", role: "status", text: this.t("customCardLoading") }));
      // Do not run user card creation while constructing our own DOM.
      queueMicrotask(() => this._loadCustomCard());
    }
    return container;
  }
  _commitRender(style, card) {
    const nextSlot = card.querySelector(".custom-card"), oldSlot = this._customCardHost;
    const oldCard = this.shadowRoot.querySelector("ha-card"), oldBody = oldSlot?.parentNode, nextBody = nextSlot?.parentNode;
    if (this._customCard && nextSlot && oldSlot && this._customCard.parentNode === oldSlot && oldBody?.parentNode === oldCard && oldCard?.parentNode === this.shadowRoot) {
      // Preserve the connected native card and all its ancestors. Only replace
      // surrounding REMI content; no event interception or ll-custom replay.
      const replaceAround = (parent, source, kept, marker) => {
        for (const child of [...parent.childNodes]) if (child !== kept) child.remove();
        let before = true;
        for (const child of [...source.childNodes]) {
          if (child === marker) { before = false; continue; }
          if (before) parent.insertBefore(child, kept); else parent.append(child);
        }
      };
      oldCard.setAttribute("class", card.className);
      replaceAround(oldBody, nextBody, oldSlot, nextSlot);
      replaceAround(oldCard, card, oldBody, nextBody);
      return;
    }
    this.shadowRoot.replaceChildren(style, card);
    this._customCardHost = nextSlot;
    if (nextSlot && this._customCard) nextSlot.append(this._customCard);
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
  _faceBrightnessState() {
    const face = this._state("select", "face")?.state, state = this._state("number", "face_brightness");
    const number = usable(state) && ["string", "number"].includes(typeof state.state) ? Number(state.state) : NaN;
    const knownFace = FACES.includes(face), knownNumber = Number.isInteger(number) && number >= 1 && number <= 10;
    const offline = ["online", "alive"].some(key => this._state("binary_sensor", key)?.state === "off");
    return {
      face, number: knownNumber ? number : null,
      value: face === "off" ? 0 : knownFace && knownNumber ? number : null,
      available: knownFace && knownNumber && !offline && this._controlConnectionReady !== false,
    };
  }
  _faceBrightnessContext() {
    const device = this._device();
    return {
      generation: this._generation, revision: this._controlRevision, connection: this._hass?.connection,
      remiId: device?.remiId, deviceId: device?.id,
      faceId: this._entity("select", "face"), numberId: this._entity("number", "face_brightness"),
    };
  }
  _faceBrightnessContextCurrent(context) {
    const device = this._device();
    return this.isConnected && this._shown("show_face_brightness") && this._tab === "remi" && !this._formVisible(this._form) && !this._library &&
      this._controlConnectionReady !== false && context.generation === this._generation && context.revision === this._controlRevision &&
      context.connection === this._hass?.connection && context.remiId === device?.remiId && context.deviceId === device?.id &&
      !!context.faceId && !!context.numberId && context.faceId === this._entity("select", "face") && context.numberId === this._entity("number", "face_brightness");
  }
  _notifyFaceBrightnessWait() { this._faceBrightnessWait?.check(); }
  _waitFaceBrightnessConfirmation(context, target) {
    return new Promise(resolve => {
      const waiter = {};
      const finish = result => {
        clearTimeout(waiter.timer);
        if (this._faceBrightnessWait === waiter) this._faceBrightnessWait = null;
        resolve(result);
      };
      waiter.check = () => {
        if (!this._faceBrightnessContextCurrent(context)) { finish("stale"); return; }
        const state = this._faceBrightnessState();
        if (!state.available) { finish("unconfirmed"); return; }
        if (state.face !== "off") { finish("changed"); return; }
        if (state.number === target) finish("confirmed");
      };
      // HA may deliver its state update to the card after the service response.
      // Wait for that observation, without polling or replaying either command.
      waiter.timer = setTimeout(() => finish("unconfirmed"), 5000);
      this._faceBrightnessWait = waiter;
      waiter.check();
    });
  }
  _setFaceBrightness(value, context, input) {
    if (this._busy || !/^(?:[0-9]|10)$/.test(String(value)) || !["string", "number"].includes(typeof value) ||
      !this._faceBrightnessContextCurrent(context) || this.shadowRoot.querySelector(".face-brightness-slider") !== input) return;
    const target = Number(value), initial = this._faceBrightnessState();
    if (!initial.available || target === 0 && initial.face === "off") { this._render(); return; }
    const remembered = this._lastFaces.get(context.remiId), restore = FACES.includes(remembered) && remembered !== "off" ? remembered : "awake";
    const current = () => this._faceBrightnessContextCurrent(context);
    this._run(async () => {
      if (target === 0) {
        await this._call("select", "select_option", { option: "off" }, context.faceId);
        return;
      }
      // Zero belongs to this composite control, never to the native 1..10 number.
      await this._call("number", "set_value", { value: target }, context.numberId);
      if (!current() || initial.face !== "off") return;
      const confirmation = await this._waitFaceBrightnessConfirmation(context, target);
      if (!current() || ["stale", "changed"].includes(confirmation)) return;
      const confirmed = this._faceBrightnessState();
      if (confirmation !== "confirmed" || !confirmed.available || confirmed.number !== target) throw new Error(this.t("faceBrightnessUnconfirmed"));
      // A different expression observed meanwhile belongs to the other actor.
      if (confirmed.face === "off") await this._call("select", "select_option", { option: restore }, context.faceId);
    }, "sent", "pending", current).catch(() => {});
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
    const card = el("ha-card", { class: `appearance-${this._config.appearance || "theme"} layout-${this._config.layout || "full"}` });
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
      const body = el("div", { class: `body body-${this._tab}` });
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
    this._commitRender(style, card);
    for (const [index, detail] of [...this.shadowRoot.querySelectorAll("details")].entries()) {
      detail.dataset.key ||= `${this._tab}:${!!this._form}:${index}`;
      if (this._details.has(detail.dataset.key)) detail.open = this._details.get(detail.dataset.key);
    }
    if (this._busy && this._form) this._form.element.querySelectorAll("button,input,select").forEach(node => { node.disabled = true; });
    else if (this._form) this._form.element.querySelectorAll("button,input,select").forEach(node => { node.disabled = false; });
  }
  _renderRemi() {
    const fragment = document.createDocumentFragment();
    const overview = el("div", { class: "remi-overview" });
    const online = this._state("binary_sensor", "online"), alive = this._state("binary_sensor", "alive");
    const status = online?.state === "off" || alive?.state === "off" ? "offline" : online?.state === "on" && alive?.state === "on" ? "online" : "statusUnknown";
    const face = this._state("select", "face")?.state;
    const knownFace = FACES.includes(face);
    this._rememberFace();
    const art = faceDrawing(face);
    const indicators = [];
    if (this._shown("show_connection")) {
      const connection = el("div", { class: "connection-indicators" }, [el("span", { class: "pill connection-status", text: `${status === "online" ? "● " : "○ "}${this.t(status)}` })]);
      const firmwareId = this._entity("binary_sensor", "firmware_update"), generation = this._generation;
      if (firmwareId && this._hass.states?.[firmwareId]?.state === "on") {
        const button = this._button("", () => {
          if (this.isConnected && generation === this._generation && this._shown("show_connection") && this._entity("binary_sensor", "firmware_update") === firmwareId && this._hass.states?.[firmwareId]?.state === "on" && this.shadowRoot.querySelector(".firmware-update") === button) this._more(firmwareId);
        }, "firmware-update");
        button.title = this.t("firmwareAvailable"); button.setAttribute("aria-label", this.t("firmwareAvailable"));
        button.append(el("ha-icon", { icon: "mdi:update", "aria-hidden": "true" })); connection.append(button);
      }
      indicators.push(connection);
    }
    if (this._shown("show_temperature")) indicators.push(el("span", { class: "temperature", text: this._textState("sensor", "temperature") }));
    overview.append(el("div", { class: "hero" }, [...(indicators.length ? [el("div", { class: "hero-top" }, indicators)] : []), art]));
    const choices = el("div", { class: "faces" });
    ["awake", "sleepy"].forEach(value => {
      const button = this._button("", () => this._setFace(value), value === face ? "selected" : "", !knownFace);
      button.setAttribute("aria-pressed", String(value === face)); button.append(faceDrawing(value, true), document.createTextNode(this.t(value))); choices.append(button);
    });
    if (this._shown("show_face")) {
      const controls = el("div", { class: "control face-controls" }, [el("div", { class: "control-title face-title" }, [el("span", { class: "face-label", text: this.t("face") }), el("span", { class: "muted current-face", text: knownFace ? this.t(face) : this.t("unknown") })]), choices]);
      overview.append(controls);
    }
    fragment.append(overview);
    const brightness = el("div", { class: "brightness-controls" });
    if (this._shown("show_brightness")) brightness.append(this._slider("brightness", 0, 100, "%"));
    if (this._shown("show_face_brightness")) brightness.append(this._faceBrightnessSlider());
    if (brightness.childNodes.length) fragment.append(brightness);
    if (this._config.show_custom_button) fragment.append(this._customButtonMode() === "card" ? this._renderCustomCard() : this._renderCustomButton());
    const player = this._state("media_player", "music_player"), playerId = this._entity("media_player", "music_player");
    const music = el("details", { class: "music" }, [el("summary", { text: this.t("music") }), el("div", { class: "row spread music-heading" }, [el("span", { class: "muted", text: this.t("music") }), this._button("⋯", () => { if (this._shown("show_music")) this._more(playerId); }, "subtle", !playerId)])]);
    music.dataset.key = "remi:music";
    if (player?.attributes?.media_title) music.append(el("p", { class: "muted", text: player.attributes.media_title }));
    music.append(el("div", { class: "music-actions" }, [["play", "▶"], ["pause", "Ⅱ"], ["stop", "■"]].map(([action, icon]) => { const button = this._button(icon, () => this._entityAction("media_player", "music_player", `media_${action}`), action === "play" ? "primary" : "", !playerId || player?.state === "unavailable"); button.title = this.t(action); button.setAttribute("aria-label", this.t(action)); return button; })), this._slider("volume", 0, 100, "%"), this._button(this.t("browse"), () => this._browse(), "full", !playerId || player?.state === "unavailable"), el("p", { class: "muted note", text: this.t("musicNote") }));
    const disclosures = el("div", { class: "remi-disclosures" });
    if (this._shown("show_music")) disclosures.append(music);
    const advanced = el("details", { class: "advanced" }, [el("summary", { text: this.t("advanced") })]);
    advanced.dataset.key = "remi:advanced";
    if (this._shown("show_face")) advanced.append(this._selectControl("face", "face"));
    advanced.append(this._selectControl("clock_format", "clock"));
    if (this._shown("show_music")) advanced.append(this._selectControl("music_mode", "musicMode"));
    advanced.append(this._slider("noise_threshold", 0, 250, ""), this._button(this.t("nightlight"), () => this._more(this._entity("light", "background_color")), "full", !this._entity("light", "background_color")));
    disclosures.append(advanced); fragment.append(disclosures); return fragment;
  }
  _slider(key, min, max, unit) {
    const state = this._state("number", key), valid = usable(state) && Number.isFinite(Number(state.state));
    const value = el("span", { class: "value", text: valid ? `${state.state}${unit}` : "—" });
    const input = el("input", { type: "range", min, max, step: 1, value: valid ? state.state : min, disabled: this._busy || !valid, "aria-label": this.t(key), oninput: event => { value.textContent = `${event.target.value}${unit}`; }, onchange: event => this._entityAction("number", key, "set_value", { value: Number(event.target.value) }) });
    return el("div", { class: "control" }, [el("div", { class: "control-title" }, [el("span", { text: this.t(key) }), value]), input]);
  }
  _faceBrightnessSlider() {
    const state = this._faceBrightnessState(), context = this._faceBrightnessContext();
    const label = number => number === null ? "—" : number === 0 ? this.t("off") : `${number}/10`;
    const value = el("span", { class: "value", text: label(state.value) });
    const input = el("input", { type: "range", class: "face-brightness-slider", min: 0, max: 10, step: 1, value: state.value ?? 0,
      disabled: this._busy || !state.available || !context.faceId || !context.numberId,
      "aria-label": this.t("face_brightness"), "aria-valuetext": label(state.value),
      oninput: event => {
        if (this._busy || !this._faceBrightnessContextCurrent(context) || this.shadowRoot.querySelector(".face-brightness-slider") !== input || !this._faceBrightnessState().available) return;
        if (!/^(?:[0-9]|10)$/.test(event.target.value)) return;
        value.textContent = label(Number(event.target.value)); input.setAttribute("aria-valuetext", value.textContent);
      },
      onchange: event => this._setFaceBrightness(event.target.value, context, input),
    });
    return el("div", { class: "control face-brightness-control" }, [el("div", { class: "control-title" }, [el("span", { text: this.t("face_brightness") }), value]), input]);
  }
  _selectControl(key, label) {
    const state = this._state("select", key);
    const select = el("select", { disabled: this._busy || !usable(state), onchange: event => this._entityAction("select", key, "select_option", { option: event.target.value }), "aria-label": this.t(label) });
    (state?.attributes?.options || []).forEach(option => select.append(el("option", { value: option, text: this.t(option), selected: option === state.state })));
    return el("label", { class: "field" }, [el("span", { class: "field-label", text: this.t(label) }), select]);
  }
  _renderAlarms() {
    const fragment = document.createDocumentFragment(), alarms = [], compact = this._config.layout === "compact";
    for (const [key, entityId] of this._index()) if (key.startsWith("switch:alarm_")) alarms.push({ eventId: this._alarmEventId(entityId), entityId, state: this._hass.states[entityId] });
    alarms.sort((a, b) => String(a.state?.attributes?.time || "99:99").localeCompare(b.state?.attributes?.time || "99:99"));
    if (!alarms.length) fragment.append(el("p", { class: "empty muted", text: this.t("emptyAlarms") }));
    alarms.forEach(alarm => {
      const attrs = alarm.state?.attributes || {}, disabled = !usable(alarm.state) || !alarm.eventId, name = attrs.alarm_name ?? attrs.friendly_name ?? this.t("alarms");
      const toggle = el("input", { type: "checkbox", class: "toggle", checked: alarm.state?.state === "on", disabled: this._busy || disabled, "aria-label": `${this.t("enabled")} ${name}`, onchange: event => { const enabled = event.target.checked; event.target.checked = alarm.state?.state === "on"; if (!this._shown("show_alarms") || !this._alarmEventId(alarm.entityId)) return; this._run(() => this._call("switch", enabled ? "turn_on" : "turn_off", {}, alarm.entityId)).catch(() => {}); } });
      if (compact) {
        const edit = this._button("", () => this._openForm("alarm", { ...attrs, event_id: alarm.eventId, enabled: alarm.state?.state === "on" }, alarm.entityId), "subtle schedule-edit", disabled);
        edit.title = `${this.t("edit")} · ${name}`; edit.setAttribute("aria-label", `${this.t("edit")} ${name}`);
        edit.append(el("ha-icon", { icon: "mdi:pencil-outline", "aria-hidden": "true" }));
        const recurrence = this._recurrenceLabel(attrs.recurrence), face = attrs.face ? this.t(attrs.face) : "";
        const item = el("section", { class: "schedule schedule-compact" }, [
          el("div", { class: "clock", text: attrs.time || "—:—" }),
          el("div", { class: "schedule-summary" }, [el("div", { class: "schedule-name", text: name }), el("div", { class: "muted schedule-recurrence", text: [recurrence, face].filter(Boolean).join(" · ") })]),
          toggle, edit,
        ]);
        if (disabled) item.append(el("p", { class: "muted schedule-unavailable", text: this.t("unavailable") }));
        fragment.append(item); return;
      }
      const item = el("section", { class: "schedule schedule-alarm" }, [el("div", { class: "row spread schedule-header" }, [el("div", { class: "schedule-heading" }, [el("div", { class: "clock", text: attrs.time || "—:—" }), el("div", { class: "schedule-name", text: name })]), toggle]), el("div", { class: "days schedule-days" }, DAYS.map(day => el("span", { class: `day${attrs.recurrence?.includes(day) ? " active" : ""}`, text: this.t(day) })))]);
      if (disabled) item.append(el("p", { class: "muted schedule-unavailable", text: this.t("unavailable") }));
      item.append(el("div", { class: "row spread schedule-footer" }, [el("span", { class: "muted schedule-face", text: attrs.face ? this.t(attrs.face) : "" }), this._button(this.t("edit"), () => this._openForm("alarm", { ...attrs, event_id: alarm.eventId, enabled: alarm.state?.state === "on" }, alarm.entityId), "subtle", disabled)]));
      fragment.append(item);
    });
    fragment.append(this._button(`+ ${this.t("addAlarm")}`, () => this._openForm("alarm"), compact ? "primary full schedule-add" : "primary full")); return fragment;
  }
  _recurrenceLabel(recurrence) {
    if (!Array.isArray(recurrence) || recurrence.some(day => !DAYS.includes(day))) return this.t("unknown");
    const days = DAYS.filter(day => recurrence.includes(day));
    if (!days.length) return this.t("once");
    if (days.length === DAYS.length) return this.t("everyDay");
    const ranges = []; let start = 0;
    for (let index = 0; index < days.length; index++) {
      if (index + 1 < days.length && DAYS.indexOf(days[index + 1]) === DAYS.indexOf(days[index]) + 1) continue;
      ranges.push(start === index ? this.t(days[index]) : `${this.t(days[start])}–${this.t(days[index])}`);
      start = index + 1;
    }
    return ranges.join(", ");
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
    const fragment = document.createDocumentFragment(), logs = this._history?.logs || [], compact = this._config.layout === "compact";
    const report = this._selectedHistory(), index = logs.findIndex(item => item.report_id === this._historyId);
    const refresh = this._button(compact ? "" : this.t("refresh"), () => this._loadHistory({ refresh: true }), "history-refresh");
    if (compact) { refresh.title = this.t("refresh"); refresh.setAttribute("aria-label", this.t("refresh")); refresh.append(el("ha-icon", { icon: "mdi:refresh", "aria-hidden": "true" })); }
    const controls = el("div", { class: "history-controls" }, [el("div", { class: "row spread history-toolbar" }, [el("span", { class: "muted", text: this.t("historyPeriod") }), refresh])]);
    fragment.append(controls);
    if (logs.length) {
      const select = el("select", { class: "history-date", "aria-label": this.t("historyPeriod"), disabled: this._busy, onchange: event => this._selectHistory(event.target.value) });
      logs.forEach(item => select.append(el("option", { value: item.report_id, selected: item.report_id === this._historyId, text: this._periodLabel(item) })));
      const previous = this._button("‹", () => this._selectHistory(logs[index + 1]?.report_id), "history-previous", index < 0 || index >= logs.length - 1);
      const next = this._button("›", () => this._selectHistory(logs[index - 1]?.report_id), "history-next", index <= 0);
      previous.setAttribute("aria-label", this.t("previousReport")); next.setAttribute("aria-label", this.t("nextReport"));
      controls.append(el("div", { class: "history-navigation" }, [previous, select, next]));
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
    const hasEstimate = ["sleep_duration", "sleep_score", "sleep_bedtime", "sleep_wake_time"].some(key => report[key] !== null && report[key] !== undefined);
    if (hasEstimate) fragment.append(stats);
    const summary = el("div", { class: "history-summary" });
    if (report.sleep_status === "unavailable") summary.append(el("p", { class: "muted note", text: this.t(compact ? "historySleepUnavailableShort" : "historySleepUnavailable"), ...(compact ? { title: this.t("historySleepUnavailable"), "aria-label": this.t("historySleepUnavailable") } : {}) }));
    const latest = logs.find(item => item.report_status === "completed" && item.sleep_status === "available" && (Number.isFinite(item.sleep_duration) && item.sleep_duration > 0 || Number.isFinite(item.sleep_score) && item.sleep_score > 0));
    if (report.sleep_status === "unavailable" && latest && latest.report_id !== report.report_id) {
      const button = this._button(this.t(compact ? "historyLatestShort" : "historyLatest"), () => this._selectHistory(latest.report_id), "history-latest subtle");
      if (compact) { button.title = this.t("historyLatest"); button.setAttribute("aria-label", this.t("historyLatest")); }
      summary.append(button);
    }
    if (summary.childNodes.length) fragment.append(summary);
    if (report.stale === true && report.report_status !== "completed") fragment.append(el("p", { class: "muted note warning", text: this.t("historyOld") }));
    if (this._history?.sync_status === "cooldown") fragment.append(el("p", { class: "muted note", text: this.t("historyCooldown") }));
    let chartSelect, chartNode;
    if (this._historyCharts) {
      const select = el("select", { class: "history-chart-kind history-date", "aria-label": this.t("historyChartKind"), disabled: this._busy, onchange: event => {
        if (!["temperature", "noise", "light"].includes(event.target.value)) return;
        this._historyKind = event.target.value; this._render();
      } });
      for (const [kind, label] of [["temperature", "temperature"], ["noise", "noiseChart"], ["light", "lightReference"]]) select.append(el("option", { value: kind, selected: kind === this._historyKind, text: `${this.t(label)}${compact && kind === "temperature" ? " · °C" : ""}` }));
      chartSelect = select; chartNode = this._chart(this._historyKind, report.series?.[this._historyKind], report.face_events);
      if (!compact) fragment.append(chartSelect, chartNode);
    }
    const infoSummary = compact ? el("summary", { class: "history-info-toggle", title: this.t("historyInfo"), "aria-label": this.t("historyInfo") }, [el("ha-icon", { icon: "mdi:information-outline", "aria-hidden": "true" })]) : el("summary", { text: this.t("historyInfo") });
    const info = el("details", { class: "history-info", "data-key": "sleep:info" }, [infoSummary]);
    for (const [key, label, cls] of [["updated_at", "historyExport", "history-export"], ["sleep_updated_at", "historySleepUpdated", "history-sleep-updated"]]) {
      if (report[key] && Number.isFinite(Date.parse(report[key]))) info.append(el("p", { class: `muted note ${cls}`, text: `${this.t(label)} · ${new Date(report[key]).toLocaleString(language(this._hass))}` }));
    }
    info.append(el("p", { class: "muted note", text: this.t("historyNote") }), el("p", { class: "muted note", text: this.t("chartNote") }));
    if (compact && chartNode?.querySelector(".face-event")) info.append(el("p", { class: "muted chart-face-note", text: this.t("faceEvents") }));
    info.append(this._button(this.t(this._historyCharts ? "hideCharts" : "charts"), () => this._toggleHistoryCharts(), "full history-charts"));
    if (compact) {
      const tools = el("div", { class: "history-chart-tools" }, [chartSelect || this._button(this.t("charts"), () => this._toggleHistoryCharts(), "history-show-charts"), info]);
      fragment.append(tools); if (chartNode) fragment.append(chartNode);
    } else fragment.append(info);
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
  _historyNeedsRefresh() {
    return Date.now() - Math.max(this._historyLoadedAt, this._historyAttemptedAt) >= 20 * 60 * 1000;
  }
  async _readHistoryDetail(generation, remiId, reportId) {
    if (!this._shown("show_sleep") || generation !== this._generation || reportId !== this._historyId) return;
    const result = await this._call(DOMAIN, "get_history", { remi_id: remiId, limit: 1, report_id: reportId }, undefined, true);
    if (generation !== this._generation || reportId !== this._historyId) return;
    const report = result?.response?.logs?.[0];
    if (!report || report.report_id !== reportId) throw new Error(this.t("historyMismatch"));
    this._historyDetail = report;
  }
  _loadHistory({ refresh = false, revalidate = false } = {}) {
    const device = this._device(), generation = this._generation; if (!device || this._busy || !this._shown("show_sleep")) return;
    const selectedId = this._historyId;
    this._historyAttemptedAt = Date.now();
    return this._run(async () => {
      const data = { remi_id: device.remiId, limit: 60, include_series: false, sync: false };
      if (refresh) Object.assign(data, { refresh: true, sync: true });
      else if (revalidate) data.refresh = true;
      const result = await this._call(DOMAIN, "get_history", data, undefined, true);
      if (generation !== this._generation || selectedId !== this._historyId) return;
      if (!Array.isArray(result?.response?.logs)) throw new Error(this.t("historyMismatch"));
      const seen = new Set(), logs = result.response.logs.filter(report => {
        if (!report || typeof report.report_id !== "string" || !report.report_id || seen.has(report.report_id)) return false;
        seen.add(report.report_id); return true;
      }).slice(0, 60);
      this._history = { ...result.response, logs };
      this._historyLoadedAt = Date.now();
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
  _chart(kind, series, faceEvents = []) {
    const compact = this._config.layout === "compact";
    const title = `${this.t(kind === "noise" ? "noiseChart" : kind === "light" ? "lightReference" : kind)}${kind === "temperature" ? " · °C" : ""}`;
    const section = el("section", { class: "chart", ...(compact ? { "aria-label": title } : {}) }, compact ? [] : [el("h3", { text: title })]);
    const valid = sample => sample && sample.valid !== false && Number.isInteger(sample.index) && sample.index >= 0 && sample.index < 720 && Number.isFinite(sample.value) && (kind !== "light" || Number.isFinite(sample.graph_value));
    const rawSamples = Array.isArray(series?.samples) ? series.samples : [], samples = rawSamples.filter(valid);
    if (!samples.length) { section.append(el("p", { class: "muted", text: this.t("noSeries") })); return section; }
    const value = sample => kind === "light" ? sample.graph_value : kind === "noise" ? sample.value * 100 / 255 : sample.value;
    // Fixed app scales make two dates comparable and avoid exaggerating tiny
    // temperature changes. Noise is a relative 0–100 scale, never decibels.
    const min = kind === "temperature" ? -10 : 0, max = kind === "temperature" ? 40 : 100;
    const bottom = compact ? 80 : 103, plotHeight = compact ? 69 : 92, labelsY = compact ? 99 : 126;
    const chart = svg("svg", { viewBox: `0 0 300 ${compact ? 105 : 135}`, role: "img", "aria-label": this.t(kind === "noise" ? "noiseChart" : kind) });
    const position = sample => [32 + sample.index / 719 * 260, bottom - (value(sample) - min) / (max - min) * plotHeight];
    chart.append(svg("line", { x1: 32, y1: bottom, x2: 292, y2: bottom, stroke: "var(--divider-color,#dde6e8)" }));
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
    const ticks = kind === "temperature" ? compact ? [-10, 15, 40] : [-10, 0, 10, 20, 30, 40] : [0, 50, 100];
    for (const tick of ticks) {
      const y = bottom - (tick - min) / (max - min) * plotHeight;
      chart.append(svg("line", { x1: 32, y1: y, x2: 292, y2: y, stroke: "var(--divider-color,#dde6e8)", "stroke-width": .5 }));
      label(kind === "light" ? tick / 100 : tick, 27, y + 3, "end");
    }
    const events = Array.isArray(faceEvents) ? faceEvents.filter(event => event && Number.isInteger(event.minute_offset) && event.minute_offset >= 0 && event.minute_offset < 1440 && FACES.includes(event.face) && typeof event.clock === "string" && /^([01]\d|2[0-3]):[0-5]\d$/.test(event.clock)) : [];
    for (const event of events) {
      const x = 32 + Math.min(event.minute_offset / 2, 719) / 719 * 260;
      const marker = svg("g", { class: "face-event", role: "img", "aria-label": `${event.clock} · ${this.t(event.face)}` });
      const tooltip = svg("title"); tooltip.textContent = `${event.clock} · ${this.t(event.face)}`;
      marker.append(tooltip, svg("circle", { cx: x, cy: bottom, r: 7, fill: "var(--card-background-color,#fff)", stroke: "var(--primary-color,#38aab9)" }));
      const symbol = svg("text", { x, y: bottom + 3, "text-anchor": "middle", fill: "var(--primary-color,#38aab9)", "font-size": 10 });
      symbol.textContent = event.face === "sleepy" ? "☾" : event.face === "off" ? "○" : "◡"; marker.append(symbol); chart.append(marker);
    }
    label("12:00", 32, labelsY); label("00:00", 32 + 360 / 719 * 260, labelsY, "middle"); label("11:58", 292, labelsY, "end");
    section.append(chart);
    if (events.length && !compact) section.append(el("p", { class: "muted chart-face-note", text: this.t("faceEvents") }));
    return section;
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
  _update(key, value) {
    const next = { ...this._config, [key]: typeof value === "boolean" ? value : value || undefined };
    try { this._config = cardConfig(next, language(this._hass)); this._editorError = null; }
    catch (error) { this._editorError = error.message; this._render(true); return; }
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true })); this._render(true);
  }
  _updateCustom(key, value) { this._update("custom_button", { ...this._config.custom_button, [key]: value }); }
  _render(force = false) {
    if (!this.shadowRoot || !this._hass) return;
    if (!force && this.shadowRoot.activeElement?.matches("input,select")) { this._renderPending = true; return; }
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
    const appearance = el("section", { class: "appearance-options" });
    for (const [key, title, choices, fallback] of [
      ["appearance", "cardAppearance", [["theme", "appearanceTheme"], ["remi", "appearanceRemi"], ["glass", "appearanceGlass"]], "theme"],
      ["layout", "cardLayout", [["full", "layoutFull"], ["compact", "layoutCompact"]], "full"],
    ]) {
      const group = el("div", { class: "visual-choices", role: "group", "aria-label": t(title) });
      for (const [value, label] of choices) {
        const selected = (this._config[key] || fallback) === value;
        const choice = el("button", { type: "button", value, class: `visual-choice${selected ? " selected" : ""}`, "aria-pressed": String(selected), "aria-label": t(label), onclick: () => this._update(key, value) }, [el("span", { class: `choice-preview ${value}`, "aria-hidden": "true" }), el("span", { text: t(label) })]);
        choice.dataset.option = key; choice.dataset.value = value; group.append(choice);
      }
      appearance.append(el("div", { class: "field" }, [el("span", { class: "field-label", text: t(title) }), group]));
    }
    const custom = el("section", { class: "custom-button-options" });
    const enabled = el("input", { type: "checkbox", checked: this._config.show_custom_button === true, "aria-label": t("showCustomButton"), onchange: event => this._update("show_custom_button", event.target.checked) });
    enabled.dataset.option = "show_custom_button";
    custom.append(el("label", { class: "display-option" }, [el("span", { text: t("showCustomButton") }), enabled]));
    if (this._config.show_custom_button) {
      const values = this._config.custom_button || {}, mode = values.mode || (values.card ? "card" : "entity");
      const field = (label, input) => el("label", { class: "field" }, [el("span", { class: "field-label", text: t(label) }), input]);
      const modes = el("select", { "aria-label": t("customMode"), onchange: event => this._updateCustom("mode", event.target.value) }); modes.dataset.customOption = "mode";
      for (const [value, label] of [["entity", "customModeEntity"], ["card", "customModeCard"]]) modes.append(el("option", { value, text: t(label), selected: mode === value }));
      custom.append(field("customMode", modes));
      if (mode === "card") custom.append(el("p", { class: "muted note", text: t("customCardHelp") }));
      else {
        custom.append(el("p", { class: "muted note", text: t("customHelp") }));
        const entities = Object.entries(this._hass.states || {}).filter(([id]) => /^(script|automation|scene|button|input_button)\.[a-z0-9_]+$/.test(id)).sort((a, b) => (a[1].attributes?.friendly_name || a[0]).localeCompare(b[1].attributes?.friendly_name || b[0]));
        const entity = el("select", { "aria-label": t("customEntity"), onchange: event => this._updateCustom("entity", event.target.value) }); entity.dataset.customOption = "entity";
        entity.append(el("option", { value: "", text: t("customChoose"), selected: !values.entity }));
        for (const [id, state] of entities) entity.append(el("option", { value: id, text: `${state.attributes?.friendly_name || id} (${id})`, selected: values.entity === id }));
        if (values.entity && !entities.some(([id]) => id === values.entity)) entity.append(el("option", { value: values.entity, text: `${values.entity} — ${t("customMissing")}`, selected: true }));
        custom.append(field("customEntity", entity));
        for (const [key, label, placeholder] of [["name", "customName", t("customButton")], ["icon", "customIcon", "mdi:play-circle-outline"]]) {
          const input = el("input", { type: "text", value: values[key] || "", placeholder, maxLength: 100, "aria-label": t(label), onchange: event => this._updateCustom(key, event.target.value) }); input.dataset.customOption = key;
          custom.append(field(label, input));
        }
        if (values.entity?.startsWith("automation.")) {
          const skip = el("input", { type: "checkbox", checked: values.skip_conditions === true, "aria-label": t("skipConditions"), onchange: event => this._updateCustom("skip_conditions", event.target.checked) }); skip.dataset.customOption = "skip_conditions";
          custom.append(el("label", { class: "display-option" }, [el("span", { text: t("skipConditions") }), skip]), el("p", { class: "muted note", text: t("customAutomationHelp") }));
        }
      }
    }
    this.shadowRoot.replaceChildren(el("style", { text: STYLE }), el("label", { class: "field" }, [el("span", { class: "field-label", text: t("device") }), select]), el("label", { class: "field" }, [el("span", { class: "field-label", text: t("title") }), el("input", { type: "text", value: this._config.title || "", onchange: event => this._update("title", event.target.value) })]), appearance, options, custom, ...(this._editorError ? [el("p", { class: "feedback error", role: "alert", text: this._editorError })] : []));
  }
}
if (globalThis.customElements) {
  if (!customElements.get("urbanhello-remi-card")) customElements.define("urbanhello-remi-card", UrbanhelloRemiCard);
  if (!customElements.get("urbanhello-remi-card-editor")) customElements.define("urbanhello-remi-card-editor", UrbanhelloRemiCardEditor);
  globalThis.customCards = globalThis.customCards || [];
  if (!globalThis.customCards.some(card => card.type === "urbanhello-remi-card")) globalThis.customCards.push({ type: "urbanhello-remi-card", name: "REMI", description: "REMI controls, schedules and sleep · Commandes, horaires et sommeil", preview: true });
}
