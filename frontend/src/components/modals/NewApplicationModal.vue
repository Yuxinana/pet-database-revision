<template>
<!-- ── New application modal ── -->
<div class="overlay" id="new-app-overlay">
  <div class="modal-box">
    <button class="modal-close" data-action="close-overlay" data-overlay="new-app-overlay">✕</button>
    <div class="modal-title">New adoption application</div>
    <div class="form-group">
      <label class="form-label">Applicant</label>
      <select class="form-control" id="form-applicant">
        <option value="">Loading applicants...</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Pet (available or reserved)</label>
      <select class="form-control" id="form-pet"><option value="">Select a pet...</option></select>
    </div>
    <div class="form-group">
      <label class="form-label">Reason for adoption</label>
      <textarea class="form-control" id="form-reason" placeholder="Describe the applicant's living situation, experience with pets, and motivation..."></textarea>
    </div>
    <div class="form-group">
      <label class="form-label">Housing type</label>
      <select class="form-control" id="form-housing"><option value="">Select housing type...</option></select>
    </div>
    <div class="hint-box">
      Submitting creates a new record in <code>ADOPTION_APPLICATION</code> shown as <code>Pending</code>. The pet's status will be updated to <code>Reserved</code>.
    </div>
    <div class="form-actions">
      <button class="btn-sm" data-action="close-overlay" data-overlay="new-app-overlay">Cancel</button>
      <button class="btn-primary" data-action="submit-new-app">Submit application</button>
    </div>
  </div>
</div>
</template>
