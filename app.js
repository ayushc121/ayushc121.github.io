/* ============================================================
   app.js — Portfolio site logic
   Reads projects.json, builds the page, handles filtering + modal.
   ============================================================ */

'use strict';

const DATA_URL = 'projects.json';

let allProjects = [];
let activeFilter = 'All';

/* ============================================================
   BOOT
   ============================================================ */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    allProjects = data.projects ?? [];
    const portfolio = data.portfolio ?? {};

    renderHeader(portfolio);
    renderHero(portfolio);
    renderFilters(allProjects);
    renderGrid(allProjects);
    renderFooter(portfolio);
    setupModal();
  } catch (err) {
    console.error('Could not load projects.json:', err);
    document.getElementById('projects-grid').innerHTML =
      `<p style="padding:2rem 0;font-family:monospace;font-size:0.8rem;color:#888;grid-column:1/-1">
         Could not load <strong>projects.json</strong>. Make sure the file exists alongside index.html.
       </p>`;
  }
});

/* ============================================================
   HEADER
   ============================================================ */
function renderHeader(p) {
  setEl('page-title', `${p.name ?? 'Portfolio'} — Projects`);
  setEl('header-name', p.name ?? '');
  setHref('header-linkedin', p.linkedin, true);

  // Hide PDF link if portfolio.pdf doesn't exist (can't detect easily, keep it)
}

/* ============================================================
   HERO
   ============================================================ */
function renderHero(p) {
  setEl('hero-name', p.name ?? '');
  setEl('hero-tagline', p.tagline ?? '');
  setHref('hero-linkedin', p.linkedin, true);
  setHref('hero-github', p.github, true);
}

/* ============================================================
   FOOTER
   ============================================================ */
function renderFooter(p) {
  setEl('footer-copy', `© ${new Date().getFullYear()} ${p.name ?? ''}`);
  setHref('footer-linkedin', p.linkedin, true);

  const emailEl = document.getElementById('footer-email');
  if (p.email && emailEl) {
    emailEl.href = `mailto:${p.email}`;
    emailEl.textContent = p.email;
  } else if (emailEl) {
    emailEl.remove();
  }
}

/* ============================================================
   FILTERS
   ============================================================ */
function renderFilters(projects) {
  const allTags = new Set();
  projects.forEach(p => (p.tags ?? []).forEach(t => allTags.add(t)));

  const bar = document.getElementById('filter-bar');
  bar.innerHTML = '';
  bar.appendChild(makeFilterBtn('All', true));
  [...allTags].sort().forEach(tag => bar.appendChild(makeFilterBtn(tag, false)));
}

function makeFilterBtn(label, isActive) {
  const btn = document.createElement('button');
  btn.className = 'filter-btn' + (isActive ? ' active' : '');
  btn.textContent = label;
  btn.addEventListener('click', () => {
    activeFilter = label;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterGrid();
  });
  return btn;
}

function filterGrid() {
  document.querySelectorAll('.project-card').forEach(card => {
    const tags = JSON.parse(card.dataset.tags ?? '[]');
    const visible = activeFilter === 'All' || tags.includes(activeFilter);
    card.classList.toggle('hidden', !visible);
  });
}

/* ============================================================
   GRID
   ============================================================ */
function renderGrid(projects) {
  const grid = document.getElementById('projects-grid');
  grid.innerHTML = '';
  projects.forEach((proj, i) => grid.appendChild(makeCard(proj, i)));
}

function makeCard(proj, index) {
  const card = document.createElement('article');
  card.className = 'project-card';
  card.dataset.id = proj.id ?? index;
  card.dataset.tags = JSON.stringify(proj.tags ?? []);
  card.setAttribute('tabindex', '0');
  card.setAttribute('role', 'button');
  card.setAttribute('aria-label', `Open ${proj.title}`);

  const annotation = formatAnnotation(index);
  const thumbSrc = proj.hero ?? firstImageSrc(proj);

  card.innerHTML = `
    <div class="card-annotation">
      <span>${annotation}</span>
    </div>
    ${thumbSrc
      ? `<img class="card-hero" src="${thumbSrc}" alt="${escHtml(proj.title)}" loading="lazy" />`
      : `<div class="card-hero-placeholder"></div>`
    }
    <h2 class="card-title">${escHtml(proj.title)}</h2>
    <p class="card-summary">${escHtml(proj.summary ?? proj.description ?? '')}</p>
    <div class="card-footer">
      <div class="card-tags">
        ${(proj.tags ?? []).map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}
      </div>
      <span class="card-open-hint">${proj.date ? proj.date + ' ·' : ''} View ↗</span>
    </div>
  `;

  const open = () => openModal(proj, index);
  card.addEventListener('click', open);
  card.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }});

  return card;
}

/* ============================================================
   MODAL
   ============================================================ */
function setupModal() {
  const overlay = document.getElementById('modal-overlay');
  const closeBtn = document.getElementById('modal-close');

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
}

function openModal(proj, index) {
  const body = document.getElementById('modal-body');
  const overlay = document.getElementById('modal-overlay');

  const annotation = formatAnnotation(index);
  const heroSrc = proj.hero ?? firstImageSrc(proj);
  const heroCandidateSrc = proj.hero;

  // Media items: exclude the hero image from the media grid to avoid duplication
  const mediaItems = (proj.media ?? []).filter(m =>
    !(m.type === 'image' && m.src === heroCandidateSrc)
  );

  const links = proj.links ?? {};

  body.innerHTML = `
    <div class="modal-eyebrow">
      <span>${annotation}</span>
      <span>${escHtml(proj.date ?? '')}</span>
    </div>
    <h2 class="modal-title">${escHtml(proj.title)}</h2>
    <div class="modal-tags">
      ${(proj.tags ?? []).map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}
    </div>
    ${heroSrc ? `<img class="modal-hero" src="${heroSrc}" alt="${escHtml(proj.title)}" />` : ''}
    <div class="modal-description">${formatDescription(proj.description ?? '')}</div>
    ${renderMediaGrid(mediaItems)}
    ${renderLinks(links)}
  `;

  overlay.setAttribute('aria-hidden', 'false');
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';

  // Focus close button for keyboard users
  document.getElementById('modal-close').focus();
}

function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('open');
  overlay.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  // Clear modal after transition to stop video playback
  setTimeout(() => {
    const body = document.getElementById('modal-body');
    if (body) body.innerHTML = '';
  }, 260);
}

function renderMediaGrid(items) {
  if (!items || items.length === 0) return '';

  const cells = items.map(item => {
    if (item.type === 'image') {
      return `
        <div class="modal-media-item">
          <img src="${item.src}" alt="${escHtml(item.caption ?? '')}" loading="lazy" />
          ${item.caption ? `<p class="media-caption">${escHtml(item.caption)}</p>` : ''}
        </div>`;
    }

    if (item.type === 'youtube') {
      return `
        <div class="modal-media-item">
          <div class="video-wrap">
            <iframe
              src="https://www.youtube.com/embed/${item.id}"
              title="${escHtml(item.caption ?? 'YouTube video')}"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
              loading="lazy">
            </iframe>
          </div>
          ${item.caption ? `<p class="media-caption">${escHtml(item.caption)}</p>` : ''}
        </div>`;
    }

    if (item.type === 'vimeo') {
      return `
        <div class="modal-media-item">
          <div class="video-wrap">
            <iframe
              src="https://player.vimeo.com/video/${item.id}"
              title="${escHtml(item.caption ?? 'Vimeo video')}"
              allow="autoplay; fullscreen; picture-in-picture"
              allowfullscreen
              loading="lazy">
            </iframe>
          </div>
          ${item.caption ? `<p class="media-caption">${escHtml(item.caption)}</p>` : ''}
        </div>`;
    }

    return '';
  }).filter(Boolean);

  if (cells.length === 0) return '';
  return `<div class="modal-media-grid">${cells.join('\n')}</div>`;
}

function renderLinks(links) {
  const LABELS = {
    github:  'GitHub ↗',
    demo:    'Live Demo ↗',
    video:   'Video ↗',
    paper:   'Paper ↗',
    report:  'Report ↗',
    website: 'Website ↗',
  };

  const entries = Object.entries(links).filter(([, v]) => v);
  if (entries.length === 0) return '';

  const btns = entries
    .map(([k, url]) => `<a class="modal-link" href="${url}" target="_blank" rel="noopener noreferrer">${LABELS[k] ?? (k + ' ↗')}</a>`)
    .join('');

  return `<div class="modal-links">${btns}</div>`;
}

/* ============================================================
   HELPERS
   ============================================================ */
function formatAnnotation(index) {
  return `P.${String(index + 1).padStart(3, '0')}`;
}

function firstImageSrc(proj) {
  return (proj.media ?? []).find(m => m.type === 'image')?.src ?? null;
}

function formatDescription(text) {
  return text
    .split(/\n{2,}/)
    .map(p => p.trim())
    .filter(Boolean)
    .map(p => {
      // Escape HTML first, then apply **bold** markdown
      let html = escHtml(p);
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      return `<p>${html}</p>`;
    })
    .join('');
}

function setEl(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setHref(id, url, hideIfEmpty = false) {
  const el = document.getElementById(id);
  if (!el) return;
  if (url) {
    el.href = url;
  } else if (hideIfEmpty) {
    el.style.display = 'none';
  }
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
