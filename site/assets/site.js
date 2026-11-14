(() => {
  const normalized = (value) => String(value || '').trim().toLocaleLowerCase();
  let syncDeathControls = () => {};

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
    const indexStatus = document.querySelector('#search-index-status');
    let fullIndex = null;
    let indexPromise = null;
    let indexFailed = false;

    function setIndexStatus(message) {
      if (!indexStatus) return;
      indexStatus.textContent = message;
      indexStatus.hidden = !message;
    }

    function matchingSections(record, query) {
      const sections = fullIndex?.[record.dataset.nodeId]?.sections;
      if (!Array.isArray(sections)) return [];
      return sections.map((section, order) => {
        const label = String(section?.label || '');
        const content = String(section?.text || '');
        const labelText = normalized(label);
        const contentText = normalized(content);
        const labelHit = labelText.includes(query);
        const occurrences = contentText ? contentText.split(query).length - 1 : 0;
        return { section, order, labelHit, occurrences, content };
      }).filter((item) => item.labelHit || item.occurrences > 0)
        .sort((left, right) => (
          Number(right.labelHit) - Number(left.labelHit)
          || right.occurrences - left.occurrences
          || left.order - right.order
        ))
        .slice(0, 2);
    }

    function makeExcerpt(content, query) {
      const source = String(content || '').replace(/\s+/g, ' ').trim();
      const matchIndex = normalized(source).indexOf(query);
      if (matchIndex < 0) return source.slice(0, 120);
      let start = Math.max(0, matchIndex - 60);
      let end = Math.min(source.length, matchIndex + query.length + 60);
      const leftBoundary = Math.max(
        source.lastIndexOf('。', start),
        source.lastIndexOf('；', start),
        source.lastIndexOf('！', start),
        source.lastIndexOf('？', start),
      );
      if (leftBoundary >= Math.max(0, matchIndex - 80)) start = leftBoundary + 1;
      const rightCandidates = ['。', '；', '！', '？']
        .map((mark) => source.indexOf(mark, end))
        .filter((position) => position >= 0 && position <= matchIndex + query.length + 80);
      if (rightCandidates.length) end = Math.min(...rightCandidates) + 1;
      if (start > 0 && /[A-Za-z0-9]/.test(source[start - 1]) && /[A-Za-z0-9]/.test(source[start])) {
        const space = source.lastIndexOf(' ', start);
        if (space >= Math.max(0, matchIndex - 80)) start = space + 1;
      }
      return `${start > 0 ? '……' : ''}${source.slice(start, end).trim()}${end < source.length ? '……' : ''}`;
    }

    function appendHighlightedText(parent, content, query) {
      const source = String(content || '');
      const haystack = normalized(source);
      let cursor = 0;
      let match = haystack.indexOf(query, cursor);
      while (match >= 0) {
        parent.appendChild(document.createTextNode(source.slice(cursor, match)));
        const mark = document.createElement('mark');
        mark.textContent = source.slice(match, match + query.length);
        parent.appendChild(mark);
        cursor = match + query.length;
        match = haystack.indexOf(query, cursor);
      }
      parent.appendChild(document.createTextNode(source.slice(cursor)));
    }

    function renderMatches(record, query) {
      const container = record.querySelector('.search-match');
      if (!container) return;
      container.replaceChildren();
      if (!query || !fullIndex || record.hidden) {
        container.hidden = true;
        return;
      }
      const matches = matchingSections(record, query);
      if (!matches.length) {
        container.hidden = true;
        return;
      }
      matches.forEach(({ section, content }) => {
        const entry = document.createElement('div');
        entry.className = 'search-match-entry';
        const location = document.createElement('p');
        location.className = 'search-match-location';
        location.appendChild(document.createTextNode('匹配于：'));
        const link = document.createElement('a');
        link.href = String(section.anchor || `nodes/${record.dataset.nodeId}.html`);
        link.textContent = String(section.label || '公开档案');
        location.appendChild(link);
        const excerpt = document.createElement('p');
        excerpt.className = 'search-match-excerpt';
        appendHighlightedText(excerpt, makeExcerpt(content, query), query);
        entry.append(location, excerpt);
        container.appendChild(entry);
      });
      container.hidden = false;
    }

    function applyFilters() {
      const query = normalized(search.value);
      if (query && !fullIndex && !indexFailed) ensureFullIndex();
      const selectedDeaths = deathOptions.filter((option) => option.checked).map((option) => option.value);
      let visible = 0;

      records.forEach((record) => {
        const deathTypes = record.dataset.deaths.split('|').filter(Boolean);
        const baseMatch = !query || normalized(record.dataset.search).includes(query);
        const fullMatch = Boolean(query && fullIndex && matchingSections(record, query).length);
        const keywordMatch = !query || (fullIndex ? (baseMatch || fullMatch) : baseMatch);
        const matches = (
          keywordMatch
          && (!filters.domain.value || record.dataset.domain === filters.domain.value)
          && (!selectedDeaths.length || selectedDeaths.some((type) => deathTypes.includes(type)))
          && (!filters.status.value || record.dataset.status === filters.status.value)
          && (!filters.archive.value || record.dataset.archive === filters.archive.value)
        );
        record.hidden = !matches;
        renderMatches(record, query);
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
      if (!query) setIndexStatus('');
      else if (indexFailed) setIndexStatus('全文索引暂不可用，当前仅搜索基础档案内容。');
      else if (indexPromise && !fullIndex) setIndexStatus('正在加载公开全文索引…');
      else setIndexStatus('');
    }

    function ensureFullIndex() {
      if (indexPromise || fullIndex || indexFailed) return;
      indexPromise = fetch('data/search-index.json').then((response) => {
        if (!response.ok) throw new Error('search index unavailable');
        return response.json();
      }).then((payload) => {
        if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
          throw new Error('invalid search index');
        }
        fullIndex = payload;
        indexPromise = null;
        applyFilters();
      }).catch(() => {
        indexPromise = null;
        indexFailed = true;
        applyFilters();
      });
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
    syncDeathControls = syncControls;

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

  const DAY_MS = 24 * 60 * 60 * 1000;

  function utcDayNumber(year, month, day) {
    const value = new Date(Date.UTC(year, month - 1, day));
    if (
      value.getUTCFullYear() !== year
      || value.getUTCMonth() !== month - 1
      || value.getUTCDate() !== day
    ) return null;
    return Math.floor(value.getTime() / DAY_MS);
  }

  function parseExpiryDay(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '');
    if (!match) return null;
    return utcDayNumber(Number(match[1]), Number(match[2]), Number(match[3]));
  }

  function daysUntilExpiry(value, now = new Date()) {
    const expiryDay = parseExpiryDay(value);
    if (expiryDay === null) return null;
    const todayDay = utcDayNumber(
      now.getFullYear(),
      now.getMonth() + 1,
      now.getDate(),
    );
    return expiryDay - todayDay;
  }

  function initExpiryStatuses(now = new Date()) {
    document.querySelectorAll('[data-expiry]').forEach((container) => {
      const days = daysUntilExpiry(container.dataset.expiry, now);
      if (days === null || days > 30) return;
      const output = document.createElement('span');
      output.className = 'expiry-status';
      output.setAttribute('aria-live', 'polite');
      if (days < 0) {
        output.textContent = `已到期 · 超过 ${Math.abs(days)} 天`;
        output.dataset.expiryState = 'expired';
      } else if (days === 0) {
        output.textContent = '今日到期';
        output.dataset.expiryState = 'due';
      } else {
        output.textContent = `临期 · 还剩 ${days} 天`;
        output.dataset.expiryState = 'due-soon';
      }
      const date = container.querySelector('time.expiry-date');
      if (date) date.insertAdjacentElement('afterend', output);
      else container.appendChild(output);
    });
  }

  function initPrint() {
    const button = document.querySelector('#print-detail');
    if (!button) return;
    let printDetailsState = null;

    function prepareDetailsForPrint() {
      if (printDetailsState) return;
      printDetailsState = new Map();
      document.querySelectorAll('.detail-layout details').forEach((element) => {
        printDetailsState.set(element, element.open);
        element.open = true;
      });
    }

    function restoreDetailsAfterPrint() {
      if (!printDetailsState) return;
      printDetailsState.forEach((wasOpen, element) => { element.open = wasOpen; });
      printDetailsState = null;
      syncDeathControls();
    }

    window.addEventListener('beforeprint', prepareDetailsForPrint);
    window.addEventListener('afterprint', restoreDetailsAfterPrint);
    const printMedia = window.matchMedia('print');
    const handleMediaChange = (event) => {
      if (event.matches) prepareDetailsForPrint();
      else restoreDetailsAfterPrint();
    };
    if (printMedia.addEventListener) printMedia.addEventListener('change', handleMediaChange);
    else printMedia.addListener(handleMediaChange);
    button.addEventListener('click', () => window.print());
    button.hidden = false;
  }

  initFilters();
  initSectionJumps();
  initDeathSections();
  initExpiryStatuses();
  initPrint();
})();
