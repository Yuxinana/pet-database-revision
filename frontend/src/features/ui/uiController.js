export function createUiController() {
  function showToast(msg, type = 'success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast show toast-' + type;
    setTimeout(() => t.className = 'toast', 2800);
  }

  function navItemForPage(id) {
    return document.querySelector(`.nav-item[data-page="${id}"]`);
  }

  function showPage(id, el) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const page = document.getElementById('page-' + id);
    if (!page) return;
    page.classList.add('active', 'page-entering');
    window.setTimeout(() => page.classList.remove('page-entering'), 460);
    const nav = el || navItemForPage(id);
    if (nav) nav.classList.add('active');
  }

  function pulseDashboardTarget(id) {
    const target = document.querySelector(`#page-${id} .section-card`);
    if (!target) return;
    target.classList.remove('dashboard-target-glow');
    void target.offsetWidth;
    target.classList.add('dashboard-target-glow');
    window.setTimeout(() => target.classList.remove('dashboard-target-glow'), 1100);
  }

  function openDashboardPage(id) {
    showPage(id);
    const main = document.querySelector('.main');
    if (main) main.scrollTo({top: 0, behavior: 'smooth'});
    window.setTimeout(() => pulseDashboardTarget(id), 120);
  }

  function bindDashboardCards() {
    document.querySelectorAll('.dashboard-nav-card[data-nav-page]').forEach(card => {
      card.addEventListener('click', () => openDashboardPage(card.dataset.navPage));
      card.addEventListener('keydown', event => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        openDashboardPage(card.dataset.navPage);
      });
    });
  }

  function initTableSelection() {
    document.querySelectorAll('.section-card table').forEach(table => {
      table.addEventListener('click', event => {
        const row = event.target.closest('tr');
        if (!row || row.closest('thead')) return;
        const tbody = row.parentElement;
        tbody.querySelectorAll('tr').forEach(tr => tr.classList.remove('selected'));
        row.classList.add('selected');
      });
    });
  }

  function closeOverlay(id) {
    document.getElementById(id).classList.remove('open');
  }

  return {
    showToast,
    showPage,
    bindDashboardCards,
    initTableSelection,
    closeOverlay,
  };
}
