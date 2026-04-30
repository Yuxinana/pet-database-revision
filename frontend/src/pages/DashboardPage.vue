<template>
<!-- Dashboard -->
  <div id="page-dashboard" class="page active">
    <div class="page-title">Dashboard</div>

    <div class="hero-banner">
      <div class="hero-copy">
        <h2 class="hero-title">PawTrack adoption command center</h2>
        <p class="hero-description">Coordinate shelter capacity, medical history, adoption reviews, and follow-up care from one focused dashboard.</p>
        <div class="hero-command-panel">
          <div class="hero-command-copy">
            <div class="hero-command-summary">
              <strong class="hero-command-value" id="hero-primary-insight">--</strong>
              <p class="hero-command-meta" id="hero-secondary-insight">Loading live shelter overview...</p>
            </div>
          </div>
          <div class="hero-signal-grid">
            <div class="hero-signal-card dashboard-nav-card" data-tone="green" data-nav-page="pets" role="button" tabindex="0" aria-label="Open pets page">
              <div class="hero-signal-head">
                <span class="hero-signal-label">Adoptable</span>
                <span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span>
              </div>
              <div class="hero-signal-main">
                <strong class="hero-signal-value" id="hero-available-count">--</strong>
                <span class="hero-signal-note" id="hero-available-detail">adoption-ready pets</span>
              </div>
              <span class="dashboard-card-caption">Open pets</span>
            </div>
            <div class="hero-signal-card dashboard-nav-card" data-tone="amber" data-nav-page="applications" role="button" tabindex="0" aria-label="Open applications page">
              <div class="hero-signal-head">
                <span class="hero-signal-label">In review</span>
                <span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span>
              </div>
              <div class="hero-signal-main">
                <strong class="hero-signal-value" id="hero-pending-count">--</strong>
                <span class="hero-signal-note" id="hero-pending-detail">applications waiting for staff</span>
              </div>
              <span class="dashboard-card-caption">Review applications</span>
            </div>
            <div class="hero-signal-card dashboard-nav-card" data-tone="blue" data-nav-page="shelters" role="button" tabindex="0" aria-label="Open shelters page">
              <div class="hero-signal-head">
                <span class="hero-signal-label">Shelters</span>
                <span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span>
              </div>
              <div class="hero-signal-main">
                <strong class="hero-signal-value" id="hero-shelter-count">--</strong>
                <span class="hero-signal-note" id="hero-shelter-detail">locations live today</span>
              </div>
              <span class="dashboard-card-caption">Open shelters</span>
            </div>
          </div>
        </div>
      </div>
      <div class="hero-stage" aria-hidden="true">
        <svg class="shelter-scene" viewBox="0 0 520 330" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="sceneGround" x1="86" y1="244" x2="442" y2="304" gradientUnits="userSpaceOnUse">
              <stop stop-color="#FFF4E6"/>
              <stop offset="0.55" stop-color="#D3F9D8"/>
              <stop offset="1" stop-color="#D0EBFF"/>
            </linearGradient>
            <linearGradient id="sceneHouse" x1="188" y1="88" x2="351" y2="247" gradientUnits="userSpaceOnUse">
              <stop stop-color="#FFFFFF"/>
              <stop offset="1" stop-color="#FFE8CC"/>
            </linearGradient>
            <filter id="sceneShadow" x="40" y="36" width="440" height="280" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
              <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#212529" flood-opacity="0.18"/>
            </filter>
          </defs>
          <path d="M92 256C130 212 189 200 251 218C313 236 360 213 414 242C460 267 451 306 386 311H140C86 309 66 286 92 256Z" fill="url(#sceneGround)" opacity="0.96"/>
          <g class="svg-float" filter="url(#sceneShadow)">
            <path d="M168 159L260 83L352 159V255H168V159Z" fill="url(#sceneHouse)"/>
            <path d="M142 164L260 65L378 164" stroke="#FFE3C2" stroke-width="28" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M142 164L260 65L378 164" stroke="#F76707" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="220" y="177" width="78" height="78" rx="18" fill="#1864AB"/>
            <path d="M246 255V216C246 204 256 194 268 194C280 194 290 204 290 216V255" fill="#0B7285"/>
            <rect x="186" y="173" width="42" height="38" rx="10" fill="#E7F5FF"/>
            <path d="M207 173V211M186 192H228" stroke="#74C0FC" stroke-width="5" stroke-linecap="round"/>
            <rect x="304" y="173" width="42" height="38" rx="10" fill="#EBFBEE"/>
            <path d="M325 173V211M304 192H346" stroke="#8CE99A" stroke-width="5" stroke-linecap="round"/>
            <path d="M250 120C253 111 267 111 270 120C273 128 266 137 260 141C254 137 247 128 250 120Z" fill="#D6336C"/>
          </g>
          <g class="svg-float svg-float-delayed">
            <path d="M112 232C112 213 128 200 148 200H182C205 200 221 215 221 236V251H112V232Z" fill="#FFC078"/>
            <path class="tail-wag" d="M107 225C87 215 82 197 93 186" stroke="#FFC078" stroke-width="14" stroke-linecap="round"/>
            <circle cx="154" cy="188" r="32" fill="#FFD8A8"/>
            <path d="M132 170L119 146L148 160" fill="#FFD8A8"/>
            <path d="M175 160L201 145L190 174" fill="#FFD8A8"/>
            <circle cx="144" cy="187" r="4" fill="#3D2B1F"/>
            <circle cx="166" cy="187" r="4" fill="#3D2B1F"/>
            <path d="M153 200C157 204 164 204 168 200" stroke="#3D2B1F" stroke-width="4" stroke-linecap="round"/>
            <path d="M126 251V268M199 251V268" stroke="#9C6644" stroke-width="11" stroke-linecap="round"/>
          </g>
          <g class="svg-float">
            <path d="M330 238C330 215 348 200 372 200H394C415 200 431 216 431 238V252H330V238Z" fill="#ADB5BD"/>
            <path class="cat-tail" d="M424 226C458 207 449 174 422 182" stroke="#ADB5BD" stroke-width="12" stroke-linecap="round"/>
            <circle cx="374" cy="188" r="30" fill="#CED4DA"/>
            <path d="M350 169L344 145L365 160" fill="#CED4DA"/>
            <path d="M391 160L414 146L405 171" fill="#CED4DA"/>
            <circle cx="365" cy="187" r="4" fill="#212529"/>
            <circle cx="386" cy="187" r="4" fill="#212529"/>
            <path d="M373 198C377 202 383 202 387 198" stroke="#212529" stroke-width="4" stroke-linecap="round"/>
            <path d="M348 252V267M409 252V267" stroke="#868E96" stroke-width="10" stroke-linecap="round"/>
          </g>
          <g class="heart-pop">
            <path d="M410 104C414 94 429 94 432 105C436 117 424 128 421 130C418 127 406 116 410 104Z" fill="#FFDEEB"/>
            <path d="M96 118C99 109 112 109 115 119C118 129 108 138 105 140C102 137 92 128 96 118Z" fill="#FFD43B"/>
          </g>
          <g fill="#FFFFFF" opacity="0.86">
            <g class="paw-step" style="animation-delay:0.1s"><ellipse cx="232" cy="296" rx="6" ry="8"/><circle cx="221" cy="287" r="3"/><circle cx="230" cy="284" r="3"/><circle cx="239" cy="287" r="3"/></g>
            <g class="paw-step" style="animation-delay:0.75s"><ellipse cx="268" cy="288" rx="6" ry="8"/><circle cx="257" cy="279" r="3"/><circle cx="266" cy="276" r="3"/><circle cx="275" cy="279" r="3"/></g>
            <g class="paw-step" style="animation-delay:1.4s"><ellipse cx="305" cy="296" rx="6" ry="8"/><circle cx="294" cy="287" r="3"/><circle cx="303" cy="284" r="3"/><circle cx="312" cy="287" r="3"/></g>
            <g class="paw-step" style="animation-delay:2.05s"><ellipse cx="341" cy="288" rx="6" ry="8"/><circle cx="330" cy="279" r="3"/><circle cx="339" cy="276" r="3"/><circle cx="348" cy="279" r="3"/></g>
          </g>
        </svg>
      </div>
      <div class="hero-footer">
        <div class="hero-feature">
          <span class="hero-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M4 7h16M7 4v6M17 4v6"/><rect x="4" y="7" width="16" height="13" rx="2"/><path d="M8 14h3M14 14h2M8 17h6"/></svg></span>
          <div><strong>Intake tracking</strong><p>Keep shelter capacity, pet status, and new arrivals visible.</p></div>
        </div>
        <div class="hero-feature">
          <span class="hero-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M22 12h-4l-3 8L9 4l-3 8H2"/><path d="M12 21c-4-3-7-6-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 4-3 7-7 10Z"/></svg></span>
          <div><strong>Health timeline</strong><p>See medical visits, vaccinations, and care work in context.</p></div>
        </div>
        <div class="hero-feature">
          <span class="hero-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M20 6 9 17l-5-5"/><path d="M4 20h16"/><path d="M15 4h5v5"/></svg></span>
          <div><strong>Adoption handoff</strong><p>Review applications, records, and follow-ups without losing flow.</p></div>
        </div>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card dashboard-nav-card" data-tone="orange" data-nav-page="pets" role="button" tabindex="0" aria-label="Open pet directory"><div class="stat-top"><span class="stat-label">Total pets</span><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/></svg></span></div><div class="stat-value" id="dash-total-pets">--</div><div class="stat-sub" id="dash-shelter-count">loading shelters</div><div class="stat-link-row"><span class="stat-link-text">Open pet directory</span><span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span></div></div>
      <div class="stat-card dashboard-nav-card" data-tone="blue" data-nav-page="shelters" role="button" tabindex="0" aria-label="Open shelter directory"><div class="stat-top"><span class="stat-label">Peak occupancy</span><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 11 12 5l8 6"/><path d="M7 10.5V19h10v-8.5"/><path d="M12 13v6"/><path d="M9.5 16H14.5"/></svg></span></div><div class="stat-value" id="dash-peak-occupancy">--</div><div class="stat-sub" id="dash-peak-occupancy-sub">loading shelter pressure</div><div class="stat-link-row"><span class="stat-link-text">Open shelters</span><span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span></div></div>
      <div class="stat-card dashboard-nav-card" data-tone="green" data-nav-page="volunteers" role="button" tabindex="0" aria-label="Open volunteers page"><div class="stat-top"><span class="stat-label">Active volunteers</span><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="8" r="3"/><path d="M4 20c0-3 2.5-5 5-5s5 2 5 5"/><circle cx="17.5" cy="9" r="2.5"/><path d="M15.5 20c0-2.2 1.7-3.9 4.5-4.5"/></svg></span></div><div class="stat-value" id="dash-active-volunteers">--</div><div class="stat-sub" id="dash-active-volunteers-sub">loading volunteer coverage</div><div class="stat-link-row"><span class="stat-link-text">Open volunteers</span><span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span></div></div>
      <div class="stat-card dashboard-nav-card" data-tone="amber" data-nav-page="adoptions" role="button" tabindex="0" aria-label="Open adoptions page"><div class="stat-top"><span class="stat-label">This month adoptions</span><span class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 11v10"/><path d="M15 5.5 14 10h5.5a2 2 0 0 1 2 2.3l-1.3 7A2 2 0 0 1 18.2 21H7"/><path d="M7 11H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h3"/><path d="M15 5.5C14.5 3.5 13.3 2 11.5 2L7 11"/></svg></span></div><div class="stat-value" id="dash-monthly-adoptions">--</div><div class="stat-sub" id="dash-monthly-adoptions-sub">successful adoptions this month</div><div class="stat-link-row"><span class="stat-link-text">Open adoptions</span><span class="dashboard-card-arrow" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M7 17 17 7"/><path d="M9 7h8v8"/></svg></span></div></div>
    </div>
    <div class="two-col">
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Recent activity</span>
          <span class="muted-text" id="activity-summary">Loading activity...</span>
        </div>
        <div id="activity-filter-bar" class="activity-filter-bar"></div>
        <div id="activity-feed" class="activity-feed">
          <div class="activity-item"><div class="activity-dot dot-blue"></div><div><div class="activity-text">Loading activity...</div><div class="activity-time">Backend API</div></div></div>
        </div>
      </div>
      <div class="section-card">
        <div class="section-header"><span class="section-title">Pet status overview</span></div>
        <table><thead><tr><th>Status</th><th>Count</th><th>Share</th></tr></thead><tbody id="status-overview-tbody">
          <tr><td colspan="3" style="color:var(--color-text-secondary)">Loading status overview...</td></tr>
        </tbody></table>
      </div>
    </div>
  </div>
</template>
