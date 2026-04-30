<template>
<!-- Shelters -->
  <div id="page-shelters" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Shelters</div>
    <div class="section-card">
      <div class="section-header"><span class="section-title">Shelter directory</span><button class="btn-primary" data-action="open-crud" data-resource="shelters" data-mode="create">+ New shelter</button></div>
      <table class="wide-table"><thead><tr><th>ID</th><th>Name</th><th>Address</th><th>Phone</th><th>Capacity</th><th>Current pets</th><th>Volunteers</th><th>Occupancy</th><th>Actions</th></tr></thead>
        <tbody id="shelter-tbody">
          <tr><td colspan="9" style="color:var(--color-text-secondary)">Loading shelters...</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
