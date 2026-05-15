/* ============================================================
   static/js/notifications.js
   Notification dropdown toggle behaviour
   Must be loaded AFTER ajax.js and homepage.js
   ============================================================ */

(function () {
  var notifOpen = false;

  window.toggleNotifDrop = function toggleNotifDrop(e) {
    e.stopPropagation();
    notifOpen = !notifOpen;
    var drop = document.getElementById('notifDrop');
    if (drop) drop.style.display = notifOpen ? 'block' : 'none';

    if (notifOpen) {
      var dot = document.getElementById('notifDot');
      if (dot) {
        dot.style.display = 'none';
        
        // Mark all as read on backend silently
        fetch('/notifications/read-all/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken()
          },
          keepalive: true
        }).catch(err => console.error('Error marking notifications as read:', err));
      }
    }
  };

  document.addEventListener('click', function () {
    if (notifOpen) {
      notifOpen = false;
      var drop = document.getElementById('notifDrop');
      if (drop) drop.style.display = 'none';
    }
  });
})();
