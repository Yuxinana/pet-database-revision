import Chart from 'chart.js/auto';
import { createApiClient } from '../services/apiClient.js';
import { APP_TIMEZONE } from '../config/appConfig.js';
import { bindDomActions } from '../utils/dom/domActions.js';
import {
  activityDotClass,
  activityTypeEntries,
  activityTypeLabel,
  clampPercent,
  emptyRow,
  entityCode,
  escapeFormValue,
  escapeHtml,
  formatMoney,
  formatPercent,
  initials,
  isoDateToUtcMs,
  speciesInitial,
  speciesKey,
  statusBadge,
  statusProgressClass,
  todayIso,
} from '../utils/format/formatters.js';
import { createSqlPreview } from '../features/assistant/sqlPreview.js';
import { createAssistantController } from '../features/assistant/assistantController.js';
import { enhanceTables } from '../utils/dom/tableEnhancements.js';
import { createCrudConfigs } from '../features/crud/crudConfigs.js';
import { loadPawtrackData } from '../features/data/pawtrackDataService.js';
import { createUiController } from '../features/ui/uiController.js';
import { createPawtrackDomain } from '../features/domain/pawtrackDomain.js';
import { renderAnalytics as renderAnalyticsView } from '../features/analytics/analyticsRenderer.js';
import { renderLoadError } from '../features/errors/loadErrorRenderer.js';
import { detailGrid, detailHeader, renderTableRows } from '../utils/dom/htmlRenderers.js';

window.Chart = Chart;

export function initializePawTrackApp() {
  const {request: apiRequest} = createApiClient();
  const {
    showToast,
    showPage,
    bindDashboardCards,
    initTableSelection,
    closeOverlay,
  } = createUiController();

  let pets = [];
  let apps = [];
  let applicants = [];
  let shelters = [];
  let adoptionRecords = [];
  let followUps = [];
  let medicalRecords = [];
  let vaccinations = [];
  let volunteers = [];
  let careAssignments = [];
  let analytics = null;
  let dashboard = null;
  let reviewingIndex = -1;
  let crudContext = null;
  let selectedActivityTypes = null;
  const getState = () => ({
    pets,
    apps,
    applicants,
    shelters,
    adoptionRecords,
    followUps,
    medicalRecords,
    vaccinations,
    volunteers,
    careAssignments,
    analytics,
    dashboard,
  });
  const {
    approvedApplicationsForPet,
    careVolunteerOptions,
    clientDeleteGuard,
    clientValidateCrudPayload,
    formatPetSelectionLabel,
    housingTypeOptions,
    petCanReceiveApplication,
    petOptions,
    petStatusOptions,
    setHousingTypeSelectValue,
  } = createPawtrackDomain({
    getState,
    getCrudContext: () => crudContext,
    todayIso,
  });
  const crudConfigs = createCrudConfigs({
    getShelters: () => shelters,
    getPets: () => pets,
    getApplicants: () => applicants,
    getAdoptionRecords: () => adoptionRecords,
    getFollowUps: () => followUps,
    getMedicalRecords: () => medicalRecords,
    getVaccinations: () => vaccinations,
    getVolunteers: () => volunteers,
    getCareAssignments: () => careAssignments,
    todayIso,
    housingTypeOptions,
    petStatusOptions,
    petOptions,
    careVolunteerOptions,
  });

  const {copyGeneratedSql, renderSqlBlock} = createSqlPreview(showToast);
  const {submitLlmPrompt} = createAssistantController({
    apiRequest,
    showToast,
    renderSqlBlock,
  });

  function normalizeSelectedActivityTypes(activities) {
    if (!(selectedActivityTypes instanceof Set)) return;
    const availableTypes = new Set(activityTypeEntries(activities).map(entry => entry.type));
    selectedActivityTypes = new Set([...selectedActivityTypes].filter(type => availableTypes.has(type)));
    if (selectedActivityTypes.size === 0) {
      selectedActivityTypes = null;
    }
  }

  function filteredActivities(activities) {
    normalizeSelectedActivityTypes(activities);
    if (!(selectedActivityTypes instanceof Set)) return activities;
    return activities.filter(activity => selectedActivityTypes.has(activity.eventType || 'activity'));
  }

  function toggleActivityType(type) {
    const activities = dashboard?.activities || [];
    const availableTypes = activityTypeEntries(activities).map(entry => entry.type);
    if (type === '__all__') {
      selectedActivityTypes = null;
      renderDashboard();
      return;
    }
    if (!availableTypes.includes(type)) return;
    if (!(selectedActivityTypes instanceof Set)) {
      selectedActivityTypes = new Set([type]);
    } else {
      const next = new Set(selectedActivityTypes);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      selectedActivityTypes = next.size ? next : null;
    }
    renderDashboard();
  }

  function actionButtons(resource, id, includeView=false) {
    const viewButton = includeView ? `<button class="btn-sm" data-action="open-pet-detail" data-id="${id}">View</button>` : '';
    return `<div class="action-row">
      ${viewButton}
      <button class="btn-sm" data-action="open-crud" data-resource="${resource}" data-mode="edit" data-id="${id}">Edit</button>
      <button class="btn-reject" data-action="delete-crud" data-resource="${resource}" data-id="${id}">Delete</button>
    </div>`;
  }

  function findCrudItem(resource, id) {
    const config = crudConfigs[resource];
    return config.data().find(item => Number(item[config.idField]) === Number(id));
  }

  function fieldValue(field, item) {
    if (item && item[field.name] != null) {
      const value = item[field.name];
      return field.type === 'date' && typeof value === 'string' ? value.slice(0, 10) : value;
    }
    if (typeof field.defaultValue === 'function') return field.defaultValue();
    return field.defaultValue ?? '';
  }

  function renderCrudField(field, item) {
    const value = fieldValue(field, item);
    const required = field.required ? ' required' : '';
    const groupClass = field.wide || field.type === 'textarea' ? 'form-group form-group-wide' : 'form-group';
    const label = `<label class="form-label">${escapeHtml(field.label)}${field.required ? ' *' : ''}</label>`;
    if (field.type === 'textarea') {
      return `<div class="${groupClass}">${label}<textarea class="form-control" id="crud-${field.name}"${required}>${escapeFormValue(value)}</textarea></div>`;
    }
    if (field.type === 'select') {
      const options = (field.options ? field.options(item, crudContext) : []).map(option => {
        const selected = String(option.value) === String(value) ? ' selected' : '';
        return `<option value="${escapeHtml(option.value)}"${selected}>${escapeHtml(option.label)}</option>`;
      }).join('');
      return `<div class="${groupClass}">${label}<select class="form-control" id="crud-${field.name}"${required}><option value="">Select...</option>${options}</select></div>`;
    }
    if (field.type === 'bool') {
      const selectedTrue = value === true || value === 'Yes' || value === 1 ? ' selected' : '';
      const selectedFalse = selectedTrue ? '' : ' selected';
      return `<div class="${groupClass}">${label}<select class="form-control" id="crud-${field.name}"><option value="true"${selectedTrue}>Yes</option><option value="false"${selectedFalse}>No</option></select></div>`;
    }
    const isDate = field.type === 'date';
    if (isDate) {
      const isFilled = value ? 'date' : 'text';
      return `<div class="${groupClass}">${label}<input class="form-control" id="crud-${field.name}" type="${isFilled}" placeholder="YYYY-MM-DD" data-date-input value="${escapeFormValue(value)}"${required}></div>`;
    }
    const inputType = field.type === 'number' || field.type === 'email' ? field.type : 'text';
    return `<div class="${groupClass}">${label}<input class="form-control" id="crud-${field.name}" type="${inputType}" value="${escapeFormValue(value)}"${required}></div>`;
  }

  function openCrudModal(resource, mode, id=null) {
    const config = crudConfigs[resource];
    const item = mode === 'edit' ? findCrudItem(resource, id) : null;
    if (mode === 'edit' && !item) {
      showToast('Record not found', 'error');
      return;
    }
    crudContext = {resource, mode, id};
    document.getElementById('crud-title').textContent = `${mode === 'create' ? 'New' : 'Edit'} ${config.label}`;
    document.getElementById('crud-submit').textContent = mode === 'create' ? 'Create' : 'Save changes';
    document.getElementById('crud-fields').innerHTML = config.fields.map(field => renderCrudField(field, item)).join('');
    document.getElementById('crud-overlay').classList.add('open');
  }

  function readCrudPayload() {
    const config = crudConfigs[crudContext.resource];
    const payload = {};
    for (const field of config.fields) {
      const el = document.getElementById(`crud-${field.name}`);
      let value = el.value;
      if (field.type === 'number') value = value === '' ? null : Number(value);
      if (field.type === 'bool') value = value === 'true';
      payload[field.name] = value;
    }
    return payload;
  }

  async function submitCrudForm() {
    if (!crudContext) return;
    const config = crudConfigs[crudContext.resource];
    const method = crudContext.mode === 'create' ? 'POST' : 'PATCH';
    const path = crudContext.mode === 'create' ? config.endpoint : `${config.endpoint}/${crudContext.id}`;
    const payload = readCrudPayload();
    const clientError = clientValidateCrudPayload(crudContext.resource, payload);
    if (clientError) {
      showToast(clientError, 'error');
      return;
    }
    try {
      await apiRequest(path, {method, body: payload});
      closeOverlay('crud-overlay');
      await loadData();
      showToast(`${config.label} ${crudContext.mode === 'create' ? 'created' : 'updated'}`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function deleteCrudRecord(resource, id) {
    const config = crudConfigs[resource];
    const item = findCrudItem(resource, id);
    const label = item?.name || item?.id || config.label;
    const blockedReason = clientDeleteGuard(resource, id);
    if (blockedReason) {
      showToast(blockedReason, 'error');
      return;
    }
    if (!window.confirm(`Delete ${label}?`)) return;
    try {
      await apiRequest(`${config.endpoint}/${id}`, {method: 'DELETE'});
      await loadData();
      showToast(`${config.label} deleted`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function loadData() {
    const data = await loadPawtrackData(apiRequest);
    dashboard = data.dashboard;
    shelters = data.shelters;
    pets = data.pets;
    applicants = data.applicants;
    apps = data.apps;
    adoptionRecords = data.adoptionRecords;
    followUps = data.followUps;
    medicalRecords = data.medicalRecords;
    vaccinations = data.vaccinations;
    volunteers = data.volunteers;
    careAssignments = data.careAssignments;
    analytics = data.analytics;

    populateSpeciesFilter();
    renderDashboard();
    renderShelters();
    filterPets();
    filterApplicants();
    filterApps();
    renderAdoptions();
    renderMedical();
    renderVolunteers();
    renderAnalyticsView(analytics || {});
  }

  function renderDashboard() {
    const stats = dashboard?.stats || {};
    const totalPets = Number(stats.totalPets);
    const availablePets = Number(stats.availablePets);
    const pendingApplications = Number(stats.pendingApplications);
    const shelterCount = Number(stats.shelterCount);
    const monthlyAdoptions = Number(stats.monthlyAdoptions);
    const activeVolunteers = volunteers.filter(v => String(v.status || '').trim().toLowerCase() === 'active').length;
    const peakShelter = shelters.reduce((best, current) => {
      const currentRate = Number(current?.occupancyRate);
      const bestRate = Number(best?.occupancyRate);
      if (!Number.isFinite(currentRate)) return best;
      if (!best || !Number.isFinite(bestRate) || currentRate > bestRate) return current;
      return best;
    }, null);
    const peakOccupancy = peakShelter ? formatPercent(peakShelter.occupancyRate) : '--';
    const availableShare = Number.isFinite(totalPets) && totalPets > 0 && Number.isFinite(availablePets)
      ? Math.round((availablePets / totalPets) * 100)
      : null;
    const heroPrimaryInsight = Number.isFinite(pendingApplications) && pendingApplications > 0
      ? `${pendingApplications} adoption ${pendingApplications === 1 ? 'review is' : 'reviews are'} waiting for a decision`
      : Number.isFinite(availablePets) && availablePets > 0
        ? `${availablePets} pets are ready for new families`
        : 'The adoption queue is clear right now';
    const heroSecondaryParts = [];
    if (Number.isFinite(shelterCount)) heroSecondaryParts.push(`${shelterCount} shelters live`);
    if (activeVolunteers) heroSecondaryParts.push(`${activeVolunteers} active volunteers`);
    if (peakShelter) heroSecondaryParts.push(`${peakShelter.name} leads occupancy at ${peakOccupancy}`);
    const heroSecondaryInsight = heroSecondaryParts.length
      ? heroSecondaryParts.join(' / ')
      : 'Waiting for live shelter data';
    const volunteerCoverage = careAssignments.length
      ? `${careAssignments.length} care ${careAssignments.length === 1 ? 'assignment' : 'assignments'} on the board`
      : 'no care assignments scheduled yet';
    const monthlyAdoptionSub = Number.isFinite(pendingApplications) && pendingApplications > 0
      ? `${pendingApplications} applications still in motion`
      : 'queue ready for the next handoff';

    document.getElementById('dash-total-pets').textContent = Number.isFinite(totalPets) ? totalPets : '--';
    document.getElementById('dash-shelter-count').textContent = `across ${Number.isFinite(shelterCount) ? shelterCount : 0} shelters`;
    document.getElementById('dash-peak-occupancy').textContent = peakOccupancy;
    document.getElementById('dash-peak-occupancy-sub').textContent = peakShelter
      ? `${peakShelter.name} / ${peakShelter.currentPetCount}/${peakShelter.capacity} pets`
      : 'no shelter occupancy data';
    document.getElementById('dash-active-volunteers').textContent = activeVolunteers;
    document.getElementById('dash-active-volunteers-sub').textContent = volunteerCoverage;
    document.getElementById('dash-monthly-adoptions').textContent = Number.isFinite(monthlyAdoptions) ? monthlyAdoptions : '--';
    document.getElementById('dash-monthly-adoptions-sub').textContent = monthlyAdoptionSub;
    document.getElementById('hero-primary-insight').textContent = heroPrimaryInsight;
    document.getElementById('hero-secondary-insight').textContent = peakShelter
      ? `Busiest shelter right now: ${peakShelter.name}.`
      : heroSecondaryInsight;
    document.getElementById('hero-available-count').textContent = Number.isFinite(availablePets) ? availablePets : '--';
    document.getElementById('hero-pending-count').textContent = Number.isFinite(pendingApplications) ? pendingApplications : '--';
    document.getElementById('hero-shelter-count').textContent = Number.isFinite(shelterCount) ? shelterCount : '--';
    document.getElementById('hero-available-detail').textContent = availableShare == null
      ? 'adoption-ready pets'
      : `${availableShare}% of all pets`;
    document.getElementById('hero-pending-detail').textContent = Number.isFinite(pendingApplications) && pendingApplications > 0
      ? 'needs staff review'
      : 'queue clear';
    document.getElementById('hero-shelter-detail').textContent = peakShelter
      ? `peak load ${peakOccupancy}`
      : 'locations live today';

    const statusTb = document.getElementById('status-overview-tbody');
    const statuses = dashboard?.statusOverview || [];
    statusTb.innerHTML = statuses.length ? statuses.map(row => `<tr>
      <td><div class="status-cell">${statusBadge(row.status)}<div class="status-progress ${statusProgressClass(row.status)}" aria-hidden="true"><span style="width:${clampPercent(row.share)}%"></span></div></div></td>
      <td><strong>${escapeHtml(row.count)}</strong></td>
      <td>${escapeHtml(row.share)}%</td>
    </tr>`).join('') : '<tr><td colspan="3" style="color:var(--color-text-secondary)">No status data</td></tr>';

    const summary = document.getElementById('activity-summary');
    const filterBar = document.getElementById('activity-filter-bar');
    const feed = document.getElementById('activity-feed');
    const activities = dashboard?.activities || [];
    const filtered = filteredActivities(activities);
    const typeEntries = activityTypeEntries(activities);
    const timezone = dashboard?.timezone || APP_TIMEZONE;
    summary.textContent = activities.length
      ? `${filtered.length} of ${activities.length} events shown`
      : 'No activity yet';
    filterBar.innerHTML = activities.length ? [
    `<button class="activity-filter-chip${selectedActivityTypes instanceof Set ? '' : ' active'}" data-action="toggle-activity-type" data-activity-type="__all__">All <span class="activity-filter-count">${escapeHtml(activities.length)}</span></button>`,
    ...typeEntries.map(entry => `<button class="activity-filter-chip${selectedActivityTypes instanceof Set && selectedActivityTypes.has(entry.type) ? ' active' : ''}" data-action="toggle-activity-type" data-activity-type="${escapeHtml(entry.type)}">${escapeHtml(activityTypeLabel(entry.type))} <span class="activity-filter-count">${escapeHtml(entry.count)}</span></button>`)
    ].join('') : '';
    feed.innerHTML = filtered.length ? filtered.map(a => `<div class="activity-item">
      <div class="activity-dot ${escapeHtml(activityDotClass(a.eventType, a.dotClass))}"></div>
      <div>
        <div class="activity-text">${escapeHtml(a.text)}</div>
        <div class="activity-meta">
          <span class="activity-type activity-type-${escapeHtml(a.eventType || 'activity')}">${escapeHtml(activityTypeLabel(a.eventType || 'activity'))}</span>
          <div class="activity-time">${escapeHtml(a.time)} · ${escapeHtml(timezone)}</div>
        </div>
      </div>
    </div>`).join('') : '<div class="activity-empty">No activity matches the current filter.</div>';
  }

  function renderShelters() {
    document.getElementById('shelter-tbody').innerHTML = renderTableRows(
      shelters,
      9,
      s => `<tr>
        <td style="color:var(--color-text-secondary)">${escapeHtml(s.id)}</td>
        <td style="font-weight:500">${escapeHtml(s.name)}</td>
        <td>${escapeHtml(s.address)}</td>
        <td>${escapeHtml(s.phone)}</td>
        <td>${escapeHtml(s.capacity)}</td>
        <td>${escapeHtml(s.currentPetCount)}</td>
        <td>${escapeHtml(s.volunteerCount)}</td>
        <td><div class="occupancy-cell"><strong>${escapeHtml(formatPercent(s.occupancyRate))}</strong><div class="occupancy-meter" aria-hidden="true"><span style="width:${clampPercent(s.occupancyRate)}%"></span></div></div></td>
        <td>${actionButtons('shelters', s.shelterId)}</td>
      </tr>`
    );


  }


  function filterApplicants() {
    const q = document.getElementById('applicant-search').value.toLowerCase();
    const experience = document.getElementById('applicant-experience-filter').value;
    renderApplicants(applicants.filter(a => {
      const searchable = [a.id, a.name, a.phone, a.email, a.address, a.housingType].join(' ').toLowerCase();
      const matchesExperience = !experience
        || (experience === 'yes' && a.hasPetExperience)
        || (experience === 'no' && !a.hasPetExperience);
      return (!q || searchable.includes(q)) && matchesExperience;
    }));
  }

  function renderApplicants(data) {
    document.getElementById('applicant-tbody').innerHTML = renderTableRows(
      data,
      9,
      a => `<tr>
        <td style="color:var(--color-text-secondary)">${escapeHtml(a.id)}</td>
        <td style="font-weight:500">${escapeHtml(a.name)}</td>
        <td>${escapeHtml(a.phone)}</td>
        <td>${escapeHtml(a.email)}</td>
        <td class="note-cell">${escapeHtml(a.address)}</td>
        <td>${escapeHtml(a.housingType)}</td>
        <td>${statusBadge(a.hasPetExperience ? 'Yes' : 'No')}</td>
        <td style="color:var(--color-text-secondary)">${escapeHtml(a.createdAt)}</td>
        <td>${actionButtons('applicants', a.applicantId)}</td>
      </tr>`
    );


  }


  function renderAdoptions() {
    document.getElementById('adoption-record-tbody').innerHTML = renderTableRows(
      adoptionRecords,
      8,
      r => `<tr>
        <td style="color:var(--color-text-secondary)">${escapeHtml(r.id)}</td>
        <td>${escapeHtml(r.applicationCode)}</td>
        <td style="font-weight:500">${escapeHtml(r.applicant)}<div class="muted-text">${escapeHtml(entityCode('A', r.applicantId))}</div></td>
        <td>${escapeHtml(r.pet)} <span class="muted-text">${escapeHtml(entityCode('P', r.petId))} ${escapeHtml(r.petSpecies)}</span></td>
        <td style="color:var(--color-text-secondary)">${escapeHtml(r.adoptionDate)}</td>
        <td>${escapeHtml(formatMoney(r.finalAdoptionFee))}</td>
        <td class="note-cell">${escapeHtml(r.handoverNote)}</td>
        <td>${escapeHtml(r.followupCount)}${r.lastFollowupDate ? `<div class="muted-text">last ${escapeHtml(r.lastFollowupDate)}</div>` : ''}</td>
      </tr>`
    );

    document.getElementById('followup-tbody').innerHTML = renderTableRows(
      followUps,
      9,
      f => `<tr>
        <td style="color:var(--color-text-secondary)">${escapeHtml(f.id)}</td>
        <td>${escapeHtml(f.adoptionCode)}</td>
        <td style="color:var(--color-text-secondary)">${escapeHtml(f.followupDate)}</td>
        <td>${escapeHtml(f.followupType)}</td>
        <td class="note-cell">${escapeHtml(f.petCondition)}</td>
        <td class="note-cell">${escapeHtml(f.adopterFeedback)}</td>
        <td>${statusBadge(f.resultStatus)}</td>
        <td class="note-cell">${escapeHtml(f.staffNote)}</td>
        <td>${actionButtons('follow-ups', f.followupId)}</td>
      </tr>`
    );


  }


  function populateSpeciesFilter() {
    const sel = document.getElementById('pet-species-filter');
    const current = sel.value;
    const species = [...new Set(pets.map(p => p.species).filter(Boolean))].sort();
    sel.innerHTML = '<option value="">All species</option>' + species.map(s => `<option>${escapeHtml(s)}</option>`).join('');
    sel.value = species.includes(current) ? current : '';
  }

  function renderPets(data) {
    const tb = document.getElementById('pet-tbody');
    if (!data.length) {
      tb.innerHTML = emptyRow(8, 'No pets', 'No pets match the current search or filter.');
      return;
    }
    tb.innerHTML = data.map(p => `<tr>
      <td style="color:var(--color-text-secondary)">${escapeHtml(p.id)}</td>
      <td><div class="pet-name-cell"><span class="pet-mini-avatar species-${speciesKey(p.species)}">${escapeHtml(speciesInitial(p.species))}</span><div>${escapeHtml(p.name)}${p.shelter ? `<div class="muted-text">${escapeHtml(p.shelter)}</div>` : ''}</div></div></td>
      <td><span class="species-chip species-${speciesKey(p.species)}">${escapeHtml(p.species)}</span></td><td>${escapeHtml(p.breed)}</td><td>${escapeHtml(p.sex)}</td>
      <td>${statusBadge(p.status)}</td>
      <td style="color:var(--color-text-secondary)">${escapeHtml(p.intake)}</td>
      <td>${actionButtons('pets', p.petId, true)}</td>
    </tr>`).join('');
  }

  function filterPets() {
    const q = document.getElementById('pet-search').value.toLowerCase();
    const st = document.getElementById('pet-status-filter').value;
    const sp = document.getElementById('pet-species-filter').value;
    renderPets(pets.filter(p => {
      const searchable = [p.id, p.name, p.breed, p.species].join(' ').toLowerCase();
      return (!q || searchable.includes(q)) && (!st || p.status === st) && (!sp || p.species === sp);
    }));
  }

  function openPetDetail(i) {
    const p = pets[i];
    if (!p) return;
    const shelterCode = p.shelterId ? `S-${String(p.shelterId).padStart(3,'0')}` : '';
    document.getElementById('modal-pet-name').innerHTML = detailHeader(
      'Pet profile',
      p.name,
      `${p.id} - ${p.species}${p.breed ? ` / ${p.breed}` : ''}`,
      statusBadge(p.status)
    );
    document.getElementById('modal-pet-fields').innerHTML = detailGrid([
      ['ID', p.id],
      ['Species', p.species],
      ['Breed', p.breed],
      ['Sex', p.sex],
      ['Color', p.color],
      ['Est. birth date', p.birth],
      ['Intake date', p.intake],
      ['Status', statusBadge(p.status), {html:true}],
      ['Sterilized', statusBadge(p.sterilized), {html:true}],
      ['Shelter ID', shelterCode],
      ['Shelter', p.shelter, {wide:true}],
      ['Special needs', p.special, {wide:true, note:true}]
    ]);
    document.getElementById('pet-detail-overlay').classList.add('open');
  }

  function openPetDetailById(id) {
    openPetDetail(pets.findIndex(p => Number(p.petId) === Number(id)));
  }

  function renderApps(data) {
    const tb = document.getElementById('app-tbody');
    if (!data.length) {
      tb.innerHTML = emptyRow(6, 'No applications', 'No applications match the current search or filter.');
      return;
    }
    tb.innerHTML = data.map(a => {
      const gi = apps.indexOf(a);
      const approvalLocked = a.rawStatus === 'Under Review' && approvedApplicationsForPet(a.petId, a.applicationId).length > 0;
      const actions = a.rawStatus === 'Under Review'
        ? approvalLocked
        ? `<div style="display:flex;gap:6px;align-items:center"><button class="btn-sm" data-action="open-app-detail" data-index="${gi}">View</button><span class="muted-text">Approval locked</span></div>`
        : `<div style="display:flex;gap:6px"><button class="btn-sm" data-action="open-app-detail" data-index="${gi}">View</button><button class="btn-approve" data-action="open-review" data-index="${gi}">Review</button></div>`
      : `<button class="btn-sm" data-action="open-app-detail" data-index="${gi}">View</button>`;
      return `<tr>
        <td style="color:var(--color-text-secondary)">${escapeHtml(a.id)}</td>
        <td style="font-weight:500">${escapeHtml(a.applicant)}</td>
        <td>${escapeHtml(a.pet)}</td>
        <td style="color:var(--color-text-secondary)">${escapeHtml(a.date)}</td>
        <td>${statusBadge(a.status)}</td>
        <td>${actions}</td>
      </tr>`;
    }).join('');
  }

  function filterApps() {
    const q = document.getElementById('app-search').value.toLowerCase();
    const st = document.getElementById('app-status-filter').value;
    renderApps(apps.filter(a => {
      const searchable = [a.id, a.applicant, a.pet, a.reason].join(' ').toLowerCase();
      return (!q || searchable.includes(q)) && (!st || a.status === st);
    }));
  }

  function openAppDetail(i) {
    const a = apps[i];
    if (!a) return;
    const applicantCode = entityCode('A', a.applicantId);
    const petCode = entityCode('P', a.petId);
    document.getElementById('modal-app-title').innerHTML = detailHeader(
      'Application',
      `${a.id} - ${a.applicant}`,
      `${applicantCode} to ${petCode} - ${a.pet}`,
      statusBadge(a.status)
    );
    document.getElementById('modal-app-fields').innerHTML = detailGrid([
      ['Applicant ID', applicantCode],
      ['Pet ID', petCode],
      ['Pet', a.pet],
      ['Application date', a.date],
      ['Status', statusBadge(a.status), {html:true}],
      ['Pet experience', statusBadge(a.hasPetExperience ? 'Yes' : 'No'), {html:true}],
      ['Applicant phone', a.applicantPhone],
      ['Applicant email', a.applicantEmail],
      ['Housing type', a.housingType],
      ['Applicant created at', a.applicantCreatedAt],
      ['Reviewer', a.reviewer],
      ['Reviewed date', a.reviewedDate],
      ['Applicant address', a.applicantAddress, {wide:true, note:true}],
      ['Reason', a.reason, {wide:true, note:true}],
      ['Decision note', a.decision, {wide:true, note:true}]
    ]);
    document.getElementById('app-detail-overlay').classList.add('open');
  }

  function openReview(i) {
    reviewingIndex = i;
    const a = apps[i];
    if (!a) return;
    document.getElementById('review-title').textContent = `Review: ${a.id}`;
    document.getElementById('review-summary').innerHTML = `<strong>${escapeHtml(a.applicant)}</strong> applied to adopt <strong>${escapeHtml(a.pet)}</strong> on ${escapeHtml(a.date)}.<br><span style="color:var(--color-text-secondary);margin-top:4px;display:block">"${escapeHtml(a.reason)}"</span>`;
    document.getElementById('review-note').value = '';
    document.getElementById('review-fee').value = '';
    document.getElementById('review-handover').value = '';
    document.getElementById('review-overlay').classList.add('open');
  }

  async function submitReview(decision) {
    if (reviewingIndex < 0) return;
    const note = document.getElementById('review-note').value.trim();
    if (!note) {
      document.getElementById('review-note').style.borderColor = '#A32D2D';
      setTimeout(() => document.getElementById('review-note').style.borderColor = '', 1500);
      return;
    }
    const a = apps[reviewingIndex];
    if (decision === 'Approved') {
      const conflict = approvedApplicationsForPet(a.petId, a.applicationId)[0];
      if (conflict) {
        showToast(`Cannot approve ${a.id}: ${a.pet} already has approved application ${conflict.id}.`, 'error');
        return;
      }
    }
    const feeText = document.getElementById('review-fee').value.trim();
    const handoverNote = document.getElementById('review-handover').value.trim();
    try {
      await apiRequest(`/api/applications/${a.applicationId}/review`, {
        method: 'PATCH',
        body: {
          decision,
          note,
          reviewerName: 'Staff (you)',
          finalAdoptionFee: feeText ? Number(feeText) : null,
          handoverNote
        }
      });
      closeOverlay('review-overlay');
      reviewingIndex = -1;
      await loadData();
      showToast(`Application ${a.id} marked as ${decision}`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function openNewAppModal() {
    const applicantSel = document.getElementById('form-applicant');
    applicantSel.innerHTML = '<option value="">Select an applicant...</option>';
    applicants.forEach(a => {
      const o = document.createElement('option');
      o.textContent = a.housingType ? `${a.name} (${a.housingType})` : a.name;
      o.value = a.applicantId;
      applicantSel.appendChild(o);
    });

    const petSel = document.getElementById('form-pet');
    petSel.innerHTML = '<option value="">Select a pet...</option>';
    pets.filter(p =>
      petCanReceiveApplication(p)
    ).forEach(p => {
      const o = document.createElement('option');
      o.textContent = formatPetSelectionLabel(p, p.breed || p.species || '');
      o.value = p.petId;
      petSel.appendChild(o);
    });
    setHousingTypeSelectValue(document.getElementById('form-housing'));
    document.getElementById('form-applicant').value = '';
    document.getElementById('form-reason').value = '';
    document.getElementById('new-app-overlay').classList.add('open');
  }

  function syncHousingFromApplicant() {
    const applicantId = Number(document.getElementById('form-applicant').value);
    const applicant = applicants.find(a => a.applicantId === applicantId);
    setHousingTypeSelectValue(document.getElementById('form-housing'), applicant?.housingType || '');
  }

  async function submitNewApp() {
    const applicantId = Number(document.getElementById('form-applicant').value);
    const petId = Number(document.getElementById('form-pet').value);
    const reason = document.getElementById('form-reason').value.trim();
    const housing = document.getElementById('form-housing').value;
    if (!applicantId || !petId || !reason || !housing) { showToast('Please fill in all fields', 'info'); return; }
    try {
      const result = await apiRequest('/api/applications', {
        method: 'POST',
        body: {applicantId, petId, reason, housingType: housing}
      });
      closeOverlay('new-app-overlay');
      await loadData();
      showToast(`Application ${result.application.id} submitted successfully`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function openNewFollowupModal() {
    const adoptionSel = document.getElementById('followup-adoption');
    adoptionSel.innerHTML = '<option value="">Select an adoption...</option>';
    adoptionRecords.forEach(record => {
      const o = document.createElement('option');
      o.textContent = `${record.id} - ${record.pet} / ${record.applicant}`;
      o.value = record.adoptionId;
      adoptionSel.appendChild(o);
    });
    document.getElementById('followup-date').value = todayIso();
    document.getElementById('followup-type').value = '';
    document.getElementById('followup-condition').value = '';
    document.getElementById('followup-feedback').value = '';
    document.getElementById('followup-result').value = '';
    document.getElementById('followup-note').value = '';
    document.getElementById('new-followup-overlay').classList.add('open');
  }

  async function submitFollowup() {
    const adoptionId = Number(document.getElementById('followup-adoption').value);
    const followupDate = document.getElementById('followup-date').value;
    const followupType = document.getElementById('followup-type').value;
    const petCondition = document.getElementById('followup-condition').value.trim();
    const adopterFeedback = document.getElementById('followup-feedback').value.trim();
    const resultStatus = document.getElementById('followup-result').value;
    const staffNote = document.getElementById('followup-note').value.trim();
    if (!adoptionId || !followupDate || !followupType || !petCondition || !resultStatus) {
      showToast('Please fill in the required follow-up fields', 'info');
      return;
    }
    try {
      const result = await apiRequest('/api/follow-ups', {
        method: 'POST',
        body: {adoptionId, followupDate, followupType, petCondition, adopterFeedback, resultStatus, staffNote}
      });
      closeOverlay('new-followup-overlay');
      await loadData();
      showToast(`Follow-up ${result.followUp.id} saved`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderMedical() {
    const medTb = document.getElementById('medical-tbody');
    medTb.innerHTML = medicalRecords.length ? medicalRecords.map(r => `<tr>
      <td style="color:var(--color-text-secondary)">${escapeHtml(r.id)}</td>
      <td>${escapeHtml(r.pet)}<div class="muted-text">${escapeHtml(entityCode('P', r.petId))}</div></td>
      <td>${escapeHtml(r.date)}</td>
      <td>${escapeHtml(r.type)}</td>
      <td class="note-cell">${escapeHtml(r.diagnosis)}</td>
      <td class="note-cell">${escapeHtml(r.treatment)}</td>
      <td>${escapeHtml(r.vet)}</td>
      <td class="note-cell">${escapeHtml(r.notes)}</td>
      <td>${actionButtons('medical-records', r.recordId)}</td>
    </tr>`).join('') : emptyRow(9, 'No medical records', 'No medical records match the current view.');

    const vaccTb = document.getElementById('vaccination-tbody');
    vaccTb.innerHTML = vaccinations.length ? vaccinations.map(v => `<tr>
      <td style="color:var(--color-text-secondary)">${escapeHtml(v.id)}</td>
      <td>${escapeHtml(v.pet)}<div class="muted-text">${escapeHtml(entityCode('P', v.petId))}</div></td>
      <td>${escapeHtml(v.vaccine)}</td>
      <td>${escapeHtml(v.doseNo)}</td>
      <td>${escapeHtml(v.vaccinationDate)}</td>
      <td${dueDateStyle(v.dueDate)}>${escapeHtml(v.dueDate)}</td>
      <td>${escapeHtml(v.vet)}</td>
      <td class="note-cell">${escapeHtml(v.notes)}</td>
      <td>${actionButtons('vaccinations', v.vaccinationId)}</td>
    </tr>`).join('') : emptyRow(9, 'No vaccinations', 'No vaccination records match the current view.');
  }

  function dueDateStyle(dateText) {
    if (!dateText) return '';
    const todayMs = isoDateToUtcMs(todayIso());
    const dueMs = isoDateToUtcMs(dateText);
    if (Number.isNaN(todayMs) || Number.isNaN(dueMs)) return '';
    const diffDays = Math.floor((dueMs - todayMs) / 86400000);
    if (diffDays < 0) return ' style="color:#A32D2D"';
    if (diffDays <= 30) return ' style="color:#854F0B"';
    return '';
  }

  function renderVolunteers() {
    const volunteerTb = document.getElementById('volunteer-tbody');
    volunteerTb.innerHTML = volunteers.length ? volunteers.map(v => `<tr>
      <td style="color:var(--color-text-secondary)">${escapeHtml(v.id)}</td>
      <td><div style="display:flex;align-items:center;gap:8px"><div class="avatar">${escapeHtml(initials(v.name))}</div>${escapeHtml(v.name)}</div></td>
      <td>${escapeHtml(v.phone)}</td>
      <td>${escapeHtml(v.email)}</td>
      <td>${escapeHtml(v.shelter)}<div class="muted-text">${escapeHtml(entityCode('S', v.shelterId))}</div></td>
      <td>${escapeHtml(v.joined)}</td>
      <td class="note-cell">${escapeHtml(v.availability)}</td>
      <td>${statusBadge(v.status)}</td>
      <td>${escapeHtml(v.assignedPets)}</td>
      <td>${actionButtons('volunteers', v.volunteerId)}</td>
    </tr>`).join('') : emptyRow(10, 'No volunteers', 'No volunteer records match the current view.');

    const careTb = document.getElementById('care-tbody');
    careTb.innerHTML = careAssignments.length ? careAssignments.map(c => `<tr>
      <td style="color:var(--color-text-secondary)">${escapeHtml(c.id)}</td>
      <td>${escapeHtml(c.date)}</td>
      <td>${escapeHtml(c.volunteer)}<div class="muted-text">${escapeHtml(entityCode('VLT', c.volunteerId))}</div></td>
      <td>${escapeHtml(c.pet)}<div class="muted-text">${escapeHtml(entityCode('P', c.petId))}</div></td>
      <td>${escapeHtml(c.shift)}</td>
      <td>${escapeHtml(c.task)}</td>
      <td>${statusBadge(c.status)}</td>
      <td class="note-cell">${escapeHtml(c.notes)}</td>
      <td>${actionButtons('care-assignments', c.assignmentId)}</td>
    </tr>`).join('') : emptyRow(9, 'No care assignments', 'No care assignments match the current view.');
  }

    const publicHandlers = {
      showPage,
      openCrudModal,
      filterPets,
      filterApplicants,
      openNewAppModal,
      filterApps,
      openNewFollowupModal,
      submitLlmPrompt,
      copyGeneratedSql,
      closeOverlay,
      submitNewApp,
      submitReview,
      submitFollowup,
      submitCrudForm,
      openPetDetailById,
      deleteCrudRecord,
      toggleActivityType,
      openAppDetail,
      openReview
    };
    bindDomActions(publicHandlers);

    initTableSelection();
    bindDashboardCards();

  document.getElementById('form-applicant').addEventListener('change', syncHousingFromApplicant);
  loadData().catch(err => {
    renderLoadError(err.message);
    showToast(`Could not load backend data: ${err.message}`, 'error');
  });

  enhanceTables();

}
