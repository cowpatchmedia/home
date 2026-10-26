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
  const btnSoccer      = document.getElementById('btn-soccer');

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

    // ── Tab: Soccer Analytics ──────────────────────────────────────
  function showSoccer() {
    openModule(`
      <section class="soccer-wrap">
        <header class="soccer-header">
          <p class="soccer-eyebrow">DATA & ANALYSIS</p>
          <h2>player comparison lab.</h2>
          <p>Exploring player performance through soccer data.</p>
        </header>

        <div class="soccer-controls">
          <label>
            Player A
            <select id="player-a"></select>
          </label>

          <label>
            Player B
            <select id="player-b"></select>
          </label>
        </div>

        <div id="player-radar"></div>

        <p id="player-lab-status" aria-live="polite">
          Loading player data...
        </p>

        <p class="soccer-credit">
          Data: StatsBomb Open Data.
          See the source repository and attribution requirements.
        </p>
      </section>
    `, loadSoccerData);
  }

  // Load the generated JSON file and set up the player comparison.
  async function loadSoccerData() {
    const playerA = document.getElementById('player-a');
    const playerB = document.getElementById('player-b');
    const status = document.getElementById('player-lab-status');

    try {
      if (typeof Plotly === 'undefined') {
        throw new Error('Plotly did not load. Check your internet connection.');
      }

      const response = await fetch('data/player_stats.json');

      if (!response.ok) {
        throw new Error(`Could not load player data (HTTP ${response.status}).`);
      }

      const data = await response.json();

      // Exclude unused substitutes from the comparison dropdowns.
      const players = data.players
        .filter(player => player.minutes > 0)
        .sort((a, b) => a.name.localeCompare(b.name));

      if (players.length < 2) {
        throw new Error('At least two players with recorded minutes are needed.');
      }

      // Use player ID as the option value; show team to distinguish players.
      players.forEach(player => {
        const label = `${player.name} — ${player.team}`;

        playerA.add(new Option(label, player.id));
        playerB.add(new Option(label, player.id));
      });

      playerA.selectedIndex = 0;
      playerB.selectedIndex = 1;


    const metrics = [
      // Attacking
      { key: 'goalsPer90', label: 'Goals / 90', category: 'Attacking', max: 0.8, decimals: 2 },
      { key: 'xGPer90', label: 'xG / 90', category: 'Attacking', max: 0.6, decimals: 2 },
      { key: 'xAPer90', label: 'xA / 90', category: 'Attacking', max: 0.3, decimals: 2 },

      // Defending
      { key: 'tacklesPer90', label: 'Tackles / 90', category: 'Defending', max: 3.5, decimals: 2 },
      { key: 'interceptionsPer90', label: 'Interceptions / 90', category: 'Defending', max: 2.5, decimals: 2 },
      { key: 'ballRecoveriesPer90', label: 'Ball recoveries / 90', category: 'Defending', max: 6.5, decimals: 2 },

      // Ball progression
      { key: 'passesPer90', label: 'Passes / 90', category: 'Ball progression', max: 80, decimals: 2 },
      { key: 'passCompletionPct', label: 'Pass completion %', category: 'Ball progression', max: 100, decimals: 1, suffix: '%' },
      { key: 'progressiveCarriesPer90', label: 'Progressive carries / 90', category: 'Ball progression', max: 8.5, decimals: 2 }
    ];

    function makeTrace(player) {
      const actualValues = metrics.map(metric => {
        const value = Number(player[metric.key]);
        return Number.isFinite(value) ? Math.max(0, value) : 0;
      });

      // Convert each metric to its own fixed 0–100 visual scale.
      // The underlying statistics remain unchanged.
      const visualValues = actualValues.map((value, index) =>
        Math.min((value / metrics[index].max) * 100, 100)
      );

      const hoverDetails = actualValues.map((value, index) => {
        const metric = metrics[index];
        const formattedValue =
          value.toFixed(metric.decimals) + (metric.suffix || '');

        const aboveScale = value > metric.max
          ? 'Above visual scale; position capped at 100'
          : '';

        return [
          formattedValue,
          metric.category,
          aboveScale
        ];
      });

      // Repeat the first point to close the radar shape.
      return {
        type: 'scatterpolar',
        r: [...visualValues, visualValues[0]],
        theta: [
          ...metrics.map(metric => metric.label),
          metrics[0].label
        ],
        customdata: [...hoverDetails, hoverDetails[0]],
        fill: 'toself',
        name: `${player.name} (${player.team})`,
        hovertemplate:
          '%{theta}<br>' +
          'Actual value: %{customdata[0]}<br>' +
          'Category: %{customdata[1]}<br>' +
          '%{customdata[2]}' +
          '<extra>%{fullData.name}</extra>'
      };
    }

    function updateChart() {
      const selectedA = players.find(p => p.id === playerA.value);
      const selectedB = players.find(p => p.id === playerB.value);

      if (!selectedA || !selectedB) return;

      Plotly.react(
        'player-radar',
        [makeTrace(selectedA), makeTrace(selectedB)],
        {
          title: {
            text: 'Player performance profiles',
            font: { size: 16 }
          },
          showlegend: true,
          legend: { orientation: 'h' },
          margin: { t: 60, r: 65, b: 55, l: 65 },
          autosize: true,
          polar: {
            radialaxis: {
              visible: true,
              range: [0, 100],
              tickvals: [0, 25, 50, 75, 100],
              ticktext: ['0', '25', '50', '75', '100']
            }
          },
          annotations: [
            {
              text: 'Visual scale: 0–100 per metric · Hover for actual values',
              x: 0.5,
              y: -0.12,
              xref: 'paper',
              yref: 'paper',
              showarrow: false,
              font: { size: 11 }
            }
          ]
        },
        { responsive: true }
      );
    }

      playerA.addEventListener('change', updateChart);
      playerB.addEventListener('change', updateChart);

      updateChart();

      status.textContent =
        `Loaded ${players.length} players from ${data.matchesProcessed} matches.`;
    } catch (error) {
      console.error('Soccer data error:', error);
      status.textContent = `Unable to load player comparison: ${error.message}`;
    }
  }

  // ── Resume Modal ───────────────────────────────────────────────
  function openResume() {
    // Lazy-load PDF iframe only on first open
    if (!resumeLoaded) {
      const iframe = document.createElement('iframe');
      // URL-encode the filename to handle the spaces
      iframe.src   = 'website-images/resume2026.pdf';
      iframe.title = 'Resume';
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
  btnSoccer.addEventListener('click', showSoccer);

})();