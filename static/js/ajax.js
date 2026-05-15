/* ============================================================
   static/js/ajax.js
   Global CSRF helper + AJAX response checker used by all modules
   ============================================================ */

/**
 * Read the CSRF token from the cookie or a hidden form input.
 * @returns {string}
 */
window.getCsrfToken = function getCsrfToken() {
  var name = 'csrftoken', val = null;
  document.cookie.split(';').forEach(function (c) {
    c = c.trim();
    if (c.startsWith(name + '=')) val = decodeURIComponent(c.slice(name.length + 1));
  });
  if (!val) {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el) val = el.value;
  }
  return val || '';
};

/**
 * Assert response is OK, then parse JSON. Throws on non-2xx.
 */
window.checkResponse = function checkResponse(r) {
  if (!r.ok) throw new Error('Server error: ' + r.status);
  return r.json();
};

/**
 * XSS-safe HTML escaper for all dynamic DOM injection.
 */
window.escHtml = function escHtml(t) {
  if (!t) return '';
  return String(t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
};
