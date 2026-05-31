document.addEventListener('DOMContentLoaded', function () {
  function csrfHeaders() {
    return {
      "Content-Type": "application/json",
      "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.content || "",
    };
  }

  // ── Search ──────────────────────────────────────────────────────────────
  const searchInput = document.getElementById('search-input');
  const kanban = document.getElementById('kanban');
  const noResults = document.getElementById('no-results');
  const wraps = kanban ? Array.from(kanban.querySelectorAll('.card-wrap')) : [];

  function applySearch() {
    const q = searchInput ? searchInput.value.trim().toLowerCase() : '';
    let visible = 0;
    wraps.forEach(w => {
      const name = w.dataset.name || '';
      const show = !q || name.includes(q);
      w.hidden = !show;
      if (show) visible++;
    });
    if (noResults) noResults.hidden = visible > 0;
  }

  if (searchInput) searchInput.addEventListener('input', applySearch);

  // ── Sort ────────────────────────────────────────────────────────────────
  const sortSelect = document.getElementById('sort-select');
  const SORT_KEY = 'pantry-sort';

  function sortGrid(mode) {
    if (!kanban) return;
    document.querySelectorAll('.kanban__col-body').forEach(col => {
      const colWraps = Array.from(col.querySelectorAll('.card-wrap'));
      colWraps.sort((a, b) => {
        // TODAY/EXPIRED items always float to top, regardless of sort mode
        const aUrgent = (a.dataset.urgency === 'today' || a.dataset.urgency === 'expired') ? 0 : 1;
        const bUrgent = (b.dataset.urgency === 'today' || b.dataset.urgency === 'expired') ? 0 : 1;
        if (aUrgent !== bUrgent) return aUrgent - bUrgent;
        if (mode === 'expiry') return a.dataset.expiry.localeCompare(b.dataset.expiry);
        if (mode === 'recent') return b.dataset.added.localeCompare(a.dataset.added);
        if (mode === 'alpha')  return a.dataset.alpha.localeCompare(b.dataset.alpha);
        return 0;
      });
      colWraps.forEach(w => col.appendChild(w));
    });
  }

  function applySort(mode) {
    sortGrid(mode);
    try { localStorage.setItem(SORT_KEY, mode); } catch (_) {}
  }

  if (sortSelect) {
    const saved = (() => { try { return localStorage.getItem(SORT_KEY); } catch (_) { return null; } })();
    if (saved && ['expiry', 'recent', 'alpha'].includes(saved)) {
      sortSelect.value = saved;
      sortGrid(saved);
    }
    sortSelect.addEventListener('change', () => applySort(sortSelect.value));
  }

  // ── Mobile location pills ────────────────────────────────────────────────
  document.querySelectorAll('.location-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.location-pill').forEach(p => p.classList.remove('location-pill--active'));
      pill.classList.add('location-pill--active');
      const loc = pill.dataset.location;
      document.querySelectorAll('.kanban__col').forEach(col => {
        col.hidden = (loc !== 'all' && col.dataset.location !== loc);
      });
    });
  });

  // ── Expiry banner: filter toggle + close ────────────────────────────────
  const expiryBanner = document.getElementById('expiry-banner');
  const filterBtn = document.getElementById('expiry-filter-btn');
  const bannerClose = document.getElementById('expiry-banner-close');
  let expiryFilterActive = false;

  function activateFilter() {
    expiryFilterActive = !expiryFilterActive;
    filterBtn.setAttribute('aria-pressed', String(expiryFilterActive));
    filterBtn.textContent = expiryFilterActive ? 'Show all' : 'Show expired only';
    wraps.forEach(w => {
      const urgency = w.dataset.urgency;
      const isExpired = urgency === 'expired' || urgency === 'today';
      w.hidden = expiryFilterActive ? !isExpired : false;
    });
    if (noResults) noResults.hidden = true;
  }

  function dismissBanner() {
    if (expiryBanner) expiryBanner.hidden = true;
    if (expiryFilterActive) {
      expiryFilterActive = false;
      wraps.forEach(w => { w.hidden = false; });
    }
  }

  if (filterBtn) {
    filterBtn.addEventListener('click', activateFilter);
    filterBtn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activateFilter(); } });
  }

  if (bannerClose) {
    bannerClose.addEventListener('click', dismissBanner);
    bannerClose.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); dismissBanner(); } });
  }

  // ── Undo toast ──────────────────────────────────────────────────────────
  const toast = document.getElementById('undo-toast');
  const countdown = document.getElementById('undo-countdown');

  if (toast && countdown) {
    let secs = 5;
    const interval = setInterval(() => {
      secs--;
      countdown.textContent = secs;
      if (secs <= 0) {
        clearInterval(interval);
        toast.classList.add('undo-toast--dismissed');
        setTimeout(() => toast.remove(), 300);
      }
    }, 1000);

    toast.addEventListener('mouseenter', () => clearInterval(interval));
    toast.addEventListener('focusin', () => clearInterval(interval));
  }

  // ── Action sheet (long-press / right-click) ──────────────────────────────
  const actionSheet = document.getElementById('action-sheet');
  const actionTitle = document.getElementById('action-sheet-title');
  const actionUseForm = document.getElementById('action-use-form');
  const actionDiscardForm = document.getElementById('action-discard-form');
  const actionUnwantedForm = document.getElementById('action-unwanted-form');
  const actionEditLink = document.getElementById('action-edit-link');

  function showActionSheet(itemId, itemName) {
    if (!actionSheet) return;
    actionTitle.textContent = itemName;
    actionUseForm.action = `/items/${itemId}/use`;
    actionDiscardForm.action = `/items/${itemId}/remove`;
    actionUnwantedForm.action = `/items/${itemId}/remove`;
    actionEditLink.href = `/items/${itemId}`;
    actionSheet.showModal();
  }

  if (actionSheet) {
    actionSheet.addEventListener('click', e => {
      if (e.target === actionSheet) actionSheet.close();
    });
  }

  let pressTimer = null;
  let longPressTriggered = false;

  document.querySelectorAll('.card-wrap').forEach(wrap => {
    const itemId = wrap.dataset.itemId;
    const itemName = wrap.dataset.itemName;

    // Long-press on mobile
    wrap.addEventListener('touchstart', () => {
      pressTimer = setTimeout(() => {
        pressTimer = null;
        longPressTriggered = true;
        showActionSheet(itemId, itemName);
      }, 600);
    }, { passive: true });

    wrap.addEventListener('touchend', () => {
      if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
    });

    wrap.addEventListener('touchmove', () => {
      if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
    }, { passive: true });

    // Right-click on desktop
    wrap.addEventListener('contextmenu', e => {
      e.preventDefault();
      showActionSheet(itemId, itemName);
    });
  });

  // ── Kanban resize grips (height + width) ───────────────────────────────
  const kanbanWrap = document.getElementById('kanban-wrap');
  const resizeGrip = document.getElementById('kanban-resize-grip');
  const widthGrip = document.getElementById('kanban-width-grip');
  const RESIZE_KEY = 'pantry-kanban-height';
  const WIDTH_KEY = 'pantry-kanban-width';

  function applyKanbanHeight(px) {
    kanbanWrap.style.height = px + 'px';
    kanbanWrap.style.flex = 'none';
    const isExpanded = px > window.innerHeight * 0.95;
    document.body.classList.toggle('body--kanban-expanded', isExpanded);
  }

  function applyKanbanWidth(px) {
    const minPx = 480;
    const maxPx = window.innerWidth - 32;
    const clamped = Math.max(minPx, Math.min(maxPx, px));
    kanbanWrap.style.width = clamped + 'px';
    kanbanWrap.style.marginLeft = '0';
    kanbanWrap.style.marginRight = '0';
  }

  if (kanbanWrap && resizeGrip) {
    const saved = (() => { try { return localStorage.getItem(RESIZE_KEY); } catch (_) { return null; } })();
    if (saved) applyKanbanHeight(Number(saved));

    const savedW = (() => { try { return localStorage.getItem(WIDTH_KEY); } catch (_) { return null; } })();
    if (savedW) applyKanbanWidth(Number(savedW));

    resizeGrip.addEventListener('mousedown', e => {
      e.preventDefault();
      const startY = e.clientY;
      const startH = kanbanWrap.getBoundingClientRect().height;

      function onMove(e) {
        const h = Math.max(200, startH + (e.clientY - startY));
        applyKanbanHeight(h);
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        const h = Math.round(kanbanWrap.getBoundingClientRect().height);
        try { localStorage.setItem(RESIZE_KEY, h); } catch (_) {}
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    resizeGrip.addEventListener('dblclick', () => {
      kanbanWrap.style.height = '';
      kanbanWrap.style.flex = '';
      document.body.classList.remove('body--kanban-expanded');
      try { localStorage.removeItem(RESIZE_KEY); } catch (_) {}
    });
  }

  if (kanbanWrap && widthGrip) {
    widthGrip.addEventListener('mousedown', e => {
      e.preventDefault();
      const startX = e.clientX;
      const startW = kanbanWrap.getBoundingClientRect().width;

      function onMove(e) {
        applyKanbanWidth(startW + (e.clientX - startX));
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        const w = Math.round(kanbanWrap.getBoundingClientRect().width);
        try { localStorage.setItem(WIDTH_KEY, w); } catch (_) {}
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    widthGrip.addEventListener('dblclick', () => {
      kanbanWrap.style.width = '';
      kanbanWrap.style.marginLeft = '';
      kanbanWrap.style.marginRight = '';
      try { localStorage.removeItem(WIDTH_KEY); } catch (_) {}
    });
  }

  // ── Drag-and-drop between columns (SortableJS) ──────────────────────────
  // Disabled on mobile: single-column view means there's nowhere to drag to,
  // and the touch handler conflicts with native scroll.
  const isMobile = window.matchMedia('(max-width: 767px)').matches;
  if (kanban && typeof Sortable !== 'undefined' && !isMobile) {
    function updateColCount(col) {
      const count = col.querySelectorAll('.card-wrap:not([hidden])').length;
      const badge = col.querySelector('.kanban__col-count');
      if (badge) badge.textContent = count;
    }

    kanban.querySelectorAll('.kanban__col-body').forEach(body => {
      new Sortable(body, {
        group: 'kanban',
        animation: 150,
        draggable: '.card-wrap',
        ghostClass: 'card-wrap--dragging',
        chosenClass: 'card-wrap--chosen',
        onEnd(evt) {
          if (evt.from === evt.to) return;
          const card = evt.item;
          const targetCol = evt.to.closest('.kanban__col');
          const targetLoc = targetCol?.dataset.location;
          const groupIds = (card.dataset.groupIds || '').split(',').map(Number).filter(Boolean);
          if (!groupIds.length || !targetLoc) return;
          card.dataset.location = targetLoc;
          updateColCount(evt.from.closest('.kanban__col'));
          updateColCount(targetCol);
          fetch('/items/move-group', {
            method: 'POST',
            headers: csrfHeaders(),
            body: JSON.stringify({ item_ids: groupIds, location: targetLoc }),
          }).then(res => {
            if (!res.ok) {
              evt.from.insertBefore(card, evt.from.children[evt.oldIndex] || null);
              card.dataset.location = evt.from.closest('.kanban__col')?.dataset.location || '';
              updateColCount(evt.from.closest('.kanban__col'));
              updateColCount(targetCol);
            }
          });
        },
      });
    });
  }
});
