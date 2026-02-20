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
