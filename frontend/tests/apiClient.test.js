import test from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient } from '../src/services/apiClient.js';

test('api client prefixes requests and serializes JSON bodies', async () => {
  const calls = [];
  globalThis.fetch = async (url, config) => {
    calls.push({url, config});
    return {
      ok: true,
      text: async () => JSON.stringify({ok: true}),
    };
  };

  const client = createApiClient('http://api.test');
  const payload = await client.request('/api/example', {
    method: 'POST',
    body: {name: 'PawTrack'},
  });

  assert.deepEqual(payload, {ok: true});
  assert.equal(calls[0].url, 'http://api.test/api/example');
  assert.equal(calls[0].config.method, 'POST');
  assert.equal(calls[0].config.body, JSON.stringify({name: 'PawTrack'}));
  assert.equal(calls[0].config.headers['Content-Type'], 'application/json');
});

test('api client raises server errors with response payload attached', async () => {
  globalThis.fetch = async () => ({
    ok: false,
    status: 422,
    text: async () => JSON.stringify({error: 'Invalid payload', field: 'name'}),
  });

  const client = createApiClient('');

  await assert.rejects(
    () => client.request('/api/example'),
    error => {
      assert.equal(error.message, 'Invalid payload');
      assert.equal(error.status, 422);
      assert.deepEqual(error.payload, {error: 'Invalid payload', field: 'name'});
      return true;
    },
  );
});
