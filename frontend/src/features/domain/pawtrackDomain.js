import { HOUSING_TYPES } from '../../config/appConfig.js';
import { escapeFormValue, escapeHtml } from '../../utils/format/formatters.js';

export function createPawtrackDomain({getState, getCrudContext, todayIso}) {
  function housingTypeOptions() {
    return HOUSING_TYPES.map(v => ({value:v, label:v}));
  }

  function setHousingTypeSelectValue(selectEl, value = '') {
    if (!selectEl) return;
    selectEl.innerHTML = '<option value="">Select housing type...</option>' +
      HOUSING_TYPES.map(type => `<option value="${escapeFormValue(type)}">${escapeHtml(type)}</option>`).join('');
    selectEl.value = value && HOUSING_TYPES.includes(value) ? value : '';
  }

  function formatPetSelectionLabel(p, detail = '') {
    const suffix = detail ? ` - ${detail}` : '';
    return `${p.name} (${p.id})${suffix}`;
  }

  function petOptions() {
    const {pets} = getState();
    return pets.map(p => ({
      value:p.petId,
      label:formatPetSelectionLabel(p, p.shelter || '')
    }));
  }

  function careVolunteerOptions() {
    const {volunteers} = getState();
    return volunteers.map(v => ({value:v.volunteerId, label:`${v.id} - ${v.name}${v.shelter ? ` (${v.shelter})` : ''}`}));
  }

  function petById(id) {
    return getState().pets.find(p => Number(p.petId) === Number(id));
  }

  function volunteerById(id) {
    return getState().volunteers.find(v => Number(v.volunteerId) === Number(id));
  }

  function approvedApplicationsForPet(petId, excludeApplicationId=null) {
    return getState().apps.filter(a =>
      Number(a.petId) === Number(petId)
      && a.rawStatus === 'Approved'
      && Number(a.applicationId) !== Number(excludeApplicationId)
    );
  }

  function pendingApplicationsForPet(petId, excludeApplicationId=null) {
    return getState().apps.filter(a =>
      Number(a.petId) === Number(petId)
      && a.rawStatus === 'Under Review'
      && Number(a.applicationId) !== Number(excludeApplicationId)
    );
  }

  function petCanReceiveApplication(p) {
    return ['available', 'reserved'].includes(String(p?.rawStatus || '').toLowerCase())
      && !approvedApplicationsForPet(p.petId).length;
  }

  function earliestAdoptionDateForPet(petId) {
    const {adoptionRecords} = getState();
    const dates = adoptionRecords
      .filter(r => Number(r.petId) === Number(petId) && r.adoptionDate)
      .map(r => r.adoptionDate)
      .sort();
    return dates[0] || '';
  }

  function petStatusOptions(item) {
    if (!item) {
      return ['Available','Medical hold'].map(v => ({value:v, label:v}));
    }
    const pending = pendingApplicationsForPet(item.petId, item.applicationId).length > 0;
    const approved = approvedApplicationsForPet(item.petId, item.applicationId).length > 0;
    if (pending) return ['Reserved'].map(v => ({value:v, label:v}));
    if (approved) return ['Adopted'].map(v => ({value:v, label:v}));
    return ['Available','Medical hold'].map(v => ({value:v, label:v}));
  }

  function normalizePetStatusValue(value) {
    const normalized = String(value || '').trim().toLowerCase().replace(/\s+/g, '_');
    const map = {
      'available': 'available',
      'reserved': 'reserved',
      'adopted': 'adopted',
      'medical_hold': 'medical_hold'
    };
    return map[normalized] || normalized;
  }

  function firstDateConflict(entries, limitDate) {
    return entries
      .filter(([, value]) => value && value < limitDate)
      .sort((a, b) => a[1].localeCompare(b[1]))[0] || null;
  }

  function clientValidateCrudPayload(resource, payload) {
    const {pets, apps, adoptionRecords, medicalRecords, vaccinations, careAssignments} = getState();
    const crudContext = getCrudContext();
    const editingId = crudContext?.mode === 'edit' ? Number(crudContext.id) : null;

    if (resource === 'shelters' && editingId != null) {
      const activePets = pets.filter(p =>
        Number(p.shelterId) === editingId
        && ['available', 'reserved', 'medical_hold'].includes(p.rawStatus)
      ).length;
      if (payload.capacity != null && Number(payload.capacity) < activePets) {
        return 'Shelter capacity cannot be lower than its active pet count.';
      }
    }

    if (resource === 'pets') {
      const nextStatus = normalizePetStatusValue(payload.status);
      if (payload.birth && payload.intake && payload.birth > payload.intake) {
        return 'Estimated birth date cannot be after intake date.';
      }
      if (payload.intake && payload.intake > todayIso()) {
        return 'Pet intake date cannot be in the future.';
      }
      if (editingId == null) {
        if (nextStatus === 'reserved' || nextStatus === 'adopted') {
          return 'New pets can start only as Available or Medical hold.';
        }
        return null;
      }

      const pending = pendingApplicationsForPet(editingId).length > 0;
      const approved = approvedApplicationsForPet(editingId).length > 0;
      if (pending && nextStatus !== 'reserved') {
        return 'A pet with a pending application must stay Reserved.';
      }
      if (!pending && approved && nextStatus !== 'adopted') {
        return 'A pet with an approved adoption must stay Adopted.';
      }
      if (!pending && !approved && (nextStatus === 'reserved' || nextStatus === 'adopted')) {
        return 'Reserved and Adopted statuses must come from the adoption workflow, not direct edits.';
      }
      if (payload.intake) {
        const relatedConflict = firstDateConflict([
          ...apps.filter(a => Number(a.petId) === editingId).map(a => ['application', a.date]),
          ...adoptionRecords.filter(r => Number(r.petId) === editingId).map(r => ['adoption', r.adoptionDate]),
          ...medicalRecords.filter(r => Number(r.petId) === editingId).map(r => ['medical visit', r.date]),
          ...vaccinations.filter(v => Number(v.petId) === editingId).map(v => ['vaccination', v.vaccinationDate]),
          ...careAssignments.filter(c => Number(c.petId) === editingId).map(c => ['care assignment', c.date])
        ], payload.intake);
        if (relatedConflict) {
          return `Pet intake date cannot be later than an existing ${relatedConflict[0]} on ${relatedConflict[1]}.`;
        }
      }
      if (payload.shelterId) {
        const conflictingAssignment = careAssignments.find(c =>
          Number(c.petId) === editingId
          && Number(volunteerById(c.volunteerId)?.shelterId) !== Number(payload.shelterId)
        );
        if (conflictingAssignment) {
          return 'Pet shelter cannot be changed because existing care assignments would become cross-shelter.';
        }
      }
      return null;
    }

    if (resource === 'medical-records') {
      const pet = petById(payload.petId);
      if (pet && payload.date && pet.intake && payload.date < pet.intake) {
        return 'Medical visit date cannot be before pet intake date.';
      }
    }

    if (resource === 'vaccinations') {
      const pet = petById(payload.petId);
      if (pet && payload.vaccinationDate && pet.intake && payload.vaccinationDate < pet.intake) {
        return 'Vaccination date cannot be before pet intake date.';
      }
      if (payload.dueDate && payload.vaccinationDate && payload.dueDate < payload.vaccinationDate) {
        return 'Next due date cannot be before vaccination date.';
      }
    }

    if (resource === 'volunteers') {
      if (editingId != null && payload.joined) {
        const earlyAssignment = firstDateConflict(
          careAssignments
            .filter(c => Number(c.volunteerId) === editingId)
            .map(c => ['care assignment', c.date]),
          payload.joined
        );
        if (earlyAssignment) {
          return `Volunteer join date cannot be later than existing ${earlyAssignment[0]} on ${earlyAssignment[1]}.`;
        }
      }
      if (editingId != null && payload.shelterId) {
        const conflictingAssignment = careAssignments.find(c =>
          Number(c.volunteerId) === editingId
          && Number(petById(c.petId)?.shelterId) !== Number(payload.shelterId)
        );
        if (conflictingAssignment) {
          return 'Volunteer shelter cannot be changed because existing care assignments would become cross-shelter.';
        }
      }
    }

    if (resource === 'care-assignments') {
      const volunteer = volunteerById(payload.volunteerId);
      const pet = petById(payload.petId);
      if (volunteer && pet && Number(volunteer.shelterId) !== Number(pet.shelterId)) {
        return 'Volunteer and pet must belong to the same shelter for care assignments.';
      }
      if (pet && payload.date && pet.intake && payload.date < pet.intake) {
        return 'Care assignment date cannot be before pet intake date.';
      }
      if (volunteer && payload.date && volunteer.joined && payload.date < volunteer.joined) {
        return 'Care assignment date cannot be before the volunteer join date.';
      }
      const adoptionDate = earliestAdoptionDateForPet(payload.petId);
      if (adoptionDate && payload.date && payload.date >= adoptionDate && payload.status !== 'Cancelled') {
        return 'Adopted pets cannot receive scheduled care assignments on or after adoption date.';
      }
    }

    if (resource === 'follow-ups') {
      const adoption = adoptionRecords.find(r => Number(r.adoptionId) === Number(payload.adoptionId));
      if (adoption && payload.followupDate && adoption.adoptionDate && payload.followupDate < adoption.adoptionDate) {
        return 'Follow-up date cannot be before adoption date.';
      }
    }

    return null;
  }

  function clientDeleteGuard(resource, id) {
    const {pets, apps, medicalRecords, vaccinations, volunteers, careAssignments} = getState();
    if (resource === 'shelters') {
      if (pets.some(p => Number(p.shelterId) === Number(id)) || volunteers.some(v => Number(v.shelterId) === Number(id))) {
        return 'Shelters with linked pets or volunteers cannot be deleted.';
      }
    }
    if (resource === 'applicants') {
      if (apps.some(a => Number(a.applicantId) === Number(id))) {
        return 'Applicants with adoption applications cannot be deleted.';
      }
    }
    if (resource === 'pets') {
      if (
        apps.some(a => Number(a.petId) === Number(id))
        || medicalRecords.some(r => Number(r.petId) === Number(id))
        || vaccinations.some(v => Number(v.petId) === Number(id))
        || careAssignments.some(c => Number(c.petId) === Number(id))
      ) {
        return 'Pets with linked applications, medical records, vaccinations, or care assignments cannot be deleted.';
      }
    }
    if (resource === 'volunteers') {
      if (careAssignments.some(c => Number(c.volunteerId) === Number(id))) {
        return 'Volunteers with care assignments cannot be deleted.';
      }
    }
    return null;
  }

  return {
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
    volunteerById,
  };
}
