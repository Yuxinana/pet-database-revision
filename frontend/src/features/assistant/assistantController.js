import { escapeHtml, statusBadge } from '../../utils/format/formatters.js';

export function createAssistantController({apiRequest, showToast, renderSqlBlock}) {
  async function submitLlmPrompt() {
    const input = document.getElementById('llm-prompt-input');
    const prompt = input.value.trim();
    if (!prompt) {
      showToast('Please enter a natural language prompt', 'info');
      return;
    }
    try {
      const body = {prompt, promptMethod: document.getElementById('llm-method-select').value, execute: true};
      const result = await apiRequest('/api/llm-generate-query', {method: 'POST', body});
      renderGeneratedQueryResult(result);
      showToast('Generated safe SQL', 'success');
    } catch (err) {
      renderLlmQueryError(err);
      showToast(err.message, 'error');
    }
  }

  function renderGeneratedQueryResult(result) {
    const summary = document.getElementById('llm-query-summary');
    const safety = result.validation?.safe ? 'Safe' : 'Unsafe';
    const strategy = result.resolutionStrategy === 'rule_based' ? 'Rule-based' : 'Model-assisted';
    const engine = result.resolutionStrategy === 'rule_based'
      ? 'No model call needed for this English query.'
      : `Model: ${escapeHtml(result.model)}.`;
    const normalizedPrompt = result.normalizedPrompt && result.normalizedPrompt !== result.prompt
      ? `<div class="muted-text">Interpreted prompt: ${escapeHtml(result.normalizedPrompt)}</div>`
      : '';
    const semanticNotes = (result.semanticNotes || []).slice(0, 2);
    const semanticText = semanticNotes.length
      ? `<div class="muted-text">${semanticNotes.map(note => escapeHtml(note)).join(' ')}</div>`
      : '';
    const reviewedMatches = (result.reviewedQueryMatches || []).slice(0, 2).map(match => match.title);
    const reviewedText = reviewedMatches.length
      ? `<div class="muted-text">Grounded with reviewed patterns: ${reviewedMatches.map(title => escapeHtml(title)).join(' · ')}</div>`
      : '';
    summary.style.display = 'block';
    summary.innerHTML = `<strong>Assistant SQL</strong> ${statusBadge(safety)}<br><span class="muted-text">Strategy: ${escapeHtml(strategy)}. ${engine} Method: ${escapeHtml(result.promptMethod)}. Repair attempts: ${escapeHtml(result.repairAttempts)}. Semantic retries: ${escapeHtml(result.semanticRetries || 0)}. Returned ${escapeHtml(result.rowCount)} rows.</span><div class="muted-text">${escapeHtml(result.explanation || '')}</div>${normalizedPrompt}${semanticText}${reviewedText}`;
    renderSqlAndRows(result.generatedSql, result.rows || []);
  }

  function renderSqlAndRows(sql, rows) {
    renderSqlBlock(sql);

    const head = document.getElementById('llm-query-head');
    const body = document.getElementById('llm-query-body');
    if (!rows.length) {
      head.innerHTML = '';
      body.innerHTML = '<tr><td style="text-align:center;padding:2rem;color:var(--color-text-secondary)">No rows returned</td></tr>';
      return;
    }
    const columns = Object.keys(rows[0]);
    head.innerHTML = `<tr>${columns.map(col => `<th>${escapeHtml(col)}</th>`).join('')}</tr>`;
    body.innerHTML = rows.map(row => `<tr>${columns.map(col => `<td>${escapeHtml(row[col])}</td>`).join('')}</tr>`).join('');
  }

  function renderLlmQueryError(err) {
    const payload = err.payload || {};
    const summary = document.getElementById('llm-query-summary');
    summary.style.display = 'block';
    const validation = payload.validation;
    const validationText = validation ? ` ${statusBadge(validation.safe ? 'Safe' : 'Unsafe')} <span class="muted-text">${escapeHtml(validation.reason || '')}</span>` : '';
    const normalizedPrompt = payload.normalizedPrompt ? `<div class="muted-text">Interpreted prompt: ${escapeHtml(payload.normalizedPrompt)}</div>` : '';
    const semanticIssue = payload.semanticIssue ? `<div class="muted-text">${escapeHtml(payload.semanticIssue)}</div>` : '';
    summary.innerHTML = `<strong>Assistant error</strong>${validationText}<br><span class="muted-text">${escapeHtml(err.message)}</span>${normalizedPrompt}${semanticIssue}`;
    renderSqlBlock(payload.generatedSql || '');
    document.getElementById('llm-query-head').innerHTML = '';
    document.getElementById('llm-query-body').innerHTML = '<tr><td style="text-align:center;padding:2rem;color:var(--color-text-secondary)">No executable result</td></tr>';
  }

  return {submitLlmPrompt};
}
