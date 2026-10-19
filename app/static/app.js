// State Management
let currentUsers = [];
let chartLastOp = null;
let chartAggregated = null;
let currentTab = 'users';

const DB_DISPLAY_NAMES = {
  postgres: 'PostgreSQL',
  sqlite: 'SQLite',
  mysql: 'MySQL',
  mongodb: 'MongoDB',
  mssql: 'MsSQL',
  oracle: 'Oracle'
};

const DB_COLORS = {
  postgres: '#336791',
  sqlite: '#003B57',
  mysql: '#00758F',
  mongodb: '#13AA52',
  mssql: '#CC292B',
  oracle: '#F80000'
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  loadStatuses();
  loadUsers();
  loadStats();
  lucide.createIcons();

  // Periodic status refresh every 20 seconds
  setInterval(loadStatuses, 20000);
});

// ---------------- CHARTS INITIALIZATION ---------------- //

function initCharts() {
  // Chart 1: Last Operation Latency
  const ctxLast = document.getElementById('chartLastOp').getContext('2d');
  chartLastOp = new Chart(ctxLast, {
    type: 'bar',
    data: {
      labels: Object.values(DB_DISPLAY_NAMES),
      datasets: [{
        label: 'Время отклика (мс)',
        data: [0, 0, 0, 0, 0, 0],
        backgroundColor: [
          '#38bdf8', '#38bdf8', '#38bdf8', '#38bdf8', '#38bdf8', '#38bdf8'
        ],
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#0284c7'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y} мс`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', callback: (v) => `${v} мс` }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#cbd5e1', font: { weight: 'bold' } }
        }
      }
    }
  });

  // Chart 2: Aggregated Operations Comparison
  const ctxAgg = document.getElementById('chartAggregated').getContext('2d');
  chartAggregated = new Chart(ctxAgg, {
    type: 'bar',
    data: {
      labels: Object.values(DB_DISPLAY_NAMES),
      datasets: []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#cbd5e1', font: { size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} мс`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', callback: (v) => `${v} мс` }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#cbd5e1', font: { weight: 'bold' } }
        }
      }
    }
  });
}

function updateLastOpChart(opName, timings) {
  const badge = document.getElementById('lastOpBadge');
  badge.textContent = `Операция: ${opName}`;

  const keys = ['postgres', 'sqlite', 'mysql', 'mongodb', 'mssql', 'oracle'];
  const data = keys.map(k => timings[k] !== undefined && timings[k] >= 0 ? timings[k] : 0);

  chartLastOp.data.datasets[0].data = data;
  chartLastOp.update();

  // Render timing badges
  renderTimingBadges(timings);
}

function renderTimingBadges(timings) {
  const container = document.getElementById('timingsBadges');
  container.innerHTML = '';

  const keys = ['postgres', 'sqlite', 'mysql', 'mongodb', 'mssql', 'oracle'];
  keys.forEach(k => {
    const val = timings[k];
    const span = document.createElement('span');
    span.className = 'px-2 py-0.5 rounded text-xs font-mono font-medium border flex items-center gap-1.5';
    
    if (val === undefined) {
      span.className += ' bg-slate-800/60 text-slate-500 border-slate-700/50';
      span.textContent = `${DB_DISPLAY_NAMES[k]}: -`;
    } else if (val < 0) {
      span.className += ' bg-rose-950/40 text-rose-400 border-rose-800/40';
      span.textContent = `${DB_DISPLAY_NAMES[k]}: Ошибка`;
    } else {
      span.className += ' bg-cyan-950/40 text-cyan-300 border-cyan-800/40';
      span.textContent = `${DB_DISPLAY_NAMES[k]}: ${val} мс`;
    }
    container.appendChild(span);
  });
}

// ---------------- DATA & STATUS LOADING ---------------- //

async function loadStatuses() {
  try {
    const res = await axios.get('/api/status');
    const statuses = res.data;
    renderStatusGrid(statuses);
    document.getElementById('statusLastUpdated').textContent = `Обновлено: ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    console.error('Ошибка проверки статуса БД:', err);
  }
}

function renderStatusGrid(statuses) {
  const grid = document.getElementById('statusGrid');
  grid.innerHTML = '';

  statuses.forEach(item => {
    const isOnline = item.connected;
    const card = document.createElement('div');
    card.className = `p-3.5 rounded-xl border transition shadow-sm flex flex-col justify-between ${
      isOnline ? 'bg-slate-900/90 border-slate-800 hover:border-slate-700' : 'bg-rose-950/10 border-rose-900/30'
    }`;

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-white tracking-wide">${item.display_name}</span>
        <span class="flex h-2.5 w-2.5 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isOnline ? 'bg-emerald-400' : 'bg-rose-500'}"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}"></span>
        </span>
      </div>
      <div class="mt-2 flex items-baseline justify-between text-xs">
        <span class="text-slate-400 font-medium">Записей:</span>
        <span class="font-mono font-bold ${isOnline ? 'text-cyan-400' : 'text-slate-500'}">
          ${isOnline ? item.records_count.toLocaleString() : 'Offline'}
        </span>
      </div>
      <div class="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
        <span class="text-slate-500 font-mono">${isOnline ? `${item.latency_ms} мс` : 'Недоступна'}</span>
        <button onclick="seedData('${item.name}')" title="Заполнить 1000 записей" class="text-indigo-400 hover:text-indigo-300 font-medium transition">
          +1000
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

async function loadUsers(query = '', db = 'all') {
  try {
    const res = await axios.get('/api/users', { params: { q: query, db: db } });
    currentUsers = res.data.users || [];
    renderUsersTable(currentUsers);
    document.getElementById('userCountBadge').textContent = currentUsers.length;

    if (res.data.timings && Object.keys(res.data.timings).length > 0) {
      updateLastOpChart('SELECT (Поиск)', res.data.timings);
    }
  } catch (err) {
    showToast('Ошибка при загрузке пользователей', 'error');
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('usersTableBody');
  tbody.innerHTML = '';

  if (!users || users.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="py-12 text-center text-slate-500">
          <div class="flex flex-col items-center justify-center space-y-2">
            <i data-lucide="inbox" class="w-8 h-8 text-slate-600"></i>
            <span>Пользователи не найдены. Нажмите «Заполнить 1000 записей» или добавьте нового!</span>
          </div>
        </td>
      </tr>
    `;
    lucide.createIcons();
    return;
  }

  users.forEach(u => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-800/40 transition group';
    tr.innerHTML = `
      <td class="py-3 px-4 font-mono font-medium text-slate-400">${u.id}</td>
      <td class="py-3 px-4 font-semibold text-white">${escapeHtml(u.full_name)}</td>
      <td class="py-3 px-4 text-cyan-300">${escapeHtml(u.profession)}</td>
      <td class="py-3 px-4 text-slate-300">
        <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-xs">${escapeHtml(u.department || 'IT')}</span>
      </td>
      <td class="py-3 px-4 font-mono text-emerald-400">${(u.salary || 0).toLocaleString()} ₽</td>
      <td class="py-3 px-4 font-mono text-xs text-slate-400">${escapeHtml(u.created_at || '')}</td>
      <td class="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
        <button onclick="openEditUserModal(${u.id})" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition" title="Редактировать">
          <i data-lucide="edit-3" class="w-4 h-4"></i>
        </button>
        <button onclick="confirmDeleteUser(${u.id}, '${escapeHtml(u.full_name)}')" class="p-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900 text-rose-300 transition" title="Удалить">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  lucide.createIcons();
}

async function loadStats() {
  try {
    const res = await axios.get('/api/stats');
    const { aggregated, recent_logs } = res.data;

    // Update Aggregated Chart
    if (aggregated && aggregated.datasets) {
      chartAggregated.data.labels = aggregated.chart_labels;
      chartAggregated.data.datasets = aggregated.datasets;
      chartAggregated.update();
    }

    // Render Logs Table
    renderLogsTable(recent_logs || []);
  } catch (err) {
    console.error('Ошибка загрузки статистики:', err);
  }
}

function renderLogsTable(logs) {
  const tbody = document.getElementById('logsTableBody');
  tbody.innerHTML = '';

  if (!logs || logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">Логи пусты</td></tr>`;
    return;
  }

  logs.forEach(log => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-800/30 transition text-xs';

    let opBadge = 'bg-slate-800 text-slate-300';
    if (log.operation === 'SELECT') opBadge = 'bg-blue-950/60 text-blue-300 border border-blue-800/50';
    if (log.operation === 'INSERT') opBadge = 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/50';
    if (log.operation === 'UPDATE') opBadge = 'bg-amber-950/60 text-amber-300 border border-amber-800/50';
    if (log.operation === 'DELETE') opBadge = 'bg-rose-950/60 text-rose-300 border border-rose-800/50';
    if (log.operation === 'SEED') opBadge = 'bg-purple-950/60 text-purple-300 border border-purple-800/50';

    tr.innerHTML = `
      <td class="py-2.5 px-4 font-mono text-slate-400">${log.time_str}</td>
      <td class="py-2.5 px-4">
        <span class="px-2 py-0.5 rounded text-[11px] font-bold ${opBadge}">${log.operation}</span>
      </td>
      <td class="py-2.5 px-4 font-semibold text-slate-200">${DB_DISPLAY_NAMES[log.db_name] || log.db_name}</td>
      <td class="py-2.5 px-4 font-mono font-bold ${log.success ? 'text-cyan-400' : 'text-rose-400'}">
        ${log.duration_ms} мс
      </td>
      <td class="py-2.5 px-4 text-slate-300 font-mono">${log.affected_rows}</td>
      <td class="py-2.5 px-4 text-slate-400 truncate max-w-xs" title="${escapeHtml(log.details)}">
        ${escapeHtml(log.details)}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------- ACTIONS & CRUD ---------------- //

function handleSearch() {
  const query = document.getElementById('searchInput').value.trim();
  const targetDb = document.getElementById('selectTargetDb').value;
  loadUsers(query, targetDb);
}

function openCreateUserModal() {
  document.getElementById('modalTitle').textContent = 'Добавить нового пользователя';
  document.getElementById('formUserId').value = '';
  document.getElementById('formFullName').value = '';
  document.getElementById('formProfession').value = '';
  document.getElementById('formDepartment').value = 'Разработка';
  document.getElementById('formSalary').value = '150000';
  document.getElementById('userModal').classList.remove('hidden');
}

function openEditUserModal(userId) {
  const user = currentUsers.find(u => u.id === userId);
  if (!user) return;

  document.getElementById('modalTitle').textContent = `Редактировать: ${user.full_name} (ID: ${user.id})`;
  document.getElementById('formUserId').value = user.id;
  document.getElementById('formFullName').value = user.full_name;
  document.getElementById('formProfession').value = user.profession;
  document.getElementById('formDepartment').value = user.department || 'IT';
  document.getElementById('formSalary').value = user.salary || 100000;
  document.getElementById('userModal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('userModal').classList.add('hidden');
}

async function saveUser() {
  const userId = document.getElementById('formUserId').value;
  const fullName = document.getElementById('formFullName').value.trim();
  const profession = document.getElementById('formProfession').value.trim();
  const department = document.getElementById('formDepartment').value.trim();
  const salary = parseInt(document.getElementById('formSalary').value) || 0;
  const targetDb = document.getElementById('formTargetDb').value;

  const btn = document.getElementById('btnSaveUser');
  btn.disabled = true;

  try {
    if (userId) {
      // UPDATE
      const res = await axios.put(`/api/users/${userId}?db=${targetDb}`, {
        full_name: fullName,
        profession: profession,
        department: department,
        salary: salary
      });
      showToast(`Пользователь #${userId} успешно обновлен`, 'success');
      if (res.data.timings) updateLastOpChart('UPDATE', res.data.timings);
    } else {
      // CREATE
      const res = await axios.post(`/api/users?db=${targetDb}`, {
        full_name: fullName,
        profession: profession,
        department: department,
        salary: salary
      });
      showToast(`Пользователь создан (ID: ${res.data.user.id})`, 'success');
      if (res.data.timings) updateLastOpChart('INSERT', res.data.timings);
    }

    closeModal();
    loadUsers();
    loadStats();
    loadStatuses();
  } catch (err) {
    showToast('Ошибка при сохранении пользователя', 'error');
  } finally {
    btn.disabled = false;
  }
}

async function confirmDeleteUser(userId, name) {
  if (!confirm(`Вы действительно хотите удалить пользователя "${name}" (ID: ${userId})?`)) return;

  try {
    const targetDb = document.getElementById('selectTargetDb').value;
    const res = await axios.delete(`/api/users/${userId}?db=${targetDb}`);
    showToast(`Пользователь #${userId} удален`, 'success');
    if (res.data.timings) updateLastOpChart('DELETE', res.data.timings);

    loadUsers();
    loadStats();
    loadStatuses();
  } catch (err) {
    showToast('Ошибка удаления пользователя', 'error');
  }
}

async function seedData(target = 'all') {
  const btn = document.getElementById('btnSeedAll');
  btn.disabled = true;
  btn.classList.add('opacity-50');
  showToast(`Загрузка 1000 записей в ${target === 'all' ? 'все базы' : target}...`, 'info');

  try {
    const res = await axios.post(`/api/seed?db=${target}`);
    showToast('1000 записей успешно загружены!', 'success');
    loadStatuses();
    loadUsers();
    loadStats();
  } catch (err) {
    showToast('Ошибка при сидинге данных', 'error');
  } finally {
    btn.disabled = false;
    btn.classList.remove('opacity-50');
  }
}

async function runBenchmarkSuite() {
  const btn = document.getElementById('btnRunBenchmark');
  btn.disabled = true;
  btn.classList.add('opacity-50');
  showToast('Запуск бенчмарка (SELECT, INSERT, UPDATE, DELETE)...', 'info');

  try {
    const res = await axios.post('/api/benchmark', { iterations: 10 });
    showToast('Бенчмарк успешно завершен! Графики обновлены.', 'success');
    loadStats();
    loadStatuses();
  } catch (err) {
    showToast('Ошибка запуска бенчмарка', 'error');
  } finally {
    btn.disabled = false;
    btn.classList.remove('opacity-50');
  }
}

async function clearStatsHistory() {
  if (!confirm('Очистить историю логов и графиков?')) return;
  try {
    await axios.post('/api/stats/clear');
    loadStats();
    showToast('История логов очищена', 'info');
  } catch (err) {
    showToast('Ошибка очистки статистики', 'error');
  }
}

// ---------------- TABS & UI HELPERS ---------------- //

function switchTab(tab) {
  currentTab = tab;
  const btnUsers = document.getElementById('tabBtnUsers');
  const btnLogs = document.getElementById('tabBtnLogs');
  const contentUsers = document.getElementById('tabContentUsers');
  const contentLogs = document.getElementById('tabContentLogs');

  if (tab === 'users') {
    btnUsers.className = 'px-4 py-2.5 text-sm font-semibold border-b-2 border-cyan-500 text-cyan-400 transition flex items-center gap-2';
    btnLogs.className = 'px-4 py-2.5 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center gap-2';
    contentUsers.classList.remove('hidden');
    contentLogs.classList.add('hidden');
  } else {
    btnUsers.className = 'px-4 py-2.5 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center gap-2';
    btnLogs.className = 'px-4 py-2.5 text-sm font-semibold border-b-2 border-cyan-500 text-cyan-400 transition flex items-center gap-2';
    contentUsers.classList.add('hidden');
    contentLogs.classList.remove('hidden');
    loadStats();
  }
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  
  let bg = 'bg-slate-800 border-slate-700 text-white';
  if (type === 'success') bg = 'bg-emerald-950/90 border-emerald-700 text-emerald-200';
  if (type === 'error') bg = 'bg-rose-950/90 border-rose-700 text-rose-200';
  if (type === 'info') bg = 'bg-cyan-950/90 border-cyan-700 text-cyan-200';

  toast.className = `p-3 rounded-xl border shadow-xl text-xs font-medium max-w-sm pointer-events-auto fade-in flex items-center gap-2 ${bg}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
