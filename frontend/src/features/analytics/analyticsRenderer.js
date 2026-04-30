import {
  escapeHtml,
  formatPercent,
} from '../../utils/format/formatters.js';
import { renderTableRows } from '../../utils/dom/htmlRenderers.js';

export function renderAnalytics(data = {}) {
  document.getElementById('analytics-occupancy-tbody').innerHTML = renderTableRows(
    data.occupancy,
    4,
    row => `<tr>
      <td>${escapeHtml(row.shelter)}</td>
      <td>${escapeHtml(row.currentPetCount)}</td>
      <td>${escapeHtml(row.capacity)}</td>
      <td>${escapeHtml(formatPercent(row.occupancyRate))}</td>
    </tr>`
  );

  document.getElementById('analytics-housing-tbody').innerHTML = renderTableRows(
    data.housingApproval,
    4,
    row => `<tr>
      <td>${escapeHtml(row.housingType)}</td>
      <td>${escapeHtml(row.totalApplications)}</td>
      <td>${escapeHtml(row.approvedCount)}</td>
      <td>${escapeHtml(formatPercent(row.approvalRate))}</td>
    </tr>`
  );

  document.getElementById('analytics-species-tbody').innerHTML = renderTableRows(
    data.speciesDemand,
    4,
    row => `<tr>
      <td>${escapeHtml(row.species)}</td>
      <td>${escapeHtml(row.totalApplications)}</td>
      <td>${escapeHtml(row.successfulAdoptions)}</td>
      <td>${escapeHtml(formatPercent(row.adoptionSuccessRate))}</td>
    </tr>`
  );

  document.getElementById('analytics-followup-tbody').innerHTML = renderTableRows(
    data.followupOutcomes,
    2,
    row => `<tr>
      <td>${escapeHtml(row.resultStatus)}</td>
      <td>${escapeHtml(row.totalFollowups)}</td>
    </tr>`
  );

  document.getElementById('analytics-longstay-tbody').innerHTML = renderTableRows(
    data.longStayPets,
    6,
    row => `<tr>
      <td style="color:var(--color-text-secondary)">${escapeHtml(row.id)}</td>
      <td style="font-weight:500">${escapeHtml(row.name)}</td>
      <td>${escapeHtml(row.species)}</td>
      <td>${escapeHtml(row.breed)}</td>
      <td style="color:var(--color-text-secondary)">${escapeHtml(row.intakeDate)}</td>
      <td>${escapeHtml(row.daysInShelter)}</td>
    </tr>`
  );

  document.getElementById('analytics-workload-tbody').innerHTML = renderTableRows(
    data.volunteerWorkload,
    5,
    row => `<tr>
      <td style="font-weight:500">${escapeHtml(row.name)}</td>
      <td>${escapeHtml(row.totalAssignments)}</td>
      <td>${escapeHtml(row.completedTasks)}</td>
      <td>${escapeHtml(row.scheduledTasks)}</td>
      <td>${escapeHtml(row.cancelledTasks)}</td>
    </tr>`
  );

  renderAnalyticsCharts(data);
}

function renderAnalyticsCharts(data) {
  if (!window.Chart || !data) return;
  if (window.occupancyChart) window.occupancyChart.destroy();
  if (window.speciesChart) window.speciesChart.destroy();
  const css = getComputedStyle(document.documentElement);
  const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const chartText = isDarkMode ? '#dbe7f0' : css.getPropertyValue('--color-text-secondary').trim();
  const chartLegendText = isDarkMode ? '#f4f8fb' : css.getPropertyValue('--color-text-primary').trim();
  const chartGrid = isDarkMode ? 'rgba(255,255,255,0.14)' : css.getPropertyValue('--color-border-tertiary').trim();
  const chartLegendFont = {size: 12, weight: '700'};
  const doughnutBorder = isDarkMode ? 'rgba(31,40,49,0.95)' : css.getPropertyValue('--color-background-primary').trim();

  const occCtx = document.getElementById("chart-occupancy");
  if (occCtx && data.occupancy) {
    const occCanvas = occCtx.getContext("2d");
    const currentPetsGradient = occCanvas.createLinearGradient(0, 0, 0, 220);
    currentPetsGradient.addColorStop(0, "#f76707");
    currentPetsGradient.addColorStop(1, "#ffd8a8");
    const capacityGradient = occCanvas.createLinearGradient(0, 0, 0, 220);
    capacityGradient.addColorStop(0, "#0ca678");
    capacityGradient.addColorStop(1, "#c3fae8");
    window.occupancyChart = new window.Chart(occCtx, {
      type: "bar",
      data: {
        labels: data.occupancy.map(o => o.shelter),
        datasets: [
          { label: "Current Pets", data: data.occupancy.map(o => o.currentPetCount), backgroundColor: currentPetsGradient, borderRadius: 8, borderSkipped: false },
          { label: "Capacity", data: data.occupancy.map(o => o.capacity), backgroundColor: capacityGradient, borderRadius: 8, borderSkipped: false }
        ]
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        animation: {duration: 900, easing: "easeOutQuart"},
        plugins: {legend: {position: "bottom", labels: {color: chartLegendText, font: chartLegendFont, usePointStyle: true, pointStyle: "circle", boxWidth: 7, padding: 16}}},
        scales: {
          x: {grid: {display: false}, ticks: {color: chartText}},
          y: {beginAtZero: true, grid: {color: chartGrid}, ticks: {color: chartText, precision: 0}}
        }
      }
    });
  }

  const spCtx = document.getElementById("chart-species");
  if (spCtx && data.speciesDemand) {
    window.speciesChart = new window.Chart(spCtx, {
      type: "doughnut",
      data: {
        labels: data.speciesDemand.map(s => s.species),
        datasets: [{
          data: data.speciesDemand.map(s => s.totalApplications),
          backgroundColor: ["#f76707", "#1c7ed6", "#0ca678", "#fab005", "#7048e8"],
          borderColor: doughnutBorder,
          borderWidth: 4,
          hoverOffset: 8
        }]
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        animation: {animateRotate: true, duration: 900, easing: "easeOutQuart"},
        plugins: {legend: {position: "right", labels: {color: chartLegendText, font: chartLegendFont, usePointStyle: true, pointStyle: "circle", boxWidth: 7, padding: 16}}},
        cutout: "68%"
      }
    });
  }
}
