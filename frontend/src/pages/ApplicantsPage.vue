<template>
<!-- Applicants -->
  <div id="page-applicants" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Applicants</div>
    <div class="section-card">
      <div class="section-header"><span class="section-title">Applicant directory</span><button class="btn-primary" data-action="open-crud" data-resource="applicants" data-mode="create">+ New applicant</button></div>
      <div class="toolbar">
        <input type="text" id="applicant-search" placeholder="Search applicants..." data-action="filter-applicants">
        <select id="applicant-experience-filter" data-action="filter-applicants">
          <option value="">All experience</option>
          <option value="yes">Has pet experience</option>
          <option value="no">No pet experience</option>
        </select>
      </div>
      <table class="wide-table"><thead><tr><th>ID</th><th>Full name</th><th>Phone</th><th>Email</th><th>Address</th><th>Housing</th><th>Experience</th><th>Created at</th><th>Actions</th></tr></thead>
        <tbody id="applicant-tbody">
          <tr><td colspan="9" style="color:var(--color-text-secondary)">Loading applicants...</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
