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

  // Dynamic Polling for updates (Notifications & New Posts) without full reload
  setInterval(function() {
    fetch('/api/poll-updates/')
      .then(r => r.json())
      .then(data => {
        // 1. Dynamic Notification Dot
        if (data.unread_notifs > 0) {
          var dot = document.getElementById('notifDot');
          if (dot && !notifOpen) {
            dot.style.display = 'block';
          }
        }

        // 2. Dynamic Message Dot
        var msgDot = document.getElementById('msgDot');
        if (msgDot) {
          msgDot.style.display = (data.unread_msgs > 0) ? 'block' : 'none';
        }
        
        // 3. Dynamic Feed Posts checker (Only on homepage)
        if (window.latestFeedPostId && data.latest_post_id > window.latestFeedPostId) {
          var feed = document.querySelector('.feed');
          if (feed && !document.getElementById('newPostsBtn')) {
             var btn = document.createElement('button');
             btn.id = 'newPostsBtn';
             btn.innerHTML = 'New posts available. Click to view &uarr;';
             btn.style.cssText = 'display:block;width:100%;padding:12px;background:var(--blue);color:#fff;border:none;border-radius:8px;font-weight:700;margin-bottom:16px;cursor:pointer;animation:down .4s ease;';
             btn.onclick = function() { window.location.reload(); };
             var storiesBar = document.querySelector('.stories-bar');
             if (storiesBar) {
                storiesBar.parentNode.insertBefore(btn, storiesBar.nextSibling);
             } else {
                feed.insertBefore(btn, feed.firstChild);
             }
          }
        }
      })
      .catch(e => console.log('Polling error', e));
  }, 15000); // 15 seconds
})();
