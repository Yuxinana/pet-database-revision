<template>
<!-- ── New follow-up modal ── -->
<div class="overlay" id="new-followup-overlay">
  <div class="modal-box">
    <button class="modal-close" data-action="close-overlay" data-overlay="new-followup-overlay">✕</button>
    <div class="modal-title">New follow-up</div>
    <div class="form-group">
      <label class="form-label">Adoption record</label>
      <select class="form-control" id="followup-adoption"><option value="">Select an adoption...</option></select>
    </div>
    <div class="form-group">
      <label class="form-label">Follow-up date</label>
      <input class="form-control" type="date" id="followup-date">
    </div>
    <div class="form-group">
      <label class="form-label">Follow-up type</label>
      <select class="form-control" id="followup-type">
        <option value="">Select type...</option>
        <option>Phone Check</option><option>Home Visit</option><option>Vet Check</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Pet condition</label>
      <input class="form-control" id="followup-condition" placeholder="Stable, Improving, Needs attention...">
    </div>
    <div class="form-group">
      <label class="form-label">Adopter feedback</label>
      <textarea class="form-control" id="followup-feedback" placeholder="Feedback from adopter..."></textarea>
    </div>
    <div class="form-group">
      <label class="form-label">Result status</label>
      <select class="form-control" id="followup-result">
        <option value="">Select result...</option>
        <option>Excellent</option><option>Good</option><option>Satisfactory</option><option>Needs Improvement</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Staff note</label>
      <textarea class="form-control" id="followup-note" placeholder="Internal note..."></textarea>
    </div>
    <div class="form-actions">
      <button class="btn-sm" data-action="close-overlay" data-overlay="new-followup-overlay">Cancel</button>
      <button class="btn-primary" data-action="submit-followup">Save follow-up</button>
    </div>
  </div>
</div>
</template>
