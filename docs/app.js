// CortexRadar Client-Side Interactive Dashboard
(function () {
  'use strict';

  let allItems = [];
  let currentSource = 'all';
  let currentCategory = 'all';
  let currentSort = 'score';
  let searchQuery = '';
  let bookmarks = new Set(JSON.parse(localStorage.getItem('cortex_bookmarks') || '[]'));

  // Elements
  const itemsGrid = document.getElementById('itemsGrid');
  const searchInput = document.getElementById('searchInput');
  const clearSearchBtn = document.getElementById('clearSearchBtn');
  const sourceFilters = document.getElementById('sourceFilters');
  const categoryPills = document.getElementById('categoryPills');
  const sortSelect = document.getElementById('sortSelect');
  const resultsCount = document.getElementById('resultsCount');
  const bookmarkCountSpan = document.getElementById('bookmarkCount');
  const themeToggle = document.getElementById('themeToggle');
  const statTotal = document.getElementById('statTotal');
  const statPapers = document.getElementById('statPapers');
  const statRepos = document.getElementById('statRepos');
  const statLastSync = document.getElementById('statLastSync');
  const exportCsvBtn = document.getElementById('exportCsvBtn');
  const toast = document.getElementById('toast');

  // Initialize
  initTheme();
  fetchData();
  bindEvents();

  function initTheme() {
    const savedTheme = localStorage.getItem('cortex_theme') || 'dark';
    if (savedTheme === 'light') {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
    }
  }

  function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    if (isDark) {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
      localStorage.setItem('cortex_theme', 'light');
    } else {
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
      localStorage.setItem('cortex_theme', 'dark');
    }
  }

  async function fetchData() {
    // Attempt to load from relative docs/data/master_dataset.json or fallback
    const paths = ['data/master_dataset.json', '../data/master_dataset.json'];
    let loaded = false;

    for (const path of paths) {
      try {
        const resp = await fetch(path);
        if (resp.ok) {
          allItems = await resp.json();
          loaded = true;
          break;
        }
      } catch (e) {
        // Continue trying next path
      }
    }

    if (!loaded) {
      renderErrorState("Could not load master dataset. Ensure data/master_dataset.json exists.");
      return;
    }

    updateStats();
    buildCategoryPills();
    render();
  }

  function updateStats() {
    const total = allItems.length;
    const papers = allItems.filter(i => i.source === 'arxiv').length;
    const repos = allItems.filter(i => i.source === 'github').length;
    const dates = allItems.map(i => i.discovered_date).filter(Boolean);
    const latestDate = dates.length > 0 ? dates[0] : 'Today';

    statTotal.textContent = total;
    statPapers.textContent = papers;
    statRepos.textContent = repos;
    statLastSync.textContent = latestDate;
    bookmarkCountSpan.textContent = bookmarks.size;
  }

  function buildCategoryPills() {
    const catMap = new Map();
    allItems.forEach(item => {
      if (item.primary_category && item.category_badge) {
        catMap.set(item.primary_category, item.category_badge);
      }
    });

    categoryPills.innerHTML = '<button class="pill-btn active" data-category="all">✨ All Domains</button>';
    catMap.forEach((badge, catId) => {
      const btn = document.createElement('button');
      btn.className = 'pill-btn';
      btn.dataset.category = catId;
      btn.textContent = badge;
      categoryPills.appendChild(btn);
    });
  }

  function bindEvents() {
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);

    // Search
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      clearSearchBtn.style.display = searchQuery ? 'block' : 'none';
      render();
    });

    clearSearchBtn.addEventListener('click', () => {
      searchInput.value = '';
      searchQuery = '';
      clearSearchBtn.style.display = 'none';
      render();
    });

    // Keyboard shortcut '/'
    window.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
    });

    // Source segment control
    sourceFilters.addEventListener('click', (e) => {
      const btn = e.target.closest('.segment-btn');
      if (!btn) return;
      document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSource = btn.dataset.source;
      render();
    });

    // Category pills
    categoryPills.addEventListener('click', (e) => {
      const btn = e.target.closest('.pill-btn');
      if (!btn) return;
      document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.dataset.category;
      render();
    });

    // Sort
    sortSelect.addEventListener('change', (e) => {
      currentSort = e.target.value;
      render();
    });

    // Export CSV
    exportCsvBtn.addEventListener('click', exportFilteredCsv);
  }

  function getFilteredItems() {
    return allItems.filter(item => {
      // Source filter
      if (currentSource === 'arxiv' && item.source !== 'arxiv') return false;
      if (currentSource === 'github' && item.source !== 'github') return false;
      if (currentSource === 'bookmarked' && !bookmarks.has(item.id)) return false;

      // Category filter
      if (currentCategory !== 'all' && item.primary_category !== currentCategory) return false;

      // Search query
      if (searchQuery) {
        const text = `${item.title} ${item.authors_or_owner} ${item.summary} ${item.tl_dr} ${(item.tags || []).join(' ')}`.toLowerCase();
        if (!text.includes(searchQuery)) return false;
      }

      return true;
    }).sort((a, b) => {
      if (currentSort === 'score') return (b.score || 0) - (a.score || 0);
      if (currentSort === 'stars') return (b.stars || 0) - (a.stars || 0);
      if (currentSort === 'newest') return (b.published_date || '').localeCompare(a.published_date || '');
      return 0;
    });
  }

  function render() {
    const items = getFilteredItems();
    resultsCount.textContent = `Showing ${items.length} ${items.length === 1 ? 'discovery' : 'discoveries'}`;

    if (items.length === 0) {
      itemsGrid.innerHTML = `
        <div class="empty-state">
          <h3>No discoveries found</h3>
          <p>Try clearing your search query or switching filters.</p>
        </div>
      `;
      return;
    }

    itemsGrid.innerHTML = items.map(item => createCardHTML(item)).join('');

    // Attach bookmark and copy handlers
    itemsGrid.querySelectorAll('.bookmark-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        toggleBookmark(id);
      });
    });

    itemsGrid.querySelectorAll('.copy-link-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const url = e.currentTarget.dataset.url;
        const title = e.currentTarget.dataset.title;
        copyMarkdown(title, url);
      });
    });
  }

  function createCardHTML(item) {
    const isBookmarked = bookmarks.has(item.id);
    const starDisplay = item.source === 'github' && item.stars !== null
      ? `⭐ ${item.stars >= 1000 ? (item.stars / 1000).toFixed(1) + 'k' : item.stars}`
      : `⚡ ${item.score.toFixed(1)}`;

    const tagsHTML = (item.tags || []).slice(0, 4)
      .map(t => `<span class="tag-chip">#${escapeHTML(t)}</span>`).join('');

    const pdfBtn = (item.metadata && item.metadata.pdf_url)
      ? `<a href="${item.metadata.pdf_url}" target="_blank" rel="noopener" class="action-btn">📄 View PDF</a>`
      : '';

    return `
      <article class="card" data-id="${escapeHTML(item.id)}">
        <div class="card-header">
          <span class="badge">${escapeHTML(item.category_badge || 'AI')}</span>
          <div class="card-header-right">
            <span class="score-badge">${starDisplay}</span>
            <button class="bookmark-btn ${isBookmarked ? 'bookmarked' : ''}" data-id="${escapeHTML(item.id)}" title="${isBookmarked ? 'Remove Bookmark' : 'Bookmark Item'}">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="${isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
          </div>
        </div>

        <h3 class="card-title">
          <a href="${escapeHTML(item.url)}" target="_blank" rel="noopener">${escapeHTML(item.title)}</a>
        </h3>

        <div class="card-authors">
          ${item.source === 'arxiv' ? 'By ' + escapeHTML(item.authors_or_owner) : 'Owner: ' + escapeHTML(item.authors_or_owner)}
          ${item.language ? ' &bull; ' + escapeHTML(item.language) : ''}
        </div>

        <div class="card-tldr">
          <strong>TL;DR:</strong> ${escapeHTML(item.tl_dr || item.summary)}
        </div>

        <details class="card-details">
          <summary>Full Abstract & Insights</summary>
          <p>${escapeHTML(item.summary)}</p>
        </details>

        <div class="card-tags">
          ${tagsHTML}
        </div>

        <div class="card-actions">
          <a href="${escapeHTML(item.url)}" target="_blank" rel="noopener" class="action-btn">
            ${item.source === 'arxiv' ? 'arXiv Abstract' : 'View GitHub Repo'}
          </a>
          ${pdfBtn}
          <button class="action-btn copy-link-btn" data-url="${escapeHTML(item.url)}" data-title="${escapeHTML(item.title)}">
            📋 Copy Link
          </button>
        </div>
      </article>
    `;
  }

  function toggleBookmark(id) {
    if (bookmarks.has(id)) {
      bookmarks.delete(id);
      showToast("Removed from bookmarks");
    } else {
      bookmarks.add(id);
      showToast("Added to bookmarks!");
    }
    localStorage.setItem('cortex_bookmarks', JSON.stringify(Array.from(bookmarks)));
    bookmarkCountSpan.textContent = bookmarks.size;
    render();
  }

  function copyMarkdown(title, url) {
    const md = `[${title}](${url})`;
    navigator.clipboard.writeText(md).then(() => {
      showToast("Copied Markdown link to clipboard!");
    }).catch(() => {
      showToast("Link: " + url);
    });
  }

  function exportFilteredCsv() {
    const items = getFilteredItems();
    if (items.length === 0) {
      showToast("No items to export");
      return;
    }

    const headers = ["id", "source", "title", "url", "authors_or_owner", "category", "stars", "score", "tl_dr"];
    const rows = items.map(i => [
      i.id,
      i.source,
      `"${(i.title || '').replace(/"/g, '""')}"`,
      i.url,
      `"${(i.authors_or_owner || '').replace(/"/g, '""')}"`,
      i.primary_category,
      i.stars || '',
      i.score,
      `"${(i.tl_dr || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `cortex_radar_export_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("Downloaded CSV dataset!");
  }

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  function renderErrorState(msg) {
    itemsGrid.innerHTML = `
      <div class="empty-state">
        <h3>Initialization Notice</h3>
        <p>${escapeHTML(msg)}</p>
      </div>
    `;
  }

  function escapeHTML(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
})();
