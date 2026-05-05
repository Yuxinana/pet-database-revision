import test from 'node:test';
import assert from 'node:assert/strict';
import { createPawtrackDomain } from '../src/features/domain/pawtrackDomain.js';

function createDomain(overrides = {}, crudContext = null) {
  const state = {
    pets: [],
    apps: [],
    applicants: [],
    shelters: [],
    adoptionRecords: [],
    followUps: [],
    medicalRecords: [],
    vaccinations: [],
    volunteers: [],
    careAssignments: [],
    analytics: null,
    dashboard: null,
    ...overrides,
  };

  return createPawtrackDomain({
    getState: () => state,
    getCrudContext: () => crudContext,
    todayIso: () => '2026-04-30',
  });
}

test('domain prevents a new pet from starting as reserved or adopted', () => {
  const domain = createDomain();

  assert.equal(
    domain.clientValidateCrudPayload('pets', {
      status: 'Reserved',
      intake: '2026-04-01',
    }),
    'New pets can start only as Available or Medical hold.',
  );
});

test('domain locks pet status when an approved application exists', () => {
  const domain = createDomain(
    {
      apps: [{petId: 10, applicationId: 99, rawStatus: 'Approved'}],
    },
    {mode: 'edit', id: 10},
  );

  assert.equal(
    domain.clientValidateCrudPayload('pets', {
      status: 'Available',
      intake: '2026-04-01',
    }),
    'A pet with an approved adoption must stay Adopted.',
  );
});

test('domain blocks deleting applicants with linked applications', () => {
  const domain = createDomain({
    apps: [{applicantId: 7}],
  });

  assert.equal(
    domain.clientDeleteGuard('applicants', 7),
    'Applicants with adoption applications cannot be deleted.',
  );
});

test('domain blocks shelter capacity below active pet count', () => {
  const domain = createDomain(
    {
      pets: [
        {petId: 1, shelterId: 2, rawStatus: 'available'},
        {petId: 2, shelterId: 2, rawStatus: 'reserved'},
        {petId: 3, shelterId: 2, rawStatus: 'adopted'},
      ],
    },
    {mode: 'edit', id: 2},
  );

  assert.equal(
    domain.clientValidateCrudPayload('shelters', {capacity: 1}),
    'Shelter capacity cannot be lower than its active pet count.',
  );
});

test('domain blocks cross-shelter care assignments', () => {
  const domain = createDomain({
    pets: [{petId: 1, shelterId: 10, intake: '2026-04-01'}],
    volunteers: [{volunteerId: 3, shelterId: 20, joined: '2026-04-01'}],
  });

  assert.equal(
    domain.clientValidateCrudPayload('care-assignments', {
      petId: 1,
      volunteerId: 3,
      date: '2026-04-30',
      status: 'Scheduled',
    }),
    'Volunteer and pet must belong to the same shelter for care assignments.',
  );
});

test('domain blocks vaccination due date before vaccination date', () => {
  const domain = createDomain({
    pets: [{petId: 1, intake: '2026-04-01'}],
  });

  assert.equal(
    domain.clientValidateCrudPayload('vaccinations', {
      petId: 1,
      vaccinationDate: '2026-04-20',
      dueDate: '2026-04-19',
    }),
    'Next due date cannot be before vaccination date.',
  );
});

test('domain exposes select options from current frontend state', () => {
  const domain = createDomain({
    pets: [{petId: 1, id: 'P-001', name: 'Mochi', shelter: 'North'}],
    volunteers: [{volunteerId: 3, id: 'VLT-003', name: 'Ava', shelter: 'North'}],
  });

  assert.deepEqual(domain.petOptions(), [{value: 1, label: 'Mochi (P-001) - North'}]);
  assert.deepEqual(domain.careVolunteerOptions(), [{value: 3, label: 'VLT-003 - Ava (North)'}]);
});
