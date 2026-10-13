/**
 * URL State Encoding & History Utility
 * =====================================
 * Encodes and decodes application state (regex, candidate string, stage, step)
 * to/from query parameters to allow shareable URLs.
 * Manages local browser history for the last 10 regexes entered.
 */

const RECENT_REGEXES_KEY = 'automind_recent_regexes';
const MAX_RECENT_COUNT = 10;

/**
 * Encodes active studio state into a URL query string
 */
export function encodeStateToQuery({ regex = '', inputString = '', stage = 'minimized_dfa', step = 0 } = {}) {
  const params = new URLSearchParams();
  if (regex) params.set('regex', regex);
  if (inputString !== undefined && inputString !== null) params.set('string', inputString);
  if (stage) params.set('stage', stage);
  if (typeof step === 'number' && step > 0) params.set('step', String(step));
  return params.toString();
}

/**
 * Decodes studio state from search query string or URLSearchParams
 */
export function decodeStateFromQuery(searchString = '') {
  const query = searchString.startsWith('?') ? searchString.slice(1) : searchString;
  const params = new URLSearchParams(query);

  const regex = params.get('regex') || '(a|b)*abb';
  const inputString = params.get('string') !== null ? params.get('string') : 'ababb';
  const stage = params.get('stage') || 'minimized_dfa';
  const stepRaw = params.get('step');
  const step = stepRaw !== null && !isNaN(Number(stepRaw)) ? Math.max(0, parseInt(stepRaw, 10)) : 0;

  return { regex, inputString, stage, step };
}

/**
 * Syncs current state to window.location without reloading the page
 */
export function syncStateToUrl(state) {
  if (typeof window === 'undefined' || !window.history) return;
  const queryString = encodeStateToQuery(state);
  const newUrl = queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname;
  window.history.replaceState(null, '', newUrl);
}

/**
 * Retrieves up to 10 recently used regexes from localStorage
 */
export function getRecentRegexes() {
  if (typeof window === 'undefined' || !window.localStorage) return [];
  try {
    const raw = window.localStorage.getItem(RECENT_REGEXES_KEY);
    if (!raw) return [];
    const list = JSON.parse(raw);
    return Array.isArray(list) ? list.slice(0, MAX_RECENT_COUNT) : [];
  } catch (err) {
    return [];
  }
}

/**
 * Saves a regex into localStorage history, deduplicating and limiting to 10
 */
export function saveRecentRegex(regex) {
  if (!regex || typeof regex !== 'string' || !regex.trim()) return;
  if (typeof window === 'undefined' || !window.localStorage) return;

  try {
    const current = getRecentRegexes();
    const trimmed = regex.trim();
    const updated = [trimmed, ...current.filter((r) => r !== trimmed)].slice(0, MAX_RECENT_COUNT);
    window.localStorage.setItem(RECENT_REGEXES_KEY, JSON.stringify(updated));
  } catch (err) {
    // Ignore localStorage write failures
  }
}
