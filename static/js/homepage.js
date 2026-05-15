/* ============================================================
   static/js/homepage.js
   Shared UI utilities: toast, comment toggle, Django messages
   Must be loaded AFTER ajax.js
   ============================================================ */

/* ── Toast notification ── */
window.showToast = function showToast(msg) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(function () { t.classList.remove('show'); }, 3500);
};

/* ── Toggle comment box open/close ── */
window.toggleComments = function toggleComments(id) {
  var el = document.getElementById(id);
  if (!el) return;
  var hidden = el.style.display === 'none' || el.style.display === '';
  el.style.display = hidden ? 'block' : 'none';
  var btn = el.previousElementSibling;
  if (btn && btn.classList.contains('vcmt'))
    btn.textContent = hidden ? 'Hide comments' : 'View all comments';
};

/* ── Create post modal ── */
window.openCreatePost = function openCreatePost() {
  document.getElementById('cpOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
};
window.closeCreatePost = function closeCreatePost() {
  document.getElementById('cpOverlay').classList.remove('open');
  document.body.style.overflow = '';
};

/* ── Django messages → toast on page load ── */
/* NOTE: this block is rendered server-side in the template and calls showToast() */
