<template>
<!-- Pets -->
  <div id="page-pets" class="page">
    <div class="page-title" style="display:flex; align-items:center; gap:12px;">Pet management</div>
    <div class="section-card">
      <div class="section-header"><span class="section-title">Pet directory</span><button class="btn-primary" data-action="open-crud" data-resource="pets" data-mode="create">+ New pet</button></div>
      <div class="toolbar">
        <input type="text" id="pet-search" placeholder="Search by name or breed..." data-action="filter-pets">
        <select id="pet-status-filter" data-action="filter-pets">
          <option value="">All statuses</option>
          <option>Available</option><option>Reserved</option>
          <option>Medical hold</option><option>Adopted</option>
        </select>
        <select id="pet-species-filter" data-action="filter-pets">
          <option value="">All species</option>
          <option>Dog</option><option>Cat</option><option>Rabbit</option>
        </select>
      </div>
      <table><thead><tr><th>ID</th><th>Name</th><th>Species</th><th>Breed</th><th>Sex</th><th>Status</th><th>Intake date</th><th>Actions</th></tr></thead>
        <tbody id="pet-tbody"></tbody>
      </table>
    </div>
  </div>
</template>
