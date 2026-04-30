<template>
<!-- Adoptions -->
  <div id="page-adoptions" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Adoption records &amp; follow-ups</div>
    <div class="section-card">
      <div class="section-header"><span class="section-title">Adoption records</span></div>
      <table class="wide-table"><thead><tr><th>ID</th><th>Application</th><th>Applicant</th><th>Pet</th><th>Date</th><th>Final fee</th><th>Handover note</th><th>Follow-ups</th></tr></thead>
        <tbody id="adoption-record-tbody">
          <tr><td colspan="8" style="color:var(--color-text-secondary)">Loading adoption records...</td></tr>
        </tbody>
      </table>
    </div>
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Follow-ups</span>
        <button class="btn-primary" data-action="open-new-followup">+ New follow-up</button>
      </div>
      <table class="wide-table"><thead><tr><th>ID</th><th>Adoption</th><th>Date</th><th>Type</th><th>Pet condition</th><th>Adopter feedback</th><th>Result</th><th>Staff note</th><th>Actions</th></tr></thead>
        <tbody id="followup-tbody">
          <tr><td colspan="9" style="color:var(--color-text-secondary)">Loading follow-ups...</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
