import { emptyRow, escapeHtml } from '../format/formatters.js';

export function renderTableRows(rows, colspan, renderRow) {
  return rows?.length
    ? rows.map(renderRow).join('')
    : emptyRow(colspan);
}

export function detailHeader(kicker, title, subtitle, badgeHtml = '') {
  return `<div class="detail-heading">
    <div>
      <div class="detail-kicker">${escapeHtml(kicker)}</div>
      <div class="detail-name">${escapeHtml(title)}</div>
      ${subtitle ? `<div class="detail-subtitle">${escapeHtml(subtitle)}</div>` : ''}
    </div>
    ${badgeHtml ? `<div class="detail-status">${badgeHtml}</div>` : ''}
  </div>`;
}

export function detailField(label, value, options = {}) {
  const classes = ['detail-field'];
  if (options.wide) classes.push('detail-field-wide');
  if (options.note) classes.push('detail-note');
  const content = options.html ? (value || '<span class="detail-empty">-</span>') : detailValueHtml(value);
  return `<div class="${classes.join(' ')}">
    <div class="detail-label">${escapeHtml(label)}</div>
    <div class="detail-value">${content}</div>
  </div>`;
}

export function detailGrid(fields) {
  return `<div class="detail-grid">${fields.map(([label, value, options]) => detailField(label, value, options || {})).join('')}</div>`;
}

function detailValueHtml(value) {
  return value == null || value === '' ? '<span class="detail-empty">-</span>' : escapeHtml(value);
}
