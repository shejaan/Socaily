/* ============================================================
   static/js/stories.js
   Story upload modal + story viewer
   Must be loaded AFTER ajax.js and homepage.js
   ============================================================ */

/* ── Story upload modal ── */
window.openStoryUpload = function openStoryUpload() {
  var o = document.getElementById('storyUploadOverlay');
  o.style.display = 'flex';
  document.body.style.overflow = 'hidden';
};
window.closeStoryUpload = function closeStoryUpload() {
  document.getElementById('storyUploadOverlay').style.display = 'none';
  document.body.style.overflow = '';
};

window.previewStory = function previewStory(inp) {
  if (!inp.files || !inp.files[0]) return;
  var reader = new FileReader();
  reader.onload = function (e) {
    var img = document.getElementById('storyPreviewImg');
    img.src = e.target.result;
    img.style.display = 'block';
    document.getElementById('storyDropZone').style.display = 'none';
  };
  reader.readAsDataURL(inp.files[0]);
};

window.submitStory = function submitStory() {
  var fi = document.getElementById('storyFileInput');
  if (!fi.files || !fi.files[0]) {
    var er = document.getElementById('storyError');
    er.textContent = 'Please select an image.';
    er.style.display = 'block';
    return;
  }
  var btn = document.getElementById('storySubmitBtn');
  btn.disabled = true;
  btn.textContent = 'Sharing...';
  var fd = new FormData();
  fd.append('image',   fi.files[0]);
  fd.append('caption', document.getElementById('storyCaptionInput').value);
  fd.append('csrfmiddlewaretoken', getCsrfToken());
  fetch('/stories/upload/', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: fd
  })
    .then(checkResponse)
    .then(function (d) {
      btn.disabled = false;
      btn.textContent = 'Share story';
      if (d.success) {
        closeStoryUpload();
        showToast('Story shared!');
        
        var u = d.story.username;
        var sid = d.story.id;

        // Update Homepage Story Bar
        var sbarDivs = document.querySelectorAll('.sbar .sit');
        if (sbarDivs.length > 0) {
          var own = sbarDivs[0]; // first element is always the current user's story
          own.setAttribute('onclick', "openStoryViewer('" + u + "', " + sid + ")");
          var saddbadge = own.querySelector('.saddbadge');
          if (saddbadge) saddbadge.style.display = 'none';
          var sadd = own.querySelector('.sadd');
          if (sadd) {
            sadd.className = 'sri';
            var sriHtml = sadd.outerHTML;
            own.innerHTML = '<div class="sring">' + sriHtml + '</div><span class="sname">Your story</span>';
          }
        }

        // Update Profile Page Avatar
        var avWrap = document.querySelector('.av-wrap');
        if (avWrap) {
          avWrap.setAttribute('onclick', "openStoryViewer('" + u + "', " + sid + ")");
          var avPlus = avWrap.querySelector('.av-plus');
          if (avPlus) avPlus.style.display = 'none';
          var avRing = avWrap.querySelector('.av-ring');
          if (avRing) {
            avRing.style.background = '';
            avRing.style.padding = '';
          }
        }
      } else {
        var er = document.getElementById('storyError');
        er.textContent = d.error || 'Failed.';
        er.style.display = 'block';
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.textContent = 'Share story';
      showToast('Network error.');
    });
};

/* ── Story viewer ── */
window._svTimer = null;
window._currentStoryId = null;

window.openStoryViewer = function openStoryViewer(username, storyId) {
  fetch('/stories/view/' + storyId + '/', {
    credentials: 'same-origin',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
    .then(checkResponse)
    .then(function (d) {
      window._currentStoryId = d.id;
      document.getElementById('svImage').src = d.image_url;
      document.getElementById('svUsername').textContent = d.username;
      document.getElementById('svCaption').textContent  = d.caption || '';
      document.getElementById('svTime').textContent     = d.created_at;
      var ai = document.getElementById('svAvatarImg');
      if (d.avatar_url) ai.src = d.avatar_url;
      
      var controls = document.getElementById('svOwnerControls');
      var viewersList = document.getElementById('svViewersList');
      if (d.is_owner) {
        controls.style.display = 'flex';
        document.getElementById('svViewCount').textContent = d.view_count;
        
        viewersList.innerHTML = '';
        if (d.viewers && d.viewers.length > 0) {
          d.viewers.forEach(function(v) {
            var av = v.avatar ? '<img src="' + escHtml(v.avatar) + '" style="width:100%;height:100%;object-fit:cover">' : '<div style="font-size:16px;">🧑</div>';
            viewersList.innerHTML += '<div style="display:flex; align-items:center; gap:10px; background:rgba(255,255,255,0.1); padding:6px 12px; border-radius:8px;">' +
              '<div style="width:30px; height:30px; border-radius:50%; overflow:hidden; background:#333; display:flex; align-items:center; justify-content:center; flex-shrink:0;">' + av + '</div>' +
              '<span style="color:#fff; font-size:13px; font-weight:600;">' + escHtml(v.username) + '</span>' +
              '</div>';
          });
        }
      } else {
        controls.style.display = 'none';
      }

      var p = document.getElementById('svProgress');
      p.style.transition = 'none';
      p.style.width = '0%';
      setTimeout(function () { p.style.transition = 'width 5s linear'; p.style.width = '100%'; }, 50);
      document.getElementById('storyViewerOverlay').style.display = 'flex';
      document.body.style.overflow = 'hidden';
      if (window._svTimer) clearTimeout(window._svTimer);
      window._svTimer = setTimeout(closeStoryViewer, 5000);
    })
    .catch(function () { showToast('Could not load story.'); });
};

window.closeStoryViewer = function closeStoryViewer() {
  document.getElementById('storyViewerOverlay').style.display = 'none';
  document.body.style.overflow = '';
  if (window._svTimer) { clearTimeout(window._svTimer); window._svTimer = null; }
  window._currentStoryId = null;
};

window.deleteCurrentStory = function deleteCurrentStory() {
  if (!window._currentStoryId) return;
  if (!confirm("Are you sure you want to delete this story?")) return;
  
  fetch('/stories/delete/' + window._currentStoryId + '/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
  })
    .then(checkResponse)
    .then(function (d) {
      if (d.success) {
        closeStoryViewer();
        showToast('Story deleted.');

        // Revert Homepage Story Bar
        var sbarDivs = document.querySelectorAll('.sbar .sit');
        if (sbarDivs.length > 0) {
          var own = sbarDivs[0];
          own.setAttribute('onclick', "openStoryUpload()");
          var sri = own.querySelector('.sri');
          if (sri) {
            sri.className = 'sadd';
            sri.innerHTML += '<div class="saddbadge">+</div>';
            own.innerHTML = sri.outerHTML + '<span class="sname">Your story</span>';
          }
        }

        // Revert Profile Page Avatar
        var avWrap = document.querySelector('.av-wrap');
        if (avWrap) {
          avWrap.setAttribute('onclick', "openStoryUpload()");
          var avPlus = avWrap.querySelector('.av-plus');
          if (avPlus) avPlus.style.display = 'flex';
          var avRing = avWrap.querySelector('.av-ring');
          if (avRing) {
            avRing.style.background = 'transparent';
            avRing.style.padding = '0';
          }
        }
      } else {
        showToast('Could not delete story.');
      }
    })
    .catch(function () { showToast('Network error.'); });
};
