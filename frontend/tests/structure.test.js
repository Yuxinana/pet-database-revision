import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');

test('frontend keeps standard Vue project layers', () => {
  [
    'src/App.vue',
    'src/components/AppSidebar.vue',
    'src/pages/DashboardPage.vue',
    'src/services/apiClient.js',
    'src/config/appConfig.js',
    'src/features/analytics/analyticsRenderer.js',
    'src/features/assistant/assistantController.js',
    'src/features/crud/crudConfigs.js',
    'src/features/data/pawtrackDataService.js',
    'src/features/domain/pawtrackDomain.js',
    'src/features/errors/loadErrorRenderer.js',
    'src/features/ui/uiController.js',
    'src/styles/main.css',
    'src/utils/dom/domActions.js',
    'src/utils/format/formatters.js',
  ].forEach(path => {
    assert.equal(existsSync(resolve(root, path)), true, `${path} should exist`);
  });
});
