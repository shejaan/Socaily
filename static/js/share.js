/* ============================================================
   static/js/share.js
   Share sheet (copy link + send via DM)
   Must be loaded AFTER ajax.js, homepage.js
   ============================================================ */

window.openShareSheet = function openShareSheet(pid) {
  if (window._openMenu) { window._openMenu.style.display = 'none'; window._openMenu = null; }
  document.getElementById('sharePostId').value = pid;
  document.getElementById('shareDmSection').style.display = 'none';
  var t = document.getElementById('shareDmToggle');
  if (t) t.style.display = 'block';
  fetch('/share/' + pid + '/', {
    credentials: 'same-origin',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
    .then(checkResponse)
    .then(function (d) {
      document.getElementById('shareLinkInput').value = d.url || (window.location.origin + '/p/' + pid + '/');
    })
    .catch(function () {});
  document.getElementById('shareOverlay').style.display = 'flex';
  document.body.style.overflow = 'hidden';
};

window.closeShareSheet = function closeShareSheet() {
  document.getElementById('shareOverlay').style.display = 'none';
  document.body.style.overflow = '';
};

window.copyShareLink = function copyShareLink() {
  var inp = document.getElementById('shareLinkInput');
  inp.select();
  try { document.execCommand('copy'); } catch (x) { if (navigator.clipboard) navigator.clipboard.writeText(inp.value); }
  showToast('Link copied!');
};

window.openShareDM = function openShareDM(pid) {
  openShareSheet(pid);
  document.getElementById('shareDmSection').style.display = 'block';
  var t = document.getElementById('shareDmToggle');
  if (t) t.style.display = 'none';
};

window.sendShareDM = function sendShareDM() {
  var pid = document.getElementById('sharePostId').value;
  var un  = document.getElementById('shareDmUser').value.trim();
  if (!un) { showToast('Enter a username.'); return; }
  fetch('/share/' + pid + '/', {
    method: 'POST', credentials: 'same-origin',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({ csrfmiddlewaretoken: getCsrfToken(), username: un }).toString()
  })
    .then(checkResponse)
    .then(function (d) {
      closeShareSheet();
      showToast(d.sent ? 'Sent to ' + un + '!' : 'Link ready (user not found)');
    })
    .catch(function () { showToast('Could not send.'); });
};
