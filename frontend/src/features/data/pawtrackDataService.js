export async function loadPawtrackData(apiRequest) {
  const [
    dashboardData,
    shelterData,
    petsData,
    applicantsData,
    applicationsData,
    adoptionRecordData,
    followupData,
    medicalData,
    vaccinationData,
    volunteerData,
    assignmentData,
    analyticsData,
  ] = await Promise.all([
    apiRequest('/api/dashboard'),
    apiRequest('/api/shelters'),
    apiRequest('/api/pets'),
    apiRequest('/api/applicants'),
    apiRequest('/api/applications'),
    apiRequest('/api/adoption-records'),
    apiRequest('/api/follow-ups'),
    apiRequest('/api/medical-records'),
    apiRequest('/api/vaccinations'),
    apiRequest('/api/volunteers'),
    apiRequest('/api/care-assignments'),
    apiRequest('/api/analytics'),
  ]);

  return {
    dashboard: dashboardData,
    shelters: shelterData.shelters || [],
    pets: petsData.pets || [],
    applicants: applicantsData.applicants || [],
    apps: applicationsData.applications || [],
    adoptionRecords: adoptionRecordData.adoptionRecords || [],
    followUps: followupData.followUps || [],
    medicalRecords: medicalData.medicalRecords || [],
    vaccinations: vaccinationData.vaccinations || [],
    volunteers: volunteerData.volunteers || [],
    careAssignments: assignmentData.careAssignments || [],
    analytics: analyticsData,
  };
}
