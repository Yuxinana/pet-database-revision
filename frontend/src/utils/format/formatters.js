import { ACTIVITY_TYPE_ORDER, APP_TIMEZONE } from '../../config/appConfig.js';

export function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value == null || value === '' ? '-' : String(value);
  return div.innerHTML;
}

export function escapeFormValue(value) {
  const div = document.createElement('div');
  div.textContent = value == null ? '' : String(value);
  return div.innerHTML;
}

export function statusBadge(status) {
  const classes = {
    'Available':'badge-available',
    'Reserved':'badge-reserved',
    'Adopted':'badge-adopted',
    'Medical hold':'badge-hold',
    'Pending':'badge-pending',
    'Approved':'badge-approved',
    'Rejected':'badge-rejected',
    'Completed':'badge-approved',
    'Scheduled':'badge-pending',
    'Cancelled':'badge-rejected',
    'Active':'badge-active',
    'Inactive':'badge-inactive',
    'Pass':'badge-approved',
    'Review':'badge-pending',
    'Excellent':'badge-approved',
    'Good':'badge-active',
    'Satisfactory':'badge-active',
    'Needs attention':'badge-pending',
    'Needs Improvement':'badge-pending',
    'Safe':'badge-approved',
    'Unsafe':'badge-rejected',
    'Configured':'badge-approved',
    'Missing':'badge-pending',
    'Yes':'badge-approved',
    'No':'badge-inactive',
  };
  return `<span class="badge ${classes[status] || ''}">${escapeHtml(status)}</span>`;
}

export function statusProgressClass(status) {
  const key = String(status || '').toLowerCase();
  if (key.includes('available')) return 'status-progress-available';
  if (key.includes('reserved') || key.includes('pending')) return 'status-progress-reserved';
  if (key.includes('adopted') || key.includes('approved')) return 'status-progress-adopted';
  if (key.includes('hold') || key.includes('rejected')) return 'status-progress-hold';
  return '';
}

export function clampPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(100, n));
}

export function speciesKey(species) {
  const key = String(species || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
  return key || 'unknown';
}

export function speciesInitial(species) {
  return String(species || '?').trim().slice(0, 1).toUpperCase() || '?';
}

export function emptyRow(colspan, title='No records found', message='It looks like there is no data to display here at the moment.') {
  return `<tr><td colspan="${colspan}">
    <div class="empty-state">
      <div class="empty-illustration">
        <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 29c5-10 23-10 28 0 3 7-3 13-12 10-2-.7-4-.7-6 0-9 3-15-3-10-10Z"/>
          <path d="M12 17c1-5 5-8 9-6 3 2 3 7 1 11-2 4-7 5-9 2-1-2-2-4-1-7Z"/>
          <path d="M27 11c4-2 8 1 9 6s-1 9-5 9-7-4-7-8c0-3 1-6 3-7Z"/>
        </svg>
      </div>
      <div class="empty-state-title">${escapeHtml(title)}</div>
      <div class="empty-state-message">${escapeHtml(message)}</div>
    </div>
  </td></tr>`;
}

export function entityCode(prefix, value) {
  return value ? `${prefix}-${String(value).padStart(3, '0')}` : '';
}

export function zonedDateParts(baseDate = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: APP_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(baseDate);
  return {
    year: Number(parts.find(part => part.type === 'year')?.value || 0),
    month: Number(parts.find(part => part.type === 'month')?.value || 0),
    day: Number(parts.find(part => part.type === 'day')?.value || 0),
  };
}

export function formatDateParts(parts) {
  return `${String(parts.year).padStart(4, '0')}-${String(parts.month).padStart(2, '0')}-${String(parts.day).padStart(2, '0')}`;
}

export function todayIso() {
  return formatDateParts(zonedDateParts());
}

export function activityTypeLabel(type) {
  const labels = {
    adoption: 'Adoption',
    application_review: 'Review',
    application: 'Application',
    applicant: 'Applicant',
    medical: 'Medical',
    vaccination: 'Vaccination',
    care_assignment: 'Assignment',
    follow_up: 'Follow-up',
    volunteer: 'Volunteer',
    pet: 'Pet',
    shelter: 'Shelter',
    pet_intake: 'Pet intake',
  };
  return labels[type] || String(type || 'Activity').replace(/_/g, ' ');
}

export function activityDotClass(type, fallbackClass) {
  const normalized = String(type || '').trim().replace(/[^\w-]/g, '_');
  return normalized ? `activity-dot-${normalized}` : (fallbackClass || 'dot-blue');
}

export function activityTypeEntries(activities) {
  const counts = new Map();
  activities.forEach(activity => {
    const type = activity.eventType || 'activity';
    counts.set(type, (counts.get(type) || 0) + 1);
  });
  return [...counts.entries()]
    .map(([type, count]) => ({type, count}))
    .sort((a, b) => {
      const leftIndex = ACTIVITY_TYPE_ORDER.indexOf(a.type);
      const rightIndex = ACTIVITY_TYPE_ORDER.indexOf(b.type);
      if (leftIndex !== -1 || rightIndex !== -1) {
        return (leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex)
          - (rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex);
      }
      return activityTypeLabel(a.type).localeCompare(activityTypeLabel(b.type));
    });
}

export function isoDateToUtcMs(dateText) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(dateText || ''));
  if (!match) return NaN;
  return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

export function formatPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
  return `${n.toFixed(n % 1 === 0 ? 0 : 2)}%`;
}

export function formatMoney(value) {
  if (value == null || value === '') return '-';
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
  return `$${n.toFixed(2)}`;
}

export function initials(name) {
  return String(name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0].toUpperCase())
    .join('') || '?';
}
