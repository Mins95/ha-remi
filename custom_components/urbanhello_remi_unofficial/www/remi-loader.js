/* Recover bounded module-loading failures without sending REMI commands. */
const moduleUrl = new URL('./remi-card.js', import.meta.url);
moduleUrl.search = new URL(import.meta.url).search;
const state = window.__remiCardLoading ||= {pending: null, attempt: 0};

export function loadRemiCard() {
  const registered = customElements.get('urbanhello-remi-card');
  // An already mounted custom element cannot be redefined in the same page.
  // Upgrades take effect on the next normal browser reload; never force one.
  if (registered) return Promise.resolve(registered);
  if (state.pending) return state.pending;

  state.pending = (async () => {
    let lastError;
    for (let attempt = 0; attempt < 3; ++attempt) {
      if (customElements.get('urbanhello-remi-card')) return customElements.get('urbanhello-remi-card');
      const url = new URL(moduleUrl);
      // Browsers can retain failed imports until the page is reloaded.
      url.searchParams.set('load', `${Date.now()}-${++state.attempt}`);
      let timer;
      try {
        await Promise.race([
          import(url.href),
          new Promise((resolve, reject) => {
            timer = setTimeout(() => reject(new Error('REMI card loading timed out.')), 15000);
          }),
        ]);
        const card = customElements.get('urbanhello-remi-card');
        if (!card) throw new Error('The module did not register urbanhello-remi-card.');
        return card;
      } catch (error) {
        // The browser cannot cancel a timed-out import; it may finish later.
        const card = customElements.get('urbanhello-remi-card');
        if (card) return card;
        lastError = error;
      } finally {
        clearTimeout(timer);
      }
      if (attempt < 2) await new Promise(resolve => setTimeout(resolve, 250 * (attempt + 1)));
    }
    throw new Error('REMI card could not be loaded after 3 attempts. ' + (lastError?.message || lastError));
  })().finally(() => { state.pending = null; });
  return state.pending;
}

window.loadRemiCard = loadRemiCard;
// Only an explicit later call retries after the three startup attempts.
loadRemiCard().catch(() => console.warn('REMI card could not be loaded. Reload the dashboard to retry.'));
