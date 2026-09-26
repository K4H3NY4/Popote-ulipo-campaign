'use strict';
const $ = (id) => document.getElementById(id);
const form = $('uploadForm');
const input = $('imageInput');
const dropzone = $('dropzone');
const consent = $('consent');
const submit = $('submitBtn');
const MAX_BYTES = 16 * 1024 * 1024;
let selectedFile = null;
let previewURL = null;
let busy = false;
let selectionVersion = 0;

function showError(message) {
  $('errorMessage').textContent = message;
  $('errorAlert').hidden = false;
}
function updateButton() {
  submit.disabled = busy || !selectedFile || !consent.checked;
}
function clearSelection() {
  selectionVersion++;
  selectedFile = null;
  input.value = '';
  if (previewURL) URL.revokeObjectURL(previewURL);
  previewURL = null;
  $('selectedPreview').removeAttribute('src');
  $('fileInfo').hidden = true;
  $('results').hidden = true;
  $('errorAlert').hidden = true;
  updateButton();
}
async function selectFile(file) {
  if (busy) return;
  clearSelection();
  if (!file) return;
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    showError('Please select a JPG or PNG image.'); return;
  }
  if (!file.size || file.size > MAX_BYTES) {
    showError('Please choose a non-empty image smaller than 16 MB.'); return;
  }
  const version = selectionVersion;
  const url = URL.createObjectURL(file);
  const probe = new Image();
  probe.src = url;
  try { await probe.decode(); }
  catch { URL.revokeObjectURL(url); if (version === selectionVersion) showError('This image could not be opened. Please choose another photo.'); return; }
  if (version !== selectionVersion) { URL.revokeObjectURL(url); return; }
  previewURL = url;
  selectedFile = file;
  $('selectedPreview').src = url;
  $('fileName').textContent = file.name;
  $('fileSize').textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
  $('fileInfo').hidden = false;
  updateButton();
}
function setBusy(value) {
  busy = value;
  input.disabled = value;
  consent.disabled = value;
  $('removeBtn').disabled = value;
  $('loading').hidden = !value;
  $('buttonText').textContent = value ? 'Creating your poster…' : 'Generate my poster';
  form.setAttribute('aria-busy', String(value));
  updateButton();
}
// Only web URLs may be used for images returned by the server.
function imageURL(value) {
  if (typeof value !== 'string' || !value.trim()) throw new Error('The server did not return a poster image. Please try again.');
  const url = new URL(value, location.href);
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('The server returned an unsupported image URL.');
  return url.href;
}
input.addEventListener('change', () => selectFile(input.files[0]));
consent.addEventListener('change', updateButton);
$('removeBtn').addEventListener('click', clearSelection);
['dragenter', 'dragover'].forEach((event) => dropzone.addEventListener(event, (e) => {
  e.preventDefault(); if (!busy) dropzone.classList.add('dragging');
}));
['dragleave', 'drop'].forEach((event) => dropzone.addEventListener(event, (e) => {
  e.preventDefault(); dropzone.classList.remove('dragging');
}));
dropzone.addEventListener('drop', (e) => {
  if (busy) return;
  if (e.dataTransfer.files.length !== 1) { showError('Please drop one photo at a time.'); return; }
  selectFile(e.dataTransfer.files[0]);
});
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (busy || !selectedFile || !consent.checked) return;
  $('errorAlert').hidden = true;
  $('results').hidden = true;
  if (location.protocol === 'file:') {
    showError('To generate a poster, serve this page from your application with a working /generate endpoint. File preview supports photo selection only.'); return;
  }
  const body = new FormData();
  body.append('image', selectedFile);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000);
  setBusy(true);
  try {
    const response = await fetch(form.dataset.endpoint, { method: 'POST', body, signal: controller.signal, headers: { Accept: 'application/json' } });
    if (!response.headers.get('content-type')?.includes('application/json')) {
      throw new Error('The image service is unavailable. Please check that /generate is running and returns JSON.');
    }
    const data = await response.json();
    if (!response.ok || !data.success) {
      const detail = typeof data.details === 'string' ? data.details : data.error;
      throw new Error(typeof detail === 'string' ? detail : 'Generation failed. Please try another photo.');
    }
    const generatedURL = imageURL(data.generated_url);
    const generated = new Image();
    generated.src = generatedURL;
    await Promise.race([
      generated.decode(),
      new Promise((_, reject) => controller.signal.addEventListener('abort', () => reject(new DOMException('Timed out', 'AbortError')), { once: true }))
    ]);
    $('originalImg').src = previewURL;
    $('generatedImg').src = generatedURL;
    $('downloadBtn').href = generatedURL;
    $('downloadBtn').target = '_blank';
    $('downloadBtn').rel = 'noopener';
    $('results').hidden = false;
    $('results').focus({ preventScroll: true });
    $('results').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  } catch (error) {
    showError(error.name === 'AbortError' ? 'This is taking longer than expected. Please try again shortly.' : error.message || 'Could not connect. Please try again.');
  } finally {
    clearTimeout(timeout);
    setBusy(false);
  }
});
$('startAgain').addEventListener('click', () => {
  clearSelection(); consent.checked = false; updateButton();
  $('create').scrollIntoView(); input.focus({ preventScroll: true });
});
window.addEventListener('pagehide', () => { if (previewURL) URL.revokeObjectURL(previewURL); });
