const previewInputs = document.querySelectorAll('[data-preview-target]');
previewInputs.forEach((input) => {
  const target = document.querySelector(input.dataset.previewTarget);
  if (!target) return;
  const render = () => {
    target.textContent = input.value || 'Start typing to preview content...';
  };
  input.addEventListener('input', render);
  render();
});

const uploadForm = document.getElementById('upload-form');
if (uploadForm) {
  const fileInput = uploadForm.querySelector('input[type="file"]');
  uploadForm.addEventListener('dragover', (event) => {
    event.preventDefault();
    uploadForm.classList.add('dragging');
  });
  uploadForm.addEventListener('dragleave', () => uploadForm.classList.remove('dragging'));
  uploadForm.addEventListener('drop', (event) => {
    event.preventDefault();
    uploadForm.classList.remove('dragging');
    fileInput.files = event.dataTransfer.files;
  });
}

const menuToggle = document.getElementById('menu-toggle');
const publicNav = document.getElementById('public-nav');
if (menuToggle && publicNav) {
  menuToggle.addEventListener('click', () => publicNav.classList.toggle('open'));
}

const eventGrid = document.getElementById('event-grid');
const searchInput = document.getElementById('event-search');
const categoryFilter = document.getElementById('event-category-filter');
const sortSelect = document.getElementById('event-sort');

function filterPublicEvents() {
  if (!eventGrid) return;
  const cards = Array.from(eventGrid.querySelectorAll('.event-card'));
  const searchValue = (searchInput?.value || '').toLowerCase().trim();
  const categoryValue = categoryFilter?.value || '';
  const sortValue = sortSelect?.value || 'asc';

  cards.forEach((card) => {
    const matchesSearch = card.dataset.title.includes(searchValue);
    const matchesCategory = !categoryValue || card.dataset.category === categoryValue;
    card.style.display = matchesSearch && matchesCategory ? 'block' : 'none';
  });

  cards.sort((a, b) => {
    const firstDate = new Date(a.dataset.date);
    const secondDate = new Date(b.dataset.date);
    return sortValue === 'asc' ? firstDate - secondDate : secondDate - firstDate;
  });

  cards.forEach((card) => eventGrid.appendChild(card));
}

[searchInput, categoryFilter, sortSelect].forEach((node) => {
  if (node) {
    node.addEventListener('input', filterPublicEvents);
    node.addEventListener('change', filterPublicEvents);
  }
});

const lightbox = document.getElementById('lightbox');
const lightboxContent = document.getElementById('lightbox-content');
const lightboxClose = document.getElementById('lightbox-close');
const galleryThumbs = document.querySelectorAll('[data-lightbox-src]');

function closeLightbox() {
  if (!lightbox || !lightboxContent) return;
  lightbox.classList.add('hidden');
  lightboxContent.innerHTML = '';
}

if (lightbox && lightboxContent) {
  galleryThumbs.forEach((thumb) => {
    thumb.addEventListener('click', () => {
      const src = thumb.dataset.lightboxSrc;
      const type = thumb.dataset.lightboxType;
      if (!src) return;
      if (type === 'video') {
        lightboxContent.innerHTML = `<video controls autoplay><source src="${src}"></video>`;
      } else {
        lightboxContent.innerHTML = `<img src="${src}" alt="Gallery item">`;
      }
      lightbox.classList.remove('hidden');
    });
  });

  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) closeLightbox();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeLightbox();
  });
}

if (lightboxClose) {
  lightboxClose.addEventListener('click', closeLightbox);
}


const blogGrid = document.getElementById('blog-grid');
const blogSearch = document.getElementById('blog-search');
const blogCategoryFilter = document.getElementById('blog-category-filter');

function filterBlogPosts() {
  if (!blogGrid) return;
  const cards = Array.from(blogGrid.querySelectorAll('.blog-card'));
  const keyword = (blogSearch?.value || '').toLowerCase().trim();
  const category = blogCategoryFilter?.value || '';

  cards.forEach((card) => {
    const matchesKeyword = card.dataset.title.includes(keyword);
    const matchesCategory = !category || card.dataset.category === category;
    card.style.display = matchesKeyword && matchesCategory ? 'block' : 'none';
  });
}

[blogSearch, blogCategoryFilter].forEach((node) => {
  if (node) {
    node.addEventListener('input', filterBlogPosts);
    node.addEventListener('change', filterBlogPosts);
  }
});


const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', (event) => {
    const name = document.getElementById('contact-name')?.value.trim() || '';
    const email = document.getElementById('contact-email')?.value.trim() || '';
    const message = document.getElementById('contact-message')?.value.trim() || '';
    const errorEl = document.getElementById('contact-error');

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    let errorText = '';
    if (!name || !email || !message) {
      errorText = 'Please fill in name, email, and message.';
    } else if (!emailPattern.test(email)) {
      errorText = 'Please provide a valid email address.';
    }

    if (errorText) {
      event.preventDefault();
      if (errorEl) errorEl.textContent = errorText;
    } else if (errorEl) {
      errorEl.textContent = '';
    }
  });
}


const publicGalleryGrid = document.getElementById('public-gallery-grid');
const galleryTypeFilter = document.getElementById('gallery-type-filter');
const galleryLinkedFilter = document.getElementById('gallery-linked-filter');
const galleryCategoryFilter = document.getElementById('gallery-category-filter');
const galleryEventFilter = document.getElementById('gallery-event-filter');
const galleryLoadMore = document.getElementById('gallery-load-more');

let visibleGalleryCount = 12;

function applyPublicGalleryFilters() {
  if (!publicGalleryGrid) return;
  const items = Array.from(publicGalleryGrid.querySelectorAll('.public-gallery-item'));
  const typeValue = galleryTypeFilter?.value || '';
  const linkedValue = galleryLinkedFilter?.value || '';
  const categoryValue = galleryCategoryFilter?.value || '';
  const eventValue = galleryEventFilter?.value || '';

  let shown = 0;
  items.forEach((item) => {
    const matchesType = !typeValue || item.dataset.mediaType === typeValue;
    const matchesLinked = !linkedValue || item.dataset.linkedType === linkedValue;
    const matchesCategory = !categoryValue || item.dataset.category === categoryValue;
    const matchesEvent = !eventValue || item.dataset.eventId === eventValue;

    const matches = matchesType && matchesLinked && matchesCategory && matchesEvent;
    if (matches && shown < visibleGalleryCount) {
      item.style.display = 'block';
      shown += 1;
    } else {
      item.style.display = 'none';
    }
  });

  if (galleryLoadMore) {
    const totalMatches = items.filter((item) => {
      const matchesType = !typeValue || item.dataset.mediaType === typeValue;
      const matchesLinked = !linkedValue || item.dataset.linkedType === linkedValue;
      const matchesCategory = !categoryValue || item.dataset.category === categoryValue;
      const matchesEvent = !eventValue || item.dataset.eventId === eventValue;
      return matchesType && matchesLinked && matchesCategory && matchesEvent;
    }).length;
    galleryLoadMore.style.display = shown < totalMatches ? 'inline-block' : 'none';
  }
}

[galleryTypeFilter, galleryLinkedFilter, galleryCategoryFilter, galleryEventFilter].forEach((node) => {
  if (node) {
    node.addEventListener('change', () => {
      visibleGalleryCount = 12;
      applyPublicGalleryFilters();
    });
  }
});

if (galleryLoadMore) {
  galleryLoadMore.addEventListener('click', () => {
    visibleGalleryCount += 12;
    applyPublicGalleryFilters();
  });
}

applyPublicGalleryFilters();


const sponsorTypeFilter = document.getElementById('sponsor-type-filter');
const sponsorCards = document.querySelectorAll('.sponsor-card');
if (sponsorTypeFilter && sponsorCards.length) {
  sponsorTypeFilter.addEventListener('change', () => {
    const selected = sponsorTypeFilter.value;
    sponsorCards.forEach((card) => {
      const show = !selected || card.dataset.sponsorType === selected;
      card.style.display = show ? 'block' : 'none';
    });
  });
}

const guidesTypeFilter = document.getElementById('guides-type-filter');
const guideCards = document.querySelectorAll('.guide-card');
if (guidesTypeFilter && guideCards.length) {
  guidesTypeFilter.addEventListener('change', () => {
    const selected = guidesTypeFilter.value;
    guideCards.forEach((card) => {
      const show = !selected || card.dataset.guideType === selected;
      card.style.display = show ? 'block' : 'none';
    });
  });
}

const faqItems = document.querySelectorAll('.faq-item');
faqItems.forEach((item) => {
  const question = item.querySelector('.faq-question');
  const answer = item.querySelector('.faq-answer');
  if (!question || !answer) return;
  question.addEventListener('click', () => {
    answer.classList.toggle('hidden');
    question.classList.toggle('open');
  });
});

const faqSearch = document.getElementById('faq-search');
if (faqSearch && faqItems.length) {
  faqSearch.addEventListener('input', () => {
    const keyword = faqSearch.value.toLowerCase().trim();
    faqItems.forEach((item) => {
      const hay = item.dataset.faqText || '';
      item.style.display = !keyword || hay.includes(keyword) ? 'block' : 'none';
    });
  });
}


const globalSearchInput = document.getElementById('global-search-input');
const suggestionBox = document.getElementById('search-suggestions');
const resultsMeta = document.getElementById('search-results-meta');
const resultsGrid = document.getElementById('search-results');
const searchLoadMore = document.getElementById('search-load-more');
const searchFilters = {
  content_type: document.getElementById('search-content-type'),
  event_category: document.getElementById('search-event-category'),
  post_category: document.getElementById('search-post-category'),
  post_tag: document.getElementById('search-post-tag'),
  media_type: document.getElementById('search-media-type'),
  date_from: document.getElementById('search-date-from'),
  date_to: document.getElementById('search-date-to'),
  sort: document.getElementById('search-sort'),
};

let searchPage = 1;
const searchPerPage = 12;

function collectSearchParams() {
  const params = new URLSearchParams();
  params.set('page', String(searchPage));
  params.set('per_page', String(searchPerPage));
  params.set('q', globalSearchInput?.value || '');
  Object.entries(searchFilters).forEach(([key, node]) => {
    if (node?.value) params.set(key, node.value);
  });
  return params;
}

function highlightKeyword(text, keyword) {
  if (!keyword) return text;
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`(${escaped})`, 'ig');
  return text.replace(re, '<mark>$1</mark>');
}

async function renderSearchResults(reset = true) {
  if (!resultsGrid || !resultsMeta) return;
  if (reset) {
    searchPage = 1;
    resultsGrid.innerHTML = '';
  }

  const params = collectSearchParams();
  const response = await fetch(`/api/search?${params.toString()}`);
  const data = await response.json();
  const keyword = (globalSearchInput?.value || '').trim();

  if (data.results.length === 0 && searchPage === 1) {
    resultsGrid.innerHTML = '<p>No results found.</p>';
  } else {
    data.results.forEach((row) => {
      const card = document.createElement('a');
      card.className = 'event-card search-result-card';
      card.href = row.url;
      const thumb = row.thumbnail ? `<img src="${row.thumbnail}" alt="${row.title}">` : '<div class="image-placeholder">No image</div>';
      card.innerHTML = `${thumb}<div class="event-card-body"><span class="badge">${row.content_type} · ${row.category}</span><h3>${highlightKeyword(row.title, keyword)}</h3><p>${row.date}</p><p>${highlightKeyword(row.description, keyword)}</p></div>`;
      resultsGrid.appendChild(card);
    });
  }

  resultsMeta.textContent = `Showing ${resultsGrid.querySelectorAll('.search-result-card').length} of ${data.total} results`;
  if (searchLoadMore) searchLoadMore.style.display = data.has_next ? 'inline-block' : 'none';
}

async function updateSuggestions() {
  if (!globalSearchInput || !suggestionBox) return;
  const q = globalSearchInput.value.trim();
  if (!q) {
    suggestionBox.innerHTML = '';
    return;
  }
  const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(q)}`);
  const data = await response.json();
  suggestionBox.innerHTML = data.suggestions
    .map((item) => `<button type="button" class="suggestion-item">${item}</button>`)
    .join('');
  suggestionBox.querySelectorAll('.suggestion-item').forEach((btn) => {
    btn.addEventListener('click', () => {
      globalSearchInput.value = btn.textContent || '';
      suggestionBox.innerHTML = '';
      renderSearchResults(true);
    });
  });
}

if (globalSearchInput && resultsGrid) {
  globalSearchInput.addEventListener('input', async () => {
    await updateSuggestions();
    renderSearchResults(true);
  });

  Object.values(searchFilters).forEach((node) => {
    if (node) {
      node.addEventListener('change', () => renderSearchResults(true));
    }
  });

  if (searchLoadMore) {
    searchLoadMore.addEventListener('click', () => {
      searchPage += 1;
      renderSearchResults(false);
    });
  }

  renderSearchResults(true);
}
