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

test('domain exposes select options from current frontend state', () => {
  const domain = createDomain({
    pets: [{petId: 1, id: 'P-001', name: 'Mochi', shelter: 'North'}],
    volunteers: [{volunteerId: 3, id: 'VLT-003', name: 'Ava', shelter: 'North'}],
  });

  assert.deepEqual(domain.petOptions(), [{value: 1, label: 'Mochi (P-001) - North'}]);
  assert.deepEqual(domain.careVolunteerOptions(), [{value: 3, label: 'VLT-003 - Ava (North)'}]);
});
