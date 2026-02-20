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
