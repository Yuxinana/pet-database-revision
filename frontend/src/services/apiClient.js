export function resolveApiBase() {
  if (window.PAWTRACK_API_BASE) return window.PAWTRACK_API_BASE;

  const protocol = window.location.protocol;
  const isStandardWebOrigin = protocol === 'http:' || protocol === 'https:';
  if (isStandardWebOrigin && window.location.host) {
    return '';
  }

  return 'http://127.0.0.1:8000';
}

export function createApiClient(apiBase = resolveApiBase()) {
  function apiPath(path) {
    return apiBase + path;
  }

  async function request(path, options = {}) {
    const config = {
      headers: {'Content-Type':'application/json'},
      ...options,
    };

    if (config.body && typeof config.body !== 'string') {
      config.body = JSON.stringify(config.body);
    }

    const res = await fetch(apiPath(path), config);
    const text = await res.text();
    const payload = text ? JSON.parse(text) : {};
    if (!res.ok) {
      const err = new Error(payload.error || `Request failed with status ${res.status}`);
      err.payload = payload;
      err.status = res.status;
      throw err;
    }
    return payload;
  }

  return {apiPath, request};
}
