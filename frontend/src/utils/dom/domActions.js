const clickActionMap = {
  'show-page': (handlers, element) => handlers.showPage(element.dataset.page, element),
  'open-crud': (handlers, element) => handlers.openCrudModal(
    element.dataset.resource,
    element.dataset.mode,
    element.dataset.id ? Number(element.dataset.id) : null,
  ),
  'open-new-app': handlers => handlers.openNewAppModal(),
  'open-new-followup': handlers => handlers.openNewFollowupModal(),
  'close-overlay': (handlers, element) => handlers.closeOverlay(element.dataset.overlay),
  'submit-new-app': handlers => handlers.submitNewApp(),
  'submit-review': (handlers, element) => handlers.submitReview(element.dataset.decision),
  'submit-followup': handlers => handlers.submitFollowup(),
  'submit-crud': handlers => handlers.submitCrudForm(),
  'submit-llm': handlers => handlers.submitLlmPrompt(),
  'copy-sql': handlers => handlers.copyGeneratedSql(),
  'open-pet-detail': (handlers, element) => handlers.openPetDetailById(Number(element.dataset.id)),
  'delete-crud': (handlers, element) => handlers.deleteCrudRecord(element.dataset.resource, Number(element.dataset.id)),
  'toggle-activity-type': (handlers, element) => handlers.toggleActivityType(element.dataset.activityType),
  'open-app-detail': (handlers, element) => handlers.openAppDetail(Number(element.dataset.index)),
  'open-review': (handlers, element) => handlers.openReview(Number(element.dataset.index)),
};

const valueActionMap = {
  'filter-pets': handlers => handlers.filterPets(),
  'filter-applicants': handlers => handlers.filterApplicants(),
  'filter-apps': handlers => handlers.filterApps(),
};

export function bindDomActions(handlers, root = document) {
  root.addEventListener('click', event => {
    const element = event.target.closest('[data-action]');
    if (!element) return;

    const action = clickActionMap[element.dataset.action];
    if (!action) return;

    event.preventDefault();
    action(handlers, element, event);
  });

  for (const eventName of ['input', 'change']) {
    root.addEventListener(eventName, event => {
      const element = event.target.closest('[data-action]');
      if (!element) return;

      const action = valueActionMap[element.dataset.action];
      if (!action) return;

      action(handlers, element, event);
    });
  }

  root.addEventListener('keydown', event => {
    const element = event.target.closest('[data-action="submit-llm-on-enter"]');
    if (!element || event.key !== 'Enter') return;
    handlers.submitLlmPrompt();
  });

  root.addEventListener('focusin', event => {
    const element = event.target.closest('[data-date-input]');
    if (element) element.type = 'date';
  });

  root.addEventListener('focusout', event => {
    const element = event.target.closest('[data-date-input]');
    if (element && !element.value) element.type = 'text';
  });
}
