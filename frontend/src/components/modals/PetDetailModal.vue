<template>
<!-- ── Pet detail modal ── -->
<div class="overlay" id="pet-detail-overlay">
  <div class="modal-box modal-view">
    <div class="modal-header">
      <button class="modal-close" data-action="close-overlay" data-overlay="pet-detail-overlay">✕</button>
      <div class="modal-title" id="modal-pet-name"></div>
    </div>
    <div class="modal-body" id="modal-pet-fields"></div>
  </div>
</div>
</template>
