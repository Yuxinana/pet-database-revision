<template>
  <iframe class="legacy-app-frame" title="PawTrack" :src="legacyUrl"></iframe>
</template>

<script setup>
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
const legacyUrl = `${apiBaseUrl}/pawtrack_demo.html`;
</script>
