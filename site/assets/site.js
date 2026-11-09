(() => {
  const search = document.querySelector('#search');
  if (!search) return;

  const filters = {
    domain: document.querySelector('#domain-filter'),
    death: document.querySelector('#death-filter'),
    status: document.querySelector('#status-filter'),
    archive: document.querySelector('#archive-filter'),
  };
  const records = Array.from(document.querySelectorAll('.record'));
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#empty-state');
  const reset = document.querySelector('#reset-filters');

  const normalized = (value) => value.trim().toLocaleLowerCase();

  function applyFilters() {
    const query = normalized(search.value);
    let visible = 0;

    records.forEach((record) => {
      const deathTypes = record.dataset.deaths.split('|').filter(Boolean);
      const matches = (
        (!query || normalized(record.dataset.search).includes(query))
        && (!filters.domain.value || record.dataset.domain === filters.domain.value)
        && (!filters.death.value || deathTypes.includes(filters.death.value))
        && (!filters.status.value || record.dataset.status === filters.status.value)
        && (!filters.archive.value || record.dataset.archive === filters.archive.value)
      );
      record.hidden = !matches;
      if (matches) visible += 1;
    });

    const active = Boolean(query) || Object.values(filters).some((filter) => filter.value);
    count.textContent = `显示 ${visible} / ${records.length} 个节点`;
    empty.hidden = visible !== 0;
    reset.disabled = !active;
  }

  search.addEventListener('input', applyFilters);
  Object.values(filters).forEach((filter) => filter.addEventListener('change', applyFilters));
  reset.addEventListener('click', () => {
    search.value = '';
    Object.values(filters).forEach((filter) => { filter.value = ''; });
    applyFilters();
    search.focus();
  });
})();
