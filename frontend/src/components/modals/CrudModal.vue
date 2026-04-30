<template>
<!-- ── Generic entity CRUD modal ── -->
<div class="overlay" id="crud-overlay">
  <div class="modal-box modal-box-wide">
    <button class="modal-close" data-action="close-overlay" data-overlay="crud-overlay">✕</button>
    <div class="modal-title" id="crud-title"></div>
    <div id="crud-fields" class="form-grid"></div>
    <div class="form-actions">
      <button class="btn-sm" data-action="close-overlay" data-overlay="crud-overlay">Cancel</button>
      <button class="btn-primary" data-action="submit-crud" id="crud-submit">Save</button>
    </div>
  </div>
</div>
</template>
