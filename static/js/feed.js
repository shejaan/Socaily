/* ============================================================
   static/js/feed.js
   AJAX like, comment, post inject, post menu, edit/delete
   Must be loaded AFTER ajax.js and homepage.js
   ============================================================ */

/* ── Attach AJAX handlers to all like-forms and comment-forms ── */
window.attachPostHandlers = function attachPostHandlers(scope) {
  scope = scope || document;

  /* Like forms */
  scope.querySelectorAll('form.like-form').forEach(function (form) {
    if (form.dataset.ajaxBound) return;
    form.dataset.ajaxBound = '1';
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button');
      fetch(form.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({ csrfmiddlewaretoken: getCsrfToken() })
      })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) {
          var svg = btn && btn.querySelector('svg');
          if (svg) {
            svg.setAttribute('fill',   data.liked ? '#ff3040' : 'none');
            svg.setAttribute('stroke', data.liked ? '#ff3040' : 'currentColor');
          }
          var post = form.closest('.post');
          if (post && data.like_count !== undefined) {
            var el = post.querySelector('.plikes');
            if (el) { var n = data.like_count; el.textContent = n + ' like' + (n === 1 ? '' : 's'); }
          }
          if (btn) { btn.style.transform = 'scale(1.4)'; setTimeout(function () { btn.style.transform = ''; }, 200); }
        })
        .catch(function (err) { console.error('[Like]', err); showToast('Could not update like.'); });
    });
  });

  /* Comment forms */
  scope.querySelectorAll('form.crow').forEach(function (form) {
    if (form.dataset.ajaxBound) return;
    form.dataset.ajaxBound = '1';
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var input  = form.querySelector('.cinput');
      var text   = input ? input.value.trim() : '';
      if (!text) return;
      var subBtn = form.querySelector('.postbtn');
      if (subBtn) subBtn.disabled = true;
      fetch(form.action, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'csrfmiddlewaretoken=' + encodeURIComponent(getCsrfToken()) + '&text=' + encodeURIComponent(text)
      })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) {
          if (subBtn) subBtn.disabled = false;
          if (!data.success) { showToast(data.error || 'Could not post comment.'); return; }
          if (input) input.value = '';
          var post = form.closest('.post');
          if (post) {
            var m   = form.action.match(/\/comment\/(\d+)\//), pid = m ? m[1] : null;
            if (pid) {
              var box = document.getElementById('cmt' + pid);
              if (box) {
                var c      = data.comment;
                var avHTML = c.avatar
                  ? '<img src="' + escHtml(c.avatar) + '" style="width:100%;height:100%;object-fit:cover">'
                  : '🧑';
                var row = document.createElement('div');
                row.style.cssText = 'display:flex;gap:8px;margin-bottom:8px;align-items:flex-start';
                row.innerHTML =
                  '<div style="width:28px;height:28px;border-radius:50%;overflow:hidden;flex-shrink:0;border:1px solid #efefef">' + avHTML + '</div>' +
                  '<div style="font-size:13px;line-height:1.45"><span style="font-weight:700;margin-right:4px">' + escHtml(c.username) + '</span>' + escHtml(c.text) + '</div>';
                box.style.display = 'block';
                box.appendChild(row);
              }
            }
            showToast('Comment posted! 💬');
          }
        })
        .catch(function (err) {
          if (subBtn) subBtn.disabled = false;
          console.error('[Comment]', err);
          showToast('Could not post comment.');
        });
    });
  });
};

/* ── Tag each server-rendered post with its ID ── */
document.querySelectorAll('.post').forEach(function (post) {
  var lf = post.querySelector('form.like-form');
  if (lf) { var m = lf.action.match(/\/like\/(\d+)\//); if (m) post.dataset.postId = m[1]; }
});

/* ── Bind on initial page load ── */
attachPostHandlers(document);

/* ── Post menu toggle ── */
window._openMenu = null;
window.togglePostMenu = function togglePostMenu(e, id) {
  e.stopPropagation();
  var m = document.getElementById(id);
  if (!m) return;
  var open = m.style.display === 'block';
  if (window._openMenu && window._openMenu !== m) window._openMenu.style.display = 'none';
  m.style.display = open ? 'none' : 'block';
  window._openMenu = open ? null : m;
};
document.addEventListener('click', function () {
  if (window._openMenu) { window._openMenu.style.display = 'none'; window._openMenu = null; }
});

/* ── Edit post ── */
window.openEditPost = function openEditPost(pid, cap, loc) {
  if (window._openMenu) { window._openMenu.style.display = 'none'; window._openMenu = null; }
  document.getElementById('editPostId').value = pid;
  document.getElementById('editCaption').value = cap;
  document.getElementById('editLocation').value = loc;
  document.getElementById('editPostError').style.display = 'none';
  document.getElementById('editPostOverlay').style.display = 'flex';
  document.body.style.overflow = 'hidden';
};
window.closeEditPost = function closeEditPost() {
  document.getElementById('editPostOverlay').style.display = 'none';
  document.body.style.overflow = '';
};
window.submitEditPost = function submitEditPost() {
  var pid = document.getElementById('editPostId').value;
  var b = new URLSearchParams({
    csrfmiddlewaretoken: getCsrfToken(),
    caption:  document.getElementById('editCaption').value,
    location: document.getElementById('editLocation').value
  });
  fetch('/edit-post/' + pid + '/', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded' },
    body: b.toString()
  })
    .then(checkResponse)
    .then(function (d) {
      if (d.success) {
        document.querySelectorAll('.post').forEach(function (post) {
          var lf = post.querySelector('form.like-form');
          if (lf) {
            var m = lf.action.match(/\/like\/(\d+)\//);
            if (m && m[1] == pid) {
              var capEl = post.querySelector('.pcap');
              if (capEl) {
                var un = capEl.querySelector('.un');
                capEl.textContent = '';
                if (un) capEl.appendChild(un);
                if (d.caption) {
                  capEl.appendChild(document.createTextNode(' ' + d.caption));
                  var row = post.querySelector('.caption-row');
                  if (row) row.style.display = 'flex';
                } else {
                  var row = post.querySelector('.caption-row');
                  if (row) row.style.display = 'none';
                }
              }
              var locEl = post.querySelector('.ploc');
              if (locEl) locEl.textContent = d.location || '';

              var editBtns = post.querySelectorAll('.edit-btn');
              editBtns.forEach(function(btn) {
                 var safeCap = (d.caption || '').replace(/'/g, "\\'");
                 var safeLoc = (d.location || '').replace(/'/g, "\\'");
                 btn.setAttribute('onclick', "closePostModal(" + pid + "); openEditPost(" + pid + ", '" + safeCap + "', '" + safeLoc + "');");
              });
            }
          }
        });
        closeEditPost();
        showToast('Post updated');
      } else {
        var er = document.getElementById('editPostError');
        er.textContent = d.error || 'Failed.';
        er.style.display = 'block';
      }
    })
    .catch(function () { showToast('Network error.'); });
};

/* ── Delete post ── */
window.confirmDeletePost = function confirmDeletePost(pid) {
  if (window._openMenu) { window._openMenu.style.display = 'none'; window._openMenu = null; }
  if (!confirm('Delete this post? This cannot be undone.')) return;
  fetch('/delete-post/' + pid + '/', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
    body: new URLSearchParams({ csrfmiddlewaretoken: getCsrfToken() })
  })
    .then(checkResponse)
    .then(function (d) {
      if (d.success) {
        document.querySelectorAll('.post').forEach(function (post) {
          var lf = post.querySelector('form.like-form');
          if (lf) { var m = lf.action.match(/\/like\/(\d+)\//); if (m && m[1] == pid) post.remove(); }
        });
        var gi = document.getElementById('gi-' + pid);
        if (gi) gi.remove();
        showToast('Post deleted.');
      }
    })
    .catch(function () { showToast('Network error.'); });
};

/* ── Inject a newly created post card at the top of the feed ── */
window.injectNewPost = function injectNewPost(post) {
  var feed = document.querySelector('.feed');
  if (!feed) return;
  var emptyCard = feed.querySelector('[style*="No posts"]');
  if (emptyCard) emptyCard.remove();
  var csrf  = getCsrfToken();
  var pid   = post.id || '';
  var likeUrl = '/like/' + pid + '/';
  var cmtUrl  = '/comment/' + pid + '/';
  var html =
    '<div class="post" style="animation:up .4s ease both" data-post-id="' + pid + '">' +
    '<div class="ph"><div class="par"><div class="pari">&#x1F9D1;</div></div>' +
    '<div class="pm"><div class="pun">' + escHtml(post.username) + '</div></div></div>' +
    '<div class="pimg"><img src="' + post.image_url + '" alt="' + escHtml(post.caption) + '" style="width:100%"></div>' +
    '<div class="pac">' +
    '<form method="POST" action="' + likeUrl + '" class="like-form">' +
    '<input type="hidden" name="csrfmiddlewaretoken" value="' + escHtml(csrf) + '">' +
    '<button type="submit" class="abtn lbtn" title="Like">' +
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">' +
    '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>' +
    '</button></form></div>' +
    '<div class="pinfo"><div class="plikes">0 likes</div>' +
    (post.caption ? '<div class="pcap"><span class="un">' + escHtml(post.username) + '</span> ' + escHtml(post.caption) + '</div>' : '') +
    '</div><div class="ptime">just now</div>' +
    '<form method="POST" action="' + cmtUrl + '" class="crow">' +
    '<input type="hidden" name="csrfmiddlewaretoken" value="' + escHtml(csrf) + '">' +
    '<input class="cinput" type="text" name="text" placeholder="Add a comment\u2026" autocomplete="off" required>' +
    '<button type="submit" class="postbtn">Post</button></form>' +
    '</div>';
  var sbar = feed.querySelector('.sbar');
  if (sbar) {
    sbar.insertAdjacentHTML('afterend', html);
  } else {
    var firstPost = feed.querySelector('.post');
    if (firstPost) firstPost.insertAdjacentHTML('beforebegin', html);
    else feed.insertAdjacentHTML('afterbegin', html);
  }
  var newPost = feed.querySelector('.post[data-post-id="' + pid + '"]');
  if (newPost) attachPostHandlers(newPost);
};
