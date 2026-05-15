/* ============================================================
   static/js/modals.js
   Create Post Modal logic (image preview, step navigation, submit)
   Must be loaded AFTER ajax.js, homepage.js, feed.js
   ============================================================ */

/* ── Image preview → go to Step 2 ── */
window.previewImage = function previewImage(input) {
  if (!input.files || !input.files[0]) return;
  var reader = new FileReader();
  reader.onload = function (e) {
    document.getElementById('cpStep1').style.display = 'none';
    var step2 = document.getElementById('cpStep2');
    step2.style.display = 'flex';
    document.getElementById('cpPreviewImg').src = e.target.result;
    document.getElementById('cpBackBtn').style.display = 'inline-flex';
    document.getElementById('cpHeaderSpacer').style.display = 'none';
    document.getElementById('cpTitle').textContent = 'New post';
  };
  reader.readAsDataURL(input.files[0]);
};

window.cpGoBack = function cpGoBack() {
  document.getElementById('cpStep2').style.display = 'none';
  document.getElementById('cpStep1').style.display = 'flex';
  document.getElementById('cpBackBtn').style.display = 'none';
  document.getElementById('cpHeaderSpacer').style.display = 'block';
  document.getElementById('cpTitle').textContent = 'Create new post';
  document.getElementById('imageInput').value = '';
  document.getElementById('cpPreviewImg').src = '';
  document.getElementById('cpCaption').value = '';
  document.getElementById('cpLocation').value = '';
  document.getElementById('cpError').style.display = 'none';
};

window.showCpError = function showCpError(msg) {
  var el = document.getElementById('cpError');
  el.textContent = msg;
  el.style.display = 'block';
};

window.submitPost = function submitPost() {
  var fileInput = document.getElementById('imageInput');
  if (!fileInput.files || !fileInput.files[0]) {
    showCpError('Please select an image.');
    return;
  }
  var btn = document.getElementById('cpShareBtn');
  btn.disabled = true;
  btn.textContent = 'Sharing\u2026';
  var fd = new FormData();
  fd.append('image',    fileInput.files[0]);
  fd.append('caption',  document.getElementById('cpCaption').value);
  fd.append('location', document.getElementById('cpLocation').value);
  fd.append('csrfmiddlewaretoken', getCsrfToken());
  fetch(document.getElementById('cpShareBtn').dataset.url || '/create-post/', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: fd
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      btn.disabled = false;
      btn.textContent = 'Share';
      if (data.success) {
        closeCreatePost();
        showToast(data.message || 'Post shared! 🎉');
        injectNewPost(data.post);
      } else {
        showCpError(data.error || 'Upload failed. Try again.');
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.textContent = 'Share';
      showCpError('Network error. Please try again.');
    });
};
