<template>
  <iframe class="legacy-app-frame" title="PawTrack" :src="legacyUrl"></iframe>
</template>

<script setup>
const legacyUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/pawtrack_demo.html`;
</script>
