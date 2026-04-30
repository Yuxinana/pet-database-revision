import { escapeHtml } from '../../utils/format/formatters.js';

export function renderLoadError(message) {
  document.getElementById('dash-total-pets').textContent = '--';
  document.getElementById('dash-shelter-count').textContent = 'backend unavailable';
  document.getElementById('hero-primary-insight').textContent = 'Backend unavailable';
  document.getElementById('hero-secondary-insight').textContent = 'Start the API server to restore live shelter data.';
  document.getElementById('hero-available-count').textContent = '--';
  document.getElementById('hero-pending-count').textContent = '--';
  document.getElementById('hero-shelter-count').textContent = '--';
  document.getElementById('hero-available-detail').textContent = 'adoption-ready pets';
  document.getElementById('hero-pending-detail').textContent = 'applications waiting for staff';
  document.getElementById('hero-shelter-detail').textContent = 'locations live today';
  document.getElementById('activity-feed').innerHTML = `<div class="activity-item"><div class="activity-dot dot-amber"></div><div><div class="activity-text">${escapeHtml(message)}</div><div class="activity-time">Start the API server</div></div></div>`;
  document.getElementById('shelter-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('pet-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('applicant-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('app-tbody').innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('adoption-record-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('followup-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('medical-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('vaccination-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('volunteer-tbody').innerHTML = '<tr><td colspan="10" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  document.getElementById('care-tbody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  ['analytics-occupancy-tbody','analytics-housing-tbody','analytics-species-tbody','analytics-followup-tbody','analytics-longstay-tbody','analytics-workload-tbody'].forEach(id => {
    const tb = document.getElementById(id);
    if (tb) tb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">Backend API is not connected</td></tr>';
  });
}
