const DiscourseLab = {
  showToast(title, body, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `dl-toast ${type}`;
    const icons = { success: '•', xp: '•', achievement: '•' };
    toast.innerHTML = `
      <span class="dl-toast-icon">${icons[type] || '✓'}</span>
      <div class="dl-toast-body"><strong>${title}</strong><span>${body}</span></div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(24px)';
      toast.style.transition = 'all 250ms ease';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  },

  showLevelUp(level) {
    const overlay = document.createElement('div');
    overlay.className = 'dl-modal-overlay';
    overlay.innerHTML = `
      <div class="dl-modal">
        <div class="dl-modal-celebration">🎉</div>
        <h2>¡Subiste de nivel!</h2>
        <p>Ahora eres nivel ${level}. Sigue avanzando en tu misión.</p>
        <button class="dl-btn dl-btn-primary" id="closeLevelUp">Continuar</button>
      </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('open'));
    overlay.querySelector('#closeLevelUp').addEventListener('click', () => {
      overlay.classList.remove('open');
      setTimeout(() => overlay.remove(), 300);
    });
  },

  animateCounter(el, target, duration = 1200) {
    const start = performance.now();
    const from = 0;
    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(from + (target - from) * eased);
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  },
};

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-target]').forEach((el) => {
    const target = Number(el.dataset.target);
    if (!isNaN(target) && target > 0) {
      const observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) {
          DiscourseLab.animateCounter(el, target);
          observer.unobserve(el);
        }
      }, { threshold: 0.5 });
      observer.observe(el);
    }
  });

  const tabs = document.querySelectorAll('.dl-tab');
  const panels = document.querySelectorAll('.dl-tab-panel');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      panels.forEach((p) => p.classList.remove('active'));
      tab.classList.add('active');
      const panel = document.getElementById(tab.dataset.tab);
      if (panel) panel.classList.add('active');
    });
  });

  const themeToggle = document.getElementById('themeToggle');
  const themeToggleProfile = document.getElementById('themeToggleProfile');
  const toggleTheme = () => {
    const html = document.documentElement;
    const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
    html.dataset.theme = next;
    localStorage.setItem('dl-theme', next);
  };
  themeToggle?.addEventListener('click', toggleTheme);
  themeToggleProfile?.addEventListener('click', toggleTheme);
  const saved = localStorage.getItem('dl-theme');
  if (saved) document.documentElement.dataset.theme = saved;

  const reminderToggle = document.getElementById('reminderToggle');
  const reminderEnabled = localStorage.getItem('dl-reminders') === 'enabled';
  const updateReminderButton = (enabled) => {
    if (reminderToggle) reminderToggle.textContent = enabled ? 'Desactivar recordatorios' : 'Activar recordatorios';
  };
  updateReminderButton(reminderEnabled);
  reminderToggle?.addEventListener('click', () => {
    const enabled = localStorage.getItem('dl-reminders') !== 'enabled';
    localStorage.setItem('dl-reminders', enabled ? 'enabled' : 'disabled');
    updateReminderButton(enabled);
    DiscourseLab.showToast(enabled ? 'Recordatorios activados' : 'Recordatorios desactivados', enabled ? 'Tu preferencia quedó guardada en este dispositivo.' : 'No se mostrarán nuevos recordatorios.', 'success');
  });

  const routeModeToggle = document.getElementById('routeModeToggle');
  const routeModeLabel = document.getElementById('routeModeLabel');
  routeModeToggle?.addEventListener('change', async () => {
    const enabled = routeModeToggle.checked;
    routeModeToggle.disabled = true;
    try {
      const response = await fetch(routeModeToggle.dataset.routeModeEndpoint || '/api/route-mode', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        throw new Error(response.redirected ? 'La sesión expiró. Inicia sesión nuevamente.' : `El servidor respondió con ${response.status}.`);
      }
      if (!response.ok || !data.success) throw new Error(data.message || 'No se pudo guardar el modo.');
      if (routeModeLabel) routeModeLabel.textContent = enabled ? 'ACTIVADO' : 'DESACTIVADO';
      DiscourseLab.showToast(
        enabled ? 'Modo Ruta activado' : 'Modo Ruta desactivado',
        enabled ? 'Debes completar las actividades en orden para avanzar.' : 'Ahora puedes acceder libremente a las actividades.',
        'success',
      );
      window.setTimeout(() => window.location.reload(), 350);
    } catch (error) {
      routeModeToggle.checked = !enabled;
      routeModeToggle.disabled = false;
      DiscourseLab.showToast('No se pudo guardar', error.message, 'danger');
    }
  });

  const notifToggle = document.getElementById('notifToggle');
  const notifPanel = document.getElementById('notifPanel');
  const notifClose = document.getElementById('notifClose');
  notifToggle?.addEventListener('click', () => notifPanel?.classList.toggle('open'));
  notifClose?.addEventListener('click', () => notifPanel?.classList.remove('open'));
  document.querySelectorAll('.dl-notif-item.unread').forEach((item) => {
    item.addEventListener('click', () => {
      item.classList.remove('unread');
      DiscourseLab.showToast('Notificación leída', 'La marcamos como revisada.', 'success');
    });
  });
  document.addEventListener('click', (e) => {
    if (notifPanel?.classList.contains('open') && !notifPanel.contains(e.target) && !notifToggle?.contains(e.target)) {
      notifPanel.classList.remove('open');
    }
  });

  const searchTrigger = document.getElementById('searchTrigger');
  const searchOverlay = document.getElementById('searchOverlay');
  const searchInput = document.getElementById('searchInput');
  const openSearch = () => {
    searchOverlay?.classList.add('open');
    setTimeout(() => searchInput?.focus(), 100);
  };
  const closeSearch = () => searchOverlay?.classList.remove('open');
  searchTrigger?.addEventListener('click', openSearch);
  searchOverlay?.addEventListener('click', (e) => { if (e.target === searchOverlay) closeSearch(); });
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape') { closeSearch(); notifPanel?.classList.remove('open'); }
  });
  searchInput?.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    document.querySelectorAll('.dl-search-result').forEach((r) => {
      const title = r.dataset.title || r.textContent.toLowerCase();
      r.style.display = title.includes(q) ? 'flex' : 'none';
    });
  });

  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  sidebarToggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
    sidebarBackdrop?.classList.toggle('open');
  });
  sidebarBackdrop?.addEventListener('click', () => {
    sidebar?.classList.remove('open');
    sidebarBackdrop?.classList.remove('open');
  });

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.dl-reveal').forEach((el) => revealObserver.observe(el));

  document.querySelectorAll('.dl-progress-fill[data-progress]').forEach((el) => {
    const value = Number(el.dataset.progress);
    if (!Number.isNaN(value)) {
      el.style.width = `${value}%`;
    }
  });

  document.querySelectorAll('.activity-start').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const item = e.target.closest('.dl-activity-item');
      const name = item?.dataset.activity || 'Actividad';
      DiscourseLab.showToast('Actividad iniciada', `${name} — ¡buena suerte!`, 'success');
      btn.textContent = 'En curso…';
      btn.disabled = true;
      setTimeout(() => {
        DiscourseLab.showToast('+80 XP', 'Actividad completada con éxito', 'xp');
      }, 2500);
    });
  });

  document.querySelectorAll('.dl-achievement.unlocked').forEach((ach) => {
    ach.addEventListener('click', () => {
      const name = ach.querySelector('.dl-achievement-name')?.textContent;
      DiscourseLab.showToast('Logro desbloqueado', name || 'Nuevo logro', 'achievement');
    });
  });

  setTimeout(() => {
    if (document.querySelector('.dl-page') && !sessionStorage.getItem('dl-welcomed')) {
      sessionStorage.setItem('dl-welcomed', '1');
      DiscourseLab.showToast('Bienvenida de vuelta', 'Tu racha de estudio sigue activa.', 'success');
    }
  }, 1500);
});

window.DiscourseLab = DiscourseLab;

// Client-side minimal logger: sends structured events to backend for centralization
function sendClientLog(level, message, meta) {
  try {
    navigator.sendBeacon && typeof navigator.sendBeacon === 'function'
      ? navigator.sendBeacon('/api/client_log', JSON.stringify({ level, message, meta }))
      : fetch('/api/client_log', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ level, message, meta }) }).catch(() => {});
  } catch (e) {
    // swallow
  }
}

window.addEventListener('error', (ev) => {
  sendClientLog('ERROR', ev.message || 'uncaught_error', { filename: ev.filename, lineno: ev.lineno, colno: ev.colno });
});

window.addEventListener('unhandledrejection', (ev) => {
  const reason = ev.reason && (ev.reason.message || JSON.stringify(ev.reason)) || String(ev.reason);
  sendClientLog('ERROR', `unhandledrejection: ${reason}`, {});
});
