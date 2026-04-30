<template>
<!-- Analytics -->
  <div id="page-analytics" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Analytics</div>
    <div class="analytics-grid">
      <div class="section-card">
        <div class="section-header"><span class="section-title">Shelter occupancy</span></div>
        <div style="position:relative; height:220px; margin-bottom:1.5rem;"><canvas id="chart-occupancy"></canvas></div>
        <table><thead><tr><th>Shelter</th><th>Pets</th><th>Capacity</th><th>Rate</th></tr></thead><tbody id="analytics-occupancy-tbody">
          <tr><td colspan="4" style="color:var(--color-text-secondary)">Loading occupancy...</td></tr>
        </tbody></table>
      </div>
      <div class="section-card">
        <div class="section-header"><span class="section-title">Housing approval rate</span></div>
        <table><thead><tr><th>Housing</th><th>Total</th><th>Approved</th><th>Rate</th></tr></thead><tbody id="analytics-housing-tbody">
          <tr><td colspan="4" style="color:var(--color-text-secondary)">Loading approval rates...</td></tr>
        </tbody></table>
      </div>
      <div class="section-card">
        <div class="section-header"><span class="section-title">Adoption demand by species</span></div>
        <div style="position:relative; height:220px; margin-bottom:1.5rem;"><canvas id="chart-species"></canvas></div>
        <table><thead><tr><th>Species</th><th>Applications</th><th>Adoptions</th><th>Success</th></tr></thead><tbody id="analytics-species-tbody">
          <tr><td colspan="4" style="color:var(--color-text-secondary)">Loading demand...</td></tr>
        </tbody></table>
      </div>
      <div class="section-card">
        <div class="section-header"><span class="section-title">Follow-up outcomes</span></div>
        <table><thead><tr><th>Result</th><th>Follow-ups</th></tr></thead><tbody id="analytics-followup-tbody">
          <tr><td colspan="2" style="color:var(--color-text-secondary)">Loading outcomes...</td></tr>
        </tbody></table>
      </div>
      <div class="section-card analytics-wide">
        <div class="section-header"><span class="section-title">Long-stay available pets</span></div>
        <table><thead><tr><th>ID</th><th>Name</th><th>Species</th><th>Breed</th><th>Intake date</th><th>Days</th></tr></thead><tbody id="analytics-longstay-tbody">
          <tr><td colspan="6" style="color:var(--color-text-secondary)">Loading long-stay pets...</td></tr>
        </tbody></table>
      </div>
      <div class="section-card analytics-wide">
        <div class="section-header"><span class="section-title">Volunteer workload</span></div>
        <table><thead><tr><th>Volunteer</th><th>Total</th><th>Completed</th><th>Scheduled</th><th>Cancelled</th></tr></thead><tbody id="analytics-workload-tbody">
          <tr><td colspan="5" style="color:var(--color-text-secondary)">Loading workload...</td></tr>
        </tbody></table>
      </div>
    </div>
  </div>
</template>
