(() => {
  const normalized = (value) => value.trim().toLocaleLowerCase();

  function initFilters() {
    const search = document.querySelector('#search');
    if (!search) return;

    const filters = {
      domain: document.querySelector('#domain-filter'),
      status: document.querySelector('#status-filter'),
      archive: document.querySelector('#archive-filter'),
    };
    const deathOptions = Array.from(document.querySelectorAll('input[name="death-filter"]'));
    const records = Array.from(document.querySelectorAll('.record'));
    const count = document.querySelector('#result-count');
    const empty = document.querySelector('#empty-state');
    const reset = document.querySelector('#reset-filters');
    const resultLink = document.querySelector('#filter-results-link');

    function applyFilters() {
      const query = normalized(search.value);
      const selectedDeaths = deathOptions.filter((option) => option.checked).map((option) => option.value);
      let visible = 0;

      records.forEach((record) => {
        const deathTypes = record.dataset.deaths.split('|').filter(Boolean);
        const matches = (
          (!query || normalized(record.dataset.search).includes(query))
          && (!filters.domain.value || record.dataset.domain === filters.domain.value)
          && (!selectedDeaths.length || selectedDeaths.some((type) => deathTypes.includes(type)))
          && (!filters.status.value || record.dataset.status === filters.status.value)
          && (!filters.archive.value || record.dataset.archive === filters.archive.value)
        );
        record.hidden = !matches;
        if (matches) visible += 1;
      });

      const active = Boolean(query) || selectedDeaths.length > 0
        || Object.values(filters).some((filter) => filter.value);
      count.textContent = `显示 ${visible} / ${records.length} 个节点`;
      if (resultLink) {
        resultLink.textContent = `查看 ${visible} 个结果 ↑`;
        resultLink.setAttribute('aria-label', `查看 ${visible} 个筛选结果并返回节点列表`);
      }
      empty.hidden = visible !== 0;
      reset.disabled = !active;
    }

    search.addEventListener('input', applyFilters);
    Object.values(filters).forEach((filter) => filter.addEventListener('change', applyFilters));
    deathOptions.forEach((option) => option.addEventListener('change', applyFilters));
    reset.addEventListener('click', () => {
      search.value = '';
      Object.values(filters).forEach((filter) => { filter.value = ''; });
      deathOptions.forEach((option) => { option.checked = false; });
      applyFilters();
      search.focus();
    });
  }

  function initSectionJumps() {
    document.querySelectorAll('.mobile-filter-link[href^="#"]').forEach((link) => {
      link.addEventListener('click', (event) => {
        const target = document.getElementById(link.hash.slice(1));
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ block: 'start' });
        target.focus({ preventScroll: true });
        history.replaceState(null, '', link.hash);
      });
    });
  }

  function initDeathSections() {
    const deaths = Array.from(document.querySelectorAll('details.death'));
    const controls = document.querySelector('#death-actions');
    if (!deaths.length || !controls) return;

    const expand = document.querySelector('#expand-deaths');
    const collapse = document.querySelector('#collapse-deaths');

    function syncControls() {
      expand.disabled = deaths.every((death) => death.open);
      collapse.disabled = deaths.every((death) => !death.open);
    }

    function openDeathFromHash(scroll = false) {
      const id = location.hash.slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target?.matches('details.death')) return;
      target.open = true;
      syncControls();
      if (scroll) target.scrollIntoView({ block: 'start' });
    }

    controls.hidden = false;
    deaths.forEach((death) => {
      death.open = false;
      death.addEventListener('toggle', syncControls);
    });
    expand.addEventListener('click', () => {
      deaths.forEach((death) => { death.open = true; });
      syncControls();
    });
    collapse.addEventListener('click', () => {
      deaths.forEach((death) => { death.open = false; });
      syncControls();
    });
    openDeathFromHash(true);
    window.addEventListener('hashchange', () => openDeathFromHash(true));
    syncControls();
  }

  initFilters();
  initSectionJumps();
  initDeathSections();
})();
