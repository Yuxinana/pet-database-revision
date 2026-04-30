import { escapeFormValue } from '../../utils/format/formatters.js';

const SQL_KEYWORDS = new Set([
  'SELECT','FROM','WHERE','WITH','AS','AND','OR','NOT','NULL','IS','IN','ON','JOIN','LEFT','RIGHT','INNER','OUTER',
  'CROSS','FULL','UNION','ALL','DISTINCT','GROUP','BY','ORDER','HAVING','LIMIT','OFFSET','CASE','WHEN','THEN','ELSE',
  'END','ASC','DESC','BETWEEN','LIKE','EXISTS','OVER','PARTITION',
]);

const SQL_FUNCTIONS = new Set([
  'COUNT','SUM','AVG','MIN','MAX','ROUND','COALESCE','CAST','DATE','DATETIME','STRFTIME','JULIANDAY','IFNULL','ABS',
]);

function wrapSqlToken(token) {
  const upper = token.toUpperCase();
  if (token.startsWith('--') || token.startsWith('/*')) {
    return `<span class="sql-token-comment">${escapeFormValue(token)}</span>`;
  }
  if (token.startsWith("'") || token.startsWith('"')) {
    return `<span class="sql-token-string">${escapeFormValue(token)}</span>`;
  }
  if (/^\d+(\.\d+)?$/.test(token)) {
    return `<span class="sql-token-number">${escapeFormValue(token)}</span>`;
  }
  if (/^[(),.*=<>+/\-]+$/.test(token)) {
    return `<span class="sql-token-operator">${escapeFormValue(token)}</span>`;
  }
  if (SQL_FUNCTIONS.has(upper)) {
    return `<span class="sql-token-function">${escapeFormValue(token)}</span>`;
  }
  if (SQL_KEYWORDS.has(upper)) {
    return `<span class="sql-token-keyword">${escapeFormValue(token)}</span>`;
  }
  return escapeFormValue(token);
}

export function highlightSql(sql) {
  const source = sql == null ? '' : String(sql);
  const tokenPattern = /(--.*?$|\/\*[\s\S]*?\*\/|'(?:''|[^'])*'|"(?:[^"]|"")*"|\b[A-Za-z_][A-Za-z0-9_]*\b|\b\d+(?:\.\d+)?\b|[(),.*=<>+/\-]+)/gm;
  let html = '';
  let lastIndex = 0;

  for (const match of source.matchAll(tokenPattern)) {
    const token = match[0];
    html += escapeFormValue(source.slice(lastIndex, match.index));
    html += wrapSqlToken(token);
    lastIndex = match.index + token.length;
  }

  html += escapeFormValue(source.slice(lastIndex));
  return html;
}

export function createSqlPreview(showToast) {
  let latestGeneratedSql = '';

  function renderSqlBlock(sql) {
    const panel = document.getElementById('llm-query-panel');
    const sqlBlock = document.getElementById('llm-query-sql');
    latestGeneratedSql = sql == null ? '' : String(sql);
    panel.style.display = latestGeneratedSql ? 'block' : 'none';
    sqlBlock.innerHTML = latestGeneratedSql ? highlightSql(latestGeneratedSql) : '';
  }

  async function copyGeneratedSql() {
    if (!latestGeneratedSql) {
      showToast('No SQL to copy', 'info');
      return;
    }

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(latestGeneratedSql);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = latestGeneratedSql;
        textarea.setAttribute('readonly', 'readonly');
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      showToast('SQL copied to clipboard', 'success');
    } catch (_err) {
      showToast('Copy failed', 'error');
    }
  }

  return {copyGeneratedSql, renderSqlBlock};
}
