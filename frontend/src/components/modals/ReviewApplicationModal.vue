<template>
<!-- ── Review modal ── -->
<div class="overlay" id="review-overlay">
  <div class="modal-box">
    <button class="modal-close" data-action="close-overlay" data-overlay="review-overlay">✕</button>
    <div class="modal-title" id="review-title"></div>
    <div class="review-summary" id="review-summary"></div>
    <div class="form-group">
      <label class="form-label">Decision note</label>
      <textarea class="form-control" id="review-note" placeholder="Enter your review comments..."></textarea>
    </div>
    <div class="form-group">
      <label class="form-label">Final adoption fee</label>
      <input class="form-control" type="number" id="review-fee" min="0" step="0.01" placeholder="Used when approving">
    </div>
    <div class="form-group">
      <label class="form-label">Handover note</label>
      <textarea class="form-control" id="review-handover" placeholder="Used when approving"></textarea>
    </div>
    <div class="hint-box" style="margin-bottom:0">
      Approval creates the linked <code>ADOPTION_RECORD</code>; rejection only closes the application.
    </div>
    <div class="form-actions">
      <button class="btn-sm" data-action="close-overlay" data-overlay="review-overlay">Cancel</button>
      <button class="btn-reject" data-action="submit-review" data-decision="Rejected">Reject</button>
      <button class="btn-approve" data-action="submit-review" data-decision="Approved">Approve</button>
    </div>
  </div>
</div>
</template>
