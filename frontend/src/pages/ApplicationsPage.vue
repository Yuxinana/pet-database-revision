<template>
<!-- Applications -->
  <div id="page-applications" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Adoption applications</div>
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">All applications</span>
        <button class="btn-primary" data-action="open-new-app">+ New application</button>
      </div>
      <div class="toolbar">
        <input type="text" id="app-search" placeholder="Search applicant or pet..." data-action="filter-apps">
        <select id="app-status-filter" data-action="filter-apps">
          <option value="">All statuses</option>
          <option>Pending</option><option>Approved</option><option>Rejected</option>
        </select>
      </div>
      <table><thead><tr><th>ID</th><th>Applicant</th><th>Pet</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody id="app-tbody"></tbody>
      </table>
    </div>
  </div>
</template>
