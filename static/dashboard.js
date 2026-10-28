(() => {
  const rootStyles = getComputedStyle(document.documentElement);
  const css = (name) => rootStyles.getPropertyValue(name).trim();
  const cyan = css('--cyan') || '#50e4f5';
  const purple = css('--purple') || '#b49aff';
  const red = css('--red') || '#ff6c87';
  const amber = css('--amber') || '#ffca75';
  const green = css('--green') || '#5be0b0';
  const grid = 'rgba(145,173,216,.09)';
  const ticks = '#7185a4';

  // Count-up animation is decorative only; the final value always comes from the server.
  document.querySelectorAll('.count-up').forEach((node) => {
    const target = Number(node.dataset.count || 0);
    if (!Number.isFinite(target) || target < 1) { node.textContent = '0'; return; }
    const duration = 650;
    const start = performance.now();
    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      node.textContent = String(Math.round(target * eased));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });

  const dataNode = document.getElementById('chart-event-data');
  let events = [];
  try { events = dataNode ? JSON.parse(dataNode.textContent || '[]') : []; } catch (_) { events = []; }

  if (window.Chart) {
    Chart.defaults.color = ticks;
    Chart.defaults.font.family = 'DM Mono, monospace';
    Chart.defaults.font.size = 9;
    Chart.defaults.animation.duration = 900;

    const lineCanvas = document.getElementById('activityChart');
    if (lineCanvas) {
      const ordered = [...events].reverse();
      const labels = ordered.map((e, i) => {
        const raw = String(e.created_at || '');
        const match = raw.match(/T(\d{2}:\d{2})/);
        return match ? match[1] : `EVT ${String(i + 1).padStart(2, '0')}`;
      });
      const values = ordered.map(e => Math.max(0, Math.min(100, Number(e.risk_score) || 0)));
      const ctx = lineCanvas.getContext('2d');
      const gradient = ctx.createLinearGradient(0, 0, 0, 190);
      gradient.addColorStop(0, 'rgba(80,228,245,.28)');
      gradient.addColorStop(1, 'rgba(80,228,245,0)');
      new Chart(lineCanvas, {
        type: 'line',
        data: { labels, datasets: [{ label: 'Risk score', data: values, borderColor: cyan, backgroundColor: gradient, fill: true, borderWidth: 2, tension: .38, pointRadius: values.length > 8 ? 1.5 : 3, pointHoverRadius: 5, pointBackgroundColor: cyan, pointBorderColor: '#101a2d', pointBorderWidth: 2 }] },
        options: { responsive: true, maintainAspectRatio: false, interaction: { intersect: false, mode: 'index' }, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#07101f', borderColor: '#50e4f544', borderWidth: 1, titleColor: '#eaf2ff', bodyColor: cyan, displayColors: false, callbacks: { label: (ctx) => ` Risk score: ${ctx.parsed.y}/100` } } }, scales: { x: { grid: { display: false }, border: { display: false }, ticks: { maxTicksLimit: 6, maxRotation: 0 } }, y: { min: 0, max: 100, border: { display: false, dash: [3, 4] }, grid: { color: grid }, ticks: { stepSize: 25, padding: 8 } } } }
      });
    }

    const donutCanvas = document.getElementById('severityChart');
    if (donutCanvas) {
      const low = Number(donutCanvas.dataset.low || 0);
      const medium = Number(donutCanvas.dataset.medium || 0);
      const high = Number(donutCanvas.dataset.high || 0);
      new Chart(donutCanvas, {
        type: 'doughnut',
        data: { labels: ['Low', 'Medium', 'High'], datasets: [{ data: [low, medium, high], backgroundColor: [green, amber, red], borderColor: '#101a2d', borderWidth: 4, hoverOffset: 7, spacing: 2 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '78%', plugins: { legend: { display: false }, tooltip: { backgroundColor: '#07101f', borderColor: '#50e4f544', borderWidth: 1, titleColor: '#eaf2ff', bodyColor: '#b9cbe4', padding: 10, callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed} events` } } } }
      });
    }
  }

  const form = document.getElementById('simulation-form');
  if (form) form.addEventListener('submit', (event) => {
    const button = event.submitter;
    if (!button || button.disabled) return;
    const original = button.querySelector('b');
    if (original) original.textContent = 'Running safe simulation…';
    button.setAttribute('aria-busy', 'true');
    const icon = button.querySelector('.scenario-symbol');
    if (icon) icon.textContent = '↻';
  });
})();
