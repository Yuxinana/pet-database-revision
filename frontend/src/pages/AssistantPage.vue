<template>
<!-- Assistant -->
	 <div id="page-assistant" class="page">
	    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Smart Assistant</div>
	    <div class="section-card">
	      <div class="section-header"><span class="section-title">Natural language query assistant</span></div>
	      <div class="assistant-control">
	        <label id="llm-method-label">Prompt method</label>
	        <select id="llm-method-select">
	          <option value="schema_grounded" selected>schema_grounded</option>
	          <option value="zero_shot">zero_shot</option>
	          <option value="few_shot">few_shot</option>
	          <option value="self_check_repair">self_check_repair</option>
	        </select>
	      </div>
	      <div class="toolbar">
	        <input type="text" id="llm-prompt-input" data-action="submit-llm-on-enter" placeholder="Ask: Which shelter is most occupied?" style="min-width:360px">
	        <button class="btn-primary" data-action="submit-llm">Run query</button>
	      </div>
	      <div class="hint-box" id="llm-mode-hint">
	        The assistant asks GLM to generate one SQLite query, then validates it with static checks, <code>EXPLAIN QUERY PLAN</code>, a read-only connection, and a SQLite authorizer before execution.
	      </div>
	      <div id="llm-query-summary" class="review-summary" style="display:none"></div>
	      <div id="llm-query-panel" class="sql-panel" style="display:none">
	        <div class="sql-panel-header">
	          <div class="sql-panel-meta">
	            <span class="sql-panel-kicker">Generated SQL</span>
	            <span class="sql-panel-title">SQLite query preview</span>
	            <span class="sql-panel-subtitle">Read-only SQL that passed backend validation before execution.</span>
	          </div>
	          <div class="sql-panel-actions">
	            <span class="sql-panel-chip">SQLite</span>
	            <button type="button" class="sql-copy-btn" data-action="copy-sql">Copy SQL</button>
	          </div>
	        </div>
	        <pre id="llm-query-sql" class="sql-block"></pre>
	      </div>
      <table><thead id="llm-query-head"></thead><tbody id="llm-query-body">
        <tr><td style="color:var(--color-text-secondary)">Try a prompt such as "show available pets" or "analyze volunteer workload".</td></tr>
      </tbody></table>
    </div>
  </div>
</template>
