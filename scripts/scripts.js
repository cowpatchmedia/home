// ─── scripts.js ──────────────────────────────────────────────────
// Handles: tab switching, lazy loading embeds, resume modal overlay

(() => {
  'use strict';

  // ── Element references ─────────────────────────────────────────
  const homeBtn        = document.getElementById('home-btn');
  const resumeBtn      = document.getElementById('resume-btn');
  const resumeOverlay  = document.getElementById('resume-overlay');
  const resumeClose    = document.getElementById('resume-close');
  const resumeWrap     = document.getElementById('resume-frame-wrap');
  const moduleOverlay  = document.getElementById('module-overlay');
  const moduleContent  = document.getElementById('module-content');
  const moduleClose    = document.getElementById('module-close');
  const tabBar         = document.getElementById('tab-bar');
  const contentArea    = document.getElementById('content-area');
  const btnMusic       = document.getElementById('btn-music');
  const btnPhotos      = document.getElementById('btn-photos');
  const btnGames       = document.getElementById('btn-games');

  // ── Lazy-load flags (each embed loads only once per session) ───
  let resumeLoaded  = false;
  let beholdLoaded  = false;

  // ── Helpers ────────────────────────────────────────────────────

  /** Clear active state from all tab buttons */
  function clearActive() {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  }

  /**
   * Open the module overlay with the provided HTML.
   * postInsert runs after HTML is in the DOM (needed for Behold).
   */
  function openModule(html, postInsert) {
    moduleContent.innerHTML = html;
    moduleOverlay.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';
    if (typeof postInsert === 'function') postInsert();
  }

  /**
   * Close the module overlay and clear its content.
   * skipScroll = true when called by scroll/observer so we don't
   * fight the user's manual scroll direction.
   */
  function closeModule(skipScroll = false) {
    moduleOverlay.setAttribute('hidden', '');
    moduleContent.innerHTML = '';
    document.body.style.overflow = '';
    if (!skipScroll) {
      document.getElementById('main').scrollIntoView({ behavior: 'smooth' });
    }
  }

  // ── Tab: Music ─────────────────────────────────────────────────────
  function showMusic() {
    openModule(`
      <div class="embed-wrap">
        <iframe
          width="100%" height="300"
          scrolling="no" frameborder="no" allow="autoplay"
          src="https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/cowpatch-media/sets/free-air-ep&color=%23548f59&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual=true">
        </iframe>
      </div>
      <p class="sc-credit">
        <a href="https://soundcloud.com/cowpatch-media?utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing" target="_blank" rel="noopener">Cowpatch Media</a>
        &middot;
        <a href="https://soundcloud.com/cowpatch-media/sets/free-air-ep?si=9015a42f37b64b00b3bfc8eb6af1af8e&utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing" target="_blank" rel="noopener">MC Cowpatch: Free Air EP</a>
      </p>`);
  }

  // ── Tab: Photos ────────────────────────────────────────────────────
  function showPhotos() {
    openModule(
      `<div class="photos-wrap"><behold-widget feed-id="BsmxDO1yIIL1zPsolSGb"></behold-widget></div>`,
      () => {
        if (!beholdLoaded) {
          const s = document.createElement('script');
          s.type = 'module';
          s.src  = 'https://w.behold.so/widget.js';
          document.head.appendChild(s);
          beholdLoaded = true;
        }
      }
    );
  }

  // ── Tab: Games ────────────────────────────────────────────────────
  function showGames() {
    openModule(`
      <div class="game-wrap">
        <iframe
          src="game/dicegolfv3.html"
          allowfullscreen
          title="Dice Golf v2">
        </iframe>
      </div>`);
  }

  // ── Resume Modal ───────────────────────────────────────────────
  function openResume() {
    // Lazy-load PDF iframe only on first open
    if (!resumeLoaded) {
      const iframe = document.createElement('iframe');
      // URL-encode the filename to handle the spaces
      iframe.src   = 'website-images/cowpatch-resume.pdf';
      iframe.title = 'Cowpatch Media Resume';
      resumeWrap.appendChild(iframe);
      resumeLoaded = true;
    }
    resumeOverlay.removeAttribute('hidden');
    document.body.style.overflow = 'hidden'; // prevent page scroll behind modal
    resumeClose.focus();
  }

  function closeResume() {
    resumeOverlay.setAttribute('hidden', '');
    document.body.style.overflow = '';
  }

  // ── Scroll-up reset: close module when hero comes back into view ───
  const hero = document.getElementById('hero');
  new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && !moduleOverlay.hidden) {
        closeModule(true);
      }
    },
    { threshold: 0.3 }
  ).observe(hero);

  // ── Event Listeners ──────────────────────────────────────────────
  homeBtn.addEventListener('click', (e) => {
    e.preventDefault();
    closeModule();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  moduleClose.addEventListener('click', () => closeModule());

  resumeBtn.addEventListener('click',  (e) => { e.preventDefault(); openResume(); });
  resumeClose.addEventListener('click', closeResume);

  // Backdrop click closes resume
  resumeOverlay.addEventListener('click', (e) => {
    if (e.target === resumeOverlay) closeResume();
  });

  // Escape closes whichever overlay is open
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!resumeOverlay.hidden)      closeResume();
    else if (!moduleOverlay.hidden) closeModule(true);
  });

  // ── About ───────────────────────────────────────────────────
  function showAbout() {
    openModule(`<p class="about-message">a seattle based professional using this website to explore creative projects.</p>`);
  }

  const aboutBtn = document.getElementById('about-btn');
  if (aboutBtn) aboutBtn.addEventListener('click', (e) => { e.preventDefault(); showAbout(); });

  btnMusic.addEventListener('click',  showMusic);
  btnPhotos.addEventListener('click', showPhotos);
  btnGames.addEventListener('click',  showGames);

})();