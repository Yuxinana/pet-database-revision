<template>
<!-- Volunteers -->
  <div id="page-volunteers" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Volunteers &amp; care assignments</div>
    <div class="section-card">
      <div class="section-header"><span class="section-title">Active volunteers</span><button class="btn-primary" data-action="open-crud" data-resource="volunteers" data-mode="create">+ New volunteer</button></div>
      <table class="wide-table"><thead><tr><th>ID</th><th>Volunteer</th><th>Phone</th><th>Email</th><th>Shelter</th><th>Joined</th><th>Availability</th><th>Status</th><th>Assigned pets</th><th>Actions</th></tr></thead><tbody id="volunteer-tbody">
        <tr><td colspan="10" style="color:var(--color-text-secondary)">Loading volunteers...</td></tr>
      </tbody></table>
    </div>
    <div class="section-card">
      <div class="section-header"><span class="section-title">Care assignments</span><button class="btn-primary" data-action="open-crud" data-resource="care-assignments" data-mode="create">+ New assignment</button></div>
      <table class="wide-table"><thead><tr><th>ID</th><th>Date</th><th>Volunteer</th><th>Pet</th><th>Shift</th><th>Task</th><th>Status</th><th>Notes</th><th>Actions</th></tr></thead><tbody id="care-tbody">
        <tr><td colspan="9" style="color:var(--color-text-secondary)">Loading care assignments...</td></tr>
      </tbody></table>
    </div>
  </div>
</template>
