<template>
  <div class="app">
    <AppSidebar />
    <main class="main">
      <DashboardPage />
      <SheltersPage />
      <PetsPage />
      <ApplicantsPage />
      <ApplicationsPage />
      <AdoptionsPage />
      <MedicalPage />
      <VolunteersPage />
      <AnalyticsPage />
      <AssistantPage />
    </main>
  </div>
  <PetDetailModal />
  <ApplicationDetailModal />
  <NewApplicationModal />
  <ReviewApplicationModal />
  <NewFollowupModal />
  <CrudModal />
  <ToastMessage />
</template>

<script setup>
import { onMounted } from 'vue';
import AppSidebar from './components/AppSidebar.vue';
import ToastMessage from './components/ToastMessage.vue';
import ApplicationDetailModal from './components/modals/ApplicationDetailModal.vue';
import CrudModal from './components/modals/CrudModal.vue';
import NewApplicationModal from './components/modals/NewApplicationModal.vue';
import NewFollowupModal from './components/modals/NewFollowupModal.vue';
import PetDetailModal from './components/modals/PetDetailModal.vue';
import ReviewApplicationModal from './components/modals/ReviewApplicationModal.vue';
import { initializePawTrackApp } from './lib/pawtrackApp';
import AdoptionsPage from './pages/AdoptionsPage.vue';
import AnalyticsPage from './pages/AnalyticsPage.vue';
import ApplicantsPage from './pages/ApplicantsPage.vue';
import ApplicationsPage from './pages/ApplicationsPage.vue';
import AssistantPage from './pages/AssistantPage.vue';
import DashboardPage from './pages/DashboardPage.vue';
import MedicalPage from './pages/MedicalPage.vue';
import PetsPage from './pages/PetsPage.vue';
import SheltersPage from './pages/SheltersPage.vue';
import VolunteersPage from './pages/VolunteersPage.vue';

window.PAWTRACK_API_BASE = import.meta.env.VITE_API_BASE_URL || '';

onMounted(() => {
  initializePawTrackApp();
});
</script>
