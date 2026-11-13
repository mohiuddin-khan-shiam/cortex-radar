"""Generates and updates the client-side static web dashboard in docs/."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..config import RadarAppConfig

logger = logging.getLogger("cortex_radar.site_builder")


INDEX_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CortexRadar | Daily AI, ML & Dev Tools Intelligence Hub</title>
  <meta name="description" content="Autonomous daily intelligence radar tracking breakthrough AI/ML research papers from arXiv and high-velocity open-source repositories from GitHub.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body class="dark-theme">
  <!-- Top Navigation & Header -->
  <header class="site-header">
    <div class="header-container">
      <div class="brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
          </svg>
        </div>
        <div class="brand-text">
          <h1>Cortex<span>Radar</span></h1>
          <p class="tagline">Daily AI Breakthroughs & Trending Developer Tools</p>
        </div>
      </div>

      <div class="header-actions">
        <button id="themeToggle" class="btn-icon" title="Toggle Light/Dark Theme" aria-label="Toggle Theme">
          <svg id="themeIcon" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
        </button>
        <a id="githubRepoLink" href="https://github.com/cortexradar/cortex-radar" target="_blank" rel="noopener" class="btn btn-secondary">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          <span>Star on GitHub</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Metric Badges Strip -->
  <section class="stats-strip">
    <div class="stats-container">
      <div class="stat-card">
        <span class="stat-label">Total Discoveries</span>
        <span id="statTotal" class="stat-value">--</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Research Preprints</span>
        <span id="statPapers" class="stat-value">--</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Trending Repos</span>
        <span id="statRepos" class="stat-value">--</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Last Synchronized</span>
        <span id="statLastSync" class="stat-value">--</span>
      </div>
    </div>
  </section>

  <!-- Controls: Search, Source Filter, Categories, Sort -->
  <main class="main-content">
    <div class="controls-wrapper">
      <div class="search-box">
        <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input type="text" id="searchInput" placeholder="Search by model, keyword, author, paper, or repo... (Press '/' to focus)" aria-label="Search items">
        <button id="clearSearchBtn" class="clear-btn" style="display:none;" title="Clear search">&times;</button>
      </div>

      <div class="filter-row">
        <!-- Source Segmented Control -->
        <div class="segmented-control" id="sourceFilters">
          <button class="segment-btn active" data-source="all">All Items</button>
          <button class="segment-btn" data-source="arxiv">📄 arXiv Papers</button>
          <button class="segment-btn" data-source="github">⭐ GitHub Repos</button>
          <button class="segment-btn" data-source="bookmarked">🔖 Bookmarks (<span id="bookmarkCount">0</span>)</button>
        </div>

        <!-- Sort Selector -->
        <div class="sort-wrapper">
          <label for="sortSelect">Sort:</label>
          <select id="sortSelect">
            <option value="score">Highest Signal Score</option>
            <option value="stars">Most Stars</option>
            <option value="newest">Newest Discovered</option>
          </select>
        </div>
      </div>

      <!-- Category Filter Pills -->
      <div class="category-pills" id="categoryPills">
        <button class="pill-btn active" data-category="all">✨ All Domains</button>
        <!-- Populated dynamically via app.js -->
      </div>
    </div>

    <!-- Results Status Bar -->
    <div class="results-meta">
      <span id="resultsCount">Showing 0 items</span>
      <button id="exportCsvBtn" class="btn-link">📥 Download CSV</button>
    </div>

    <!-- Items Grid Container -->
    <div class="items-grid" id="itemsGrid">
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading CortexRadar intelligence feed...</p>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="site-footer">
    <div class="footer-container">
      <p>Powered by <strong>CortexRadar</strong> &bull; Automated Daily Open-Source Radar</p>
      <p>Data ingested daily from arXiv.org & GitHub API under MIT License.</p>
    </div>
  </footer>

  <!-- Notification Toast -->
  <div id="toast" class="toast" role="alert" aria-live="polite"></div>

  <script src="app.js"></script>
</body>
</html>
"""

STYLE_CSS_CONTENT = """/* CortexRadar Modern Design System */
:root {
  --bg-primary: #0a0e17;
  --bg-secondary: #111827;
  --bg-card: #161f30;
  --bg-card-hover: #1c273c;
  --bg-input: #1f293d;
  --border-color: #27354f;
  --border-focus: #6366f1;
  --text-primary: #f3f4f6;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent-primary: #6366f1;
  --accent-secondary: #8b5cf6;
  --accent-glow: rgba(99, 102, 241, 0.25);
  --badge-arxiv: #3b82f6;
  --badge-github: #eab308;
  --success: #10b981;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --shadow-card: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
  --shadow-hover: 0 8px 30px -4px rgba(99, 102, 241, 0.2);
}

body.light-theme {
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-card-hover: #f1f5f9;
  --bg-input: #f1f5f9;
  --border-color: #e2e8f0;
  --border-focus: #4f46e5;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --accent-primary: #4f46e5;
  --accent-secondary: #7c3aed;
  --accent-glow: rgba(79, 70, 229, 0.15);
  --shadow-card: 0 4px 15px -2px rgba(0, 0, 0, 0.05);
  --shadow-hover: 0 8px 25px -4px rgba(79, 70, 229, 0.12);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
  line-height: 1.5;
  transition: background-color 0.3s ease, color 0.3s ease;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.site-header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(12px);
}

.header-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.brand-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 0 20px var(--accent-glow);
}

.brand-text h1 {
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.brand-text h1 span {
  background: linear-gradient(135deg, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-text .tagline {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-icon {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: var(--radius-md);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--bg-card-hover);
  border-color: var(--accent-primary);
}

/* Stats Strip */
.stats-strip {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 1.25rem 0;
}

.stats-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-mono);
  margin-top: 0.2rem;
}

/* Main Content */
.main-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  flex: 1;
  width: 100%;
}

.controls-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

/* Search Box */
.search-box {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 1.1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.search-box input {
  width: 100%;
  padding: 0.95rem 2.8rem 0.95rem 3rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.95rem;
  outline: none;
  transition: all 0.2s;
}

.search-box input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.clear-btn {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.4rem;
  cursor: pointer;
}

/* Filter Row */
.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.segmented-control {
  display: inline-flex;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.25rem;
  gap: 0.25rem;
}

.segment-btn {
  background: transparent;
  border: none;
  padding: 0.45rem 0.9rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.segment-btn:hover {
  color: var(--text-primary);
}

.segment-btn.active {
  background: var(--accent-primary);
  color: #ffffff;
}

.sort-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.sort-wrapper select {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0.45rem 0.8rem;
  border-radius: var(--radius-md);
  outline: none;
  font-size: 0.85rem;
  cursor: pointer;
}

/* Category Pills */
.category-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-top: 0.5rem;
}

.pill-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
}

.pill-btn:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.pill-btn.active {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  font-weight: 600;
}

/* Results Meta */
.results-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.btn-link {
  background: none;
  border: none;
  color: var(--accent-primary);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: underline;
}

/* Items Grid */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1.25rem;
}

/* Discovery Card */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-card);
  position: relative;
}

.card:hover {
  transform: translateY(-3px);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: var(--shadow-hover);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.85rem;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-sm);
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-primary);
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-badge {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  background: rgba(16, 185, 129, 0.15);
  color: var(--success);
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-sm);
}

.bookmark-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0.25rem;
  transition: color 0.2s;
}

.bookmark-btn:hover, .bookmark-btn.bookmarked {
  color: #f59e0b;
}

.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.card-title a {
  color: var(--text-primary);
  text-decoration: none;
  transition: color 0.2s;
}

.card-title a:hover {
  color: var(--accent-primary);
}

.card-authors {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
  font-style: italic;
}

.card-tldr {
  background: var(--bg-primary);
  border-left: 3px solid var(--accent-primary);
  padding: 0.65rem 0.85rem;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.45;
  margin-bottom: 0.85rem;
}

.card-tldr strong {
  color: var(--text-primary);
}

.card-details {
  font-size: 0.825rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.card-details summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--text-secondary);
  outline: none;
  user-select: none;
}

.card-details summary:hover {
  color: var(--text-primary);
}

.card-details p {
  margin-top: 0.5rem;
  line-height: 1.5;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.tag-chip {
  font-size: 0.7rem;
  font-family: var(--font-mono);
  background: var(--bg-input);
  color: var(--text-secondary);
  padding: 0.15rem 0.45rem;
  border-radius: var(--radius-sm);
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.85rem;
}

.action-btn {
  flex: 1;
  text-align: center;
  padding: 0.45rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
  text-decoration: none;
  cursor: pointer;
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #ffffff;
}

/* Loading & Empty State */
.loading-state, .empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem 1rem;
  color: var(--text-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Toast */
.toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: var(--bg-card);
  border: 1px solid var(--accent-primary);
  color: var(--text-primary);
  padding: 0.75rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 100;
}

.toast.show {
  transform: translateY(0);
  opacity: 1;
}

/* Footer */
.site-footer {
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  padding: 1.5rem 0;
  margin-top: auto;
  text-align: center;
  font-size: 0.825rem;
  color: var(--text-muted);
}

.footer-container p {
  margin: 0.25rem 0;
}
"""

APP_JS_CONTENT = """// CortexRadar Client-Side Interactive Dashboard
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

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(e => e.join(','))].join('\\n');
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
"""


class SiteBuilder:
    """Builds and refreshes the docs/ static web application assets."""

    def __init__(self, config: Optional[RadarAppConfig] = None):
        self.config = config or RadarAppConfig()
        self.docs_dir = Path(self.config.output.docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def build_site(self) -> None:
        """Write index.html, style.css, and app.js into docs/."""
        html_path = self.docs_dir / "index.html"
        css_path = self.docs_dir / "style.css"
        js_path = self.docs_dir / "app.js"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(INDEX_HTML_TEMPLATE)

        with open(css_path, "w", encoding="utf-8") as f:
            f.write(STYLE_CSS_CONTENT)

        with open(js_path, "w", encoding="utf-8") as f:
            f.write(APP_JS_CONTENT)

        logger.info(f"[SiteBuilder] Static dashboard files generated in {self.docs_dir}")
