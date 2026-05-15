/* ============================================================
   static/js/infinite-scroll.js
   Infinite scroll observer — loads paginated feed posts via AJAX.
   Must be loaded AFTER ajax.js, homepage.js, feed.js, share.js
   ============================================================ */

window.initFeedObserver = function initFeedObserver() {
  if (window.__FEED_OBSERVER__) {
    window.__FEED_OBSERVER__.disconnect();
  }
  var sentinel = document.getElementById('feedSentinel');
  if (!sentinel) return;

  var _page    = 2;
  var _loading = false;

  var obs = new IntersectionObserver(function (entries) {
    if (!entries[0].isIntersecting || _loading) return;
    _loading = true;

    fetch('/api/feed/?page=' + _page, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(checkResponse)
      .then(function (data) {
        _loading = false;
        var feed = document.querySelector('.feed');
        var ins  = document.getElementById('feedSentinel') || document.getElementById('feedEnd');

        if (!data.posts || !data.posts.length) {
          sentinel.remove();
          var end = document.getElementById('feedEnd');
          if (end) end.style.display = 'block';
          return;
        }

        _page++;
        if (!data.has_next) {
          sentinel.remove();
          var end = document.getElementById('feedEnd');
          if (end) end.style.display = 'block';
        }

        data.posts.forEach(function (p) {
          var csrf = getCsrfToken();
          var lc   = p.liked ? '#ff3040' : 'none';
          var ls   = p.liked ? '#ff3040' : 'currentColor';
          var sc   = p.saved ? 'currentColor' : 'none';
          var av   = p.avatar_url
            ? '<img src="' + escHtml(p.avatar_url) + '" style="width:100%;height:100%;object-fit:cover" alt="">'
            : '&#x1F9D1;';

          var own = p.is_owner
            ? '<button onclick="openEditPost(' + p.id + ',\'' + p.caption.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + '\',\'' + ((p.location || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'")) + '\')" style="display:block;width:100%;text-align:left;padding:10px 16px;font-size:14px;background:none;border:none;cursor:pointer;font-family:inherit">✏️ Edit</button>' +
              '<button onclick="confirmDeletePost(' + p.id + ')" style="display:block;width:100%;text-align:left;padding:10px 16px;font-size:14px;color:#ed4956;background:none;border:none;cursor:pointer;font-family:inherit">🗑️ Delete</button>'
            : '';

          var html =
            '<div class="post" style="animation:up .4s ease both">' +
            '<div class="ph">' +
            '<a href="/profile/' + escHtml(p.username) + '/" class="par"><div class="pari">' + av + '</div></a>' +
            '<div class="pm"><a href="/profile/' + escHtml(p.username) + '/" class="pun">' + escHtml(p.username) + '</a>' +
            (p.location ? '<div class="ploc">' + escHtml(p.location) + '</div>' : '') + '</div>' +
            '<div style="position:relative">' +
            '<button class="pmb" onclick="togglePostMenu(event,\'pmenu' + p.id + '\')" title="Options">' +
            '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>' +
            '</button>' +
            '<div id="pmenu' + p.id + '" style="display:none;position:absolute;right:0;top:28px;background:#fff;border:1px solid #dbdbdb;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.12);z-index:300;min-width:140px;overflow:hidden">' +
            own +
            '<button onclick="openShareSheet(' + p.id + ')" style="display:block;width:100%;text-align:left;padding:10px 16px;font-size:14px;background:none;border:none;cursor:pointer;font-family:inherit">🔗 Copy link</button>' +
            '<button onclick="openShareDM(' + p.id + ')" style="display:block;width:100%;text-align:left;padding:10px 16px;font-size:14px;background:none;border:none;cursor:pointer;font-family:inherit">✉️ Send via DM</button>' +
            '</div></div></div>' +
            '<div class="pimg"><img src="' + escHtml(p.image_url) + '" alt="" style="width:100%;height:100%;object-fit:cover"></div>' +
            '<div class="pac">' +
            '<form method="POST" action="/like/' + p.id + '/" class="like-form">' +
            '<input type="hidden" name="csrfmiddlewaretoken" value="' + escHtml(csrf) + '">' +
            '<button type="submit" class="abtn lbtn" title="Like">' +
            '<svg viewBox="0 0 24 24" fill="' + lc + '" stroke="' + ls + '" stroke-width="1.8">' +
            '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>' +
            '</button></form>' +
            '<button class="abtn" onclick="toggleComments(\'cmt' + p.id + '\')" title="Comment">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
            '</button>' +
            '<button class="abtn" title="Share" onclick="openShareSheet(' + p.id + ')">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>' +
            '</button>' +
            '<form method="POST" action="/save/' + p.id + '/" class="like-form" style="margin-left:auto">' +
            '<input type="hidden" name="csrfmiddlewaretoken" value="' + escHtml(csrf) + '">' +
            '<button type="submit" class="abtn bkbtn" title="Save">' +
            '<svg viewBox="0 0 24 24" fill="' + sc + '" stroke="currentColor" stroke-width="1.8"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>' +
            '</button></form>' +
            '</div>' +
            '<div class="pinfo">' +
            '<div class="plikes">' + p.like_count + ' like' + (p.like_count === 1 ? '' : 's') + '</div>' +
            (p.caption ? '<div class="pcap"><span class="un">' + escHtml(p.username) + '</span> ' + escHtml(p.caption) + '</div>' : '') +
            '<div id="cmt' + p.id + '" class="comment-box"></div>' +
            '</div>' +
            '<div class="ptime">just now</div>' +
            '<form method="POST" action="/comment/' + p.id + '/" class="crow">' +
            '<input type="hidden" name="csrfmiddlewaretoken" value="' + escHtml(csrf) + '">' +
            '<input class="cinput" type="text" name="text" placeholder="Add a comment\u2026" autocomplete="off" required>' +
            '<button type="submit" class="postbtn">Post</button></form>' +
            '</div>';

          var tmp = document.createElement('div');
          tmp.innerHTML = html;
          feed.insertBefore(tmp.firstElementChild, ins);
          attachPostHandlers(tmp.firstElementChild);
        });
      })
      .catch(function () { _loading = false; });
  }, { rootMargin: '200px' });

  obs.observe(sentinel);
  window.__FEED_OBSERVER__ = obs;
};

/* Auto-initialize on page load */
window.initFeedObserver();
