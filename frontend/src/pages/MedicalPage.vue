<template>
<!-- Medical -->
  <div id="page-medical" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Medical records</div>
    <div class="medical-grid" style="display:grid; grid-template-columns:1fr; gap:1.5rem">
      <div class="section-card">
        <div class="section-header"><span class="section-title" style="display:flex;align-items:center;gap:8px">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-info)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
          Medical visits
        </span><button class="btn-primary" data-action="open-crud" data-resource="medical-records" data-mode="create">+ New visit</button></div>
        <table class="wide-table"><thead><tr><th>ID</th><th>Pet</th><th>Visit date</th><th>Type</th><th>Diagnosis</th><th>Treatment</th><th>Vet</th><th>Notes</th><th>Actions</th></tr></thead><tbody id="medical-tbody">
          <tr><td colspan="9" style="color:var(--color-text-secondary)">Loading medical records...</td></tr>
        </tbody></table>
      </div>
      <div class="section-card">
        <div class="section-header"><span class="section-title" style="display:flex;align-items:center;gap:8px">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          Vaccinations
        </span><button class="btn-primary" data-action="open-crud" data-resource="vaccinations" data-mode="create">+ New vaccine</button></div>
        <table class="wide-table"><thead><tr><th>ID</th><th>Pet</th><th>Vaccine</th><th>Dose</th><th>Vaccination date</th><th>Due date</th><th>Vet</th><th>Notes</th><th>Actions</th></tr></thead><tbody id="vaccination-tbody">
          <tr><td colspan="9" style="color:var(--color-text-secondary)">Loading vaccinations...</td></tr>
        </tbody></table>
      </div>
    </div>
  </div>
</template>
