'use strict';

/* Single-transaction limit from the OSU procedure. A charge above it is marked
   in the results -- a lead for follow-up, not a finding. */
var SINGLE_TXN_LIMIT = 5000;

/* ============================================================== theme ==== */
(function () {
  var btn = document.getElementById('theme-toggle');
  if (!btn) { return; }
  btn.addEventListener('click', function () {
    var root = document.documentElement;
    var explicit = root.getAttribute('data-theme');
    var dark = explicit
      ? explicit === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches;
    var next = dark ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('pcard-theme', next); } catch (e) {}
    // The chart's colours come from CSS variables, so it has to be redrawn.
    if (lastSearch) { drawChart(lastSearch); }
  });
})();

/* =============================================================== tabs ==== */
document.querySelectorAll('.tab').forEach(function (tab) {
  tab.addEventListener('click', function () {
    document.querySelectorAll('.tab').forEach(function (t) {
      t.classList.toggle('is-active', t === tab);
      t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
    });
    document.querySelectorAll('.panel').forEach(function (p) {
      p.classList.toggle('is-active', p.id === 'tab-' + tab.dataset.tab);
    });
    window.scrollTo({ top: 0 });
  });
});

/* ============================================================ helpers ==== */
var MONEY_COLS = ['Amount', 'Total', 'Spend', 'Value', 'Overpayment', 'Charge', 'Sum', 'Largest', 'Avg'];
// Identifiers and periods are numbers but must not get thousands separators.
var PLAIN_COLS = ['Year', 'Month', 'MonthNo', 'ID', 'AgencyNumber', 'Digit'];
var MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function isMoney(col) {
  return MONEY_COLS.some(function (m) { return col.indexOf(m) !== -1; });
}

function fmtMoney(v, compact) {
  if (v === null || v === undefined || v === '') { return ''; }
  var n = Number(v);
  if (!isFinite(n)) { return String(v); }
  if (compact) {
    var a = Math.abs(n);
    // Drop a trailing .0 so a tick reads $6k, not $6.0k.
    var trim = function (x) { return x.toFixed(1).replace(/\.0$/, ''); };
    if (a >= 1e6) { return trim(n / 1e6) + 'M'; }
    if (a >= 1e3) { return trim(n / 1e3) + 'k'; }
    return String(Math.round(n));
  }
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function fmtNumber(v) {
  var n = Number(v);
  return isFinite(n) ? n.toLocaleString('en-US') : String(v);
}

function cleanDate(v) {
  // '7/26/2014 0:00:00' -> '7/26/2014'
  return typeof v === 'string' ? v.replace(/\s+0:00:00$/, '') : v;
}

function showError(el, message) {
  el.textContent = message;
  el.classList.remove('hidden');
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function svgEl(name, attrs) {
  var e = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
  return e;
}

/* ======================================================= sortable table == */
/* Each table keeps its own rows and sort state, so sorting is done on the
   underlying values rather than on the rendered text. */
var tableState = {};

function renderTable(table, columns, rows, opts) {
  opts = opts || {};
  var id = table.id;
  if (!tableState[id] || opts.reset !== false) {
    tableState[id] = { columns: columns, rows: rows, sortCol: null, sortDir: 1 };
  }
  paintTable(table);
}

function paintTable(table) {
  var st = tableState[table.id];
  var columns = st.columns;
  var rows = st.rows.slice();

  table.innerHTML = '';

  if (!rows.length) {
    var cap = document.createElement('caption');
    cap.className = 'empty';
    cap.style.captionSide = 'bottom';
    cap.innerHTML = '<strong>No transactions matched.</strong>' +
      'Try a shorter or more general keyword, clear the minimum amount, or widen the year.';
    table.appendChild(cap);
    return;
  }

  if (st.sortCol !== null) {
    var c = st.sortCol, dir = st.sortDir;
    rows.sort(function (a, b) {
      var x = a[c], y = b[c];
      if (x === null || x === undefined) { return 1; }
      if (y === null || y === undefined) { return -1; }
      if (typeof x === 'number' && typeof y === 'number') { return (x - y) * dir; }
      return String(x).localeCompare(String(y), 'en') * dir;
    });
  }

  var thead = document.createElement('thead');
  var hr = document.createElement('tr');
  columns.forEach(function (col) {
    var th = document.createElement('th');
    th.className = 'sortable' + (st.sortCol === col ? ' is-sorted' : '');
    th.textContent = col;
    var arrow = document.createElement('span');
    arrow.className = 'arrow';
    arrow.textContent = st.sortCol === col ? (st.sortDir === 1 ? '▲' : '▼') : '▴';
    th.appendChild(arrow);
    th.title = 'Sort by ' + col;
    th.addEventListener('click', function () {
      if (st.sortCol === col) { st.sortDir = -st.sortDir; }
      else { st.sortCol = col; st.sortDir = isMoney(col) ? -1 : 1; }
      paintTable(table);
    });
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  table.appendChild(thead);

  var tbody = document.createElement('tbody');
  rows.forEach(function (row) {
    var tr = document.createElement('tr');
    columns.forEach(function (col) {
      var td = document.createElement('td');
      var v = row[col];

      if (isMoney(col) && typeof v === 'number') {
        td.className = 'num' + (v < 0 ? ' neg' : '');
        td.textContent = fmtMoney(v);
        // Mark the charges that breach the single-transaction limit.
        if (col === 'Amount' && v > SINGLE_TXN_LIMIT) {
          var f = document.createElement('span');
          f.className = 'flag';
          f.textContent = 'over $5,000';
          f.title = 'Above the $5,000 single-transaction limit';
          td.appendChild(f);
        } else if (col === 'Amount' && v < 0) {
          var cr = document.createElement('span');
          cr.className = 'flag';
          cr.textContent = 'credit';
          cr.title = 'A negative amount: a credit or a return';
          td.appendChild(cr);
        }
      } else if (typeof v === 'number') {
        td.className = 'num';
        td.textContent = PLAIN_COLS.indexOf(col) !== -1 ? String(v) : fmtNumber(v);
      } else if (/Date$/.test(col)) {
        td.className = 'num';
        td.textContent = cleanDate(v);
      } else {
        if (col === 'Description' || col === 'MCC' || col === 'Vendor') { td.className = 'wrap'; }
        if (col === 'Cardholder' || col === 'FullName') { td.className = 'strong'; }
        td.textContent = v === null || v === undefined ? '' : String(v);
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

/* ============================================================== chart ==== */
/* Spend per month over the whole matching population. One series, so no legend
   is needed -- the heading names it. Colours come from CSS variables so the
   theme toggle and the OS setting both work. */
var lastSearch = null;

function drawChart(data) {
  var card = document.getElementById('chart-card');
  var svg = document.getElementById('chart');
  var tip = document.getElementById('chart-tip');
  var months = fillMonths((data && data.monthly) || []);

  if (months.length < 2) { card.classList.add('hidden'); return; }
  card.classList.remove('hidden');

  var multiYear = months.some(function (m) { return m.Year !== months[0].Year; });
  document.getElementById('chart-note').textContent =
    months.length + (multiYear ? ' months across the selected years' : ' months');

  var W = 1000, H = 210;
  var padL = 54, padR = 14, padT = 16, padB = 28;
  var plotW = W - padL - padR, plotH = H - padT - padB;

  var totals = months.map(function (m) { return m.total || 0; });
  var ticks = 4;

  // The peak month, found in the data. Kept separate from the axis maximum
  // below, which is rounded outward and so is usually not an actual value.
  var dataMax = Math.max.apply(null, totals.concat([0]));
  var dataMin = Math.min.apply(null, totals.concat([0]));
  var maxIdx = totals.indexOf(dataMax);

  // Round the scale out to a whole tick step, so the axis reads $0 / $6k / $12k
  // rather than $0 / $6.1k / $12.2k.
  var step0 = niceStep((dataMax - dataMin) / ticks);
  var maxV = Math.ceil(dataMax / step0) * step0;
  var minV = Math.floor(dataMin / step0) * step0;
  var span = (maxV - minV) || 1;
  var zeroY = padT + plotH * (maxV / span);

  var step = plotW / months.length;
  var gap = 2;                                   // surface gap between bars
  var barW = Math.max(2, Math.min(38, step - gap));
  var radius = Math.min(4, barW / 2);

  svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  svg.innerHTML = '';

  // recessive solid hairline grid + tick labels
  for (var i = 0; i <= ticks; i++) {
    var val = minV + (span * i / ticks);
    var y = padT + plotH - (plotH * i / ticks);
    svg.appendChild(svgEl('line', {
      class: 'grid-line', x1: padL, x2: W - padR, y1: y.toFixed(1), y2: y.toFixed(1)
    }));
    var lab = svgEl('text', {
      class: 'axis-text', x: padL - 8, y: (y + 3.5).toFixed(1), 'text-anchor': 'end'
    });
    lab.textContent = '$' + fmtMoney(val, true).replace('$', '');
    svg.appendChild(lab);
  }

  months.forEach(function (m, idx) {
    var v = m.total || 0;
    var x = padL + idx * step + (step - barW) / 2;
    var top = padT + plotH * ((maxV - v) / span);
    var h = Math.abs(zeroY - top);
    var up = v >= 0;
    var yTop = up ? top : zeroY;
    var hh = Math.max(1.5, h);

    var bar = svgEl('path', {
      class: 'bar' + (idx === maxIdx ? ' is-on' : ''),
      d: barPath(x, yTop, barW, hh, radius, up)
    });
    svg.appendChild(bar);

    // x-axis label: keep it readable when there are many months
    var everyN = months.length > 24 ? 6 : (months.length > 14 ? 2 : 1);
    if (idx % everyN === 0) {
      var t = svgEl('text', {
        class: 'axis-text', x: (x + barW / 2).toFixed(1), y: H - 9, 'text-anchor': 'middle'
      });
      t.textContent = multiYear
        ? MONTH_NAMES[(m.Month || 1) - 1] + ' ' + String(m.Year).slice(2)
        : MONTH_NAMES[(m.Month || 1) - 1];
      svg.appendChild(t);
    }

    // Direct-label the peak only -- a number on every bar goes unread.
    if (idx === maxIdx && hh > 14) {
      var dl = svgEl('text', {
        class: 'bar-label', x: (x + barW / 2).toFixed(1),
        y: (up ? yTop - 5 : yTop + hh + 12).toFixed(1), 'text-anchor': 'middle'
      });
      dl.textContent = fmtMoney(v, true);
      svg.appendChild(dl);
    }

    // A generous transparent hit area: the bar can be 2px wide, the target is not.
    var hit = svgEl('rect', {
      class: 'bar-hit', x: (padL + idx * step).toFixed(1), y: padT,
      width: Math.max(step, 12).toFixed(1), height: plotH
    });
    hit.addEventListener('mouseenter', function () {
      svg.classList.add('is-hovered');
      svg.querySelectorAll('.bar').forEach(function (b, bi) {
        b.classList.toggle('is-on', bi === idx);
      });
      var label = MONTH_NAMES[(m.Month || 1) - 1] + ' ' + m.Year;
      tip.innerHTML = '<div class="tip-k">' + label + '</div>' +
        '<div class="tip-v">' + fmtMoney(v) + '</div>' +
        '<div class="tip-k">' + fmtNumber(m.n) + ' transaction' + (m.n === 1 ? '' : 's') + '</div>';
      var rect = svg.getBoundingClientRect();
      var scale = rect.width / W;
      tip.style.left = ((padL + idx * step + step / 2) * scale) + 'px';
      tip.style.top = ((up ? yTop : zeroY) * scale) + 'px';
      tip.classList.add('is-on');
    });
    hit.addEventListener('mouseleave', function () {
      svg.classList.remove('is-hovered');
      svg.querySelectorAll('.bar').forEach(function (b, bi) {
        b.classList.toggle('is-on', bi === maxIdx);
      });
      tip.classList.remove('is-on');
    });
    svg.appendChild(hit);
  });

  // zero baseline, drawn last so it sits above the bars
  if (minV < 0) {
    svg.appendChild(svgEl('line', {
      class: 'grid-line', x1: padL, x2: W - padR,
      y1: zeroY.toFixed(1), y2: zeroY.toFixed(1)
    }));
  }
}

/* A month with no matching charge comes back missing, not as zero. Left as-is
   the bars would sit side by side and the axis would imply a continuous run of
   months that isn't there, so the gaps are filled in with zeroes. */
function fillMonths(rows) {
  if (rows.length < 2) { return rows.slice(); }
  var key = function (y, m) { return y * 12 + (m - 1); };
  var byKey = {};
  rows.forEach(function (r) { byKey[key(r.Year, r.Month)] = r; });

  var first = key(rows[0].Year, rows[0].Month);
  var last = key(rows[rows.length - 1].Year, rows[rows.length - 1].Month);

  // A pathological range would make a huge chart; fall back to what we got.
  if (last - first > 240) { return rows.slice(); }

  var out = [];
  for (var k = first; k <= last; k++) {
    out.push(byKey[k] || {
      Year: Math.floor(k / 12), Month: (k % 12) + 1, n: 0, total: 0
    });
  }
  return out;
}

/* Round a raw step up to 1, 2, 2.5 or 5 times a power of ten. */
function niceStep(raw) {
  if (!(raw > 0)) { return 1; }
  var mag = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
  var norm = raw / mag;
  var snap = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10;
  return snap * mag;
}

/* Rounded data-end, square end anchored to the baseline. */
function barPath(x, y, w, h, r, up) {
  r = Math.min(r, w / 2, h);
  if (up) {
    return 'M' + x + ',' + (y + h) +
           'L' + x + ',' + (y + r) +
           'Q' + x + ',' + y + ' ' + (x + r) + ',' + y +
           'L' + (x + w - r) + ',' + y +
           'Q' + (x + w) + ',' + y + ' ' + (x + w) + ',' + (y + r) +
           'L' + (x + w) + ',' + (y + h) + 'Z';
  }
  return 'M' + x + ',' + y +
         'L' + x + ',' + (y + h - r) +
         'Q' + x + ',' + (y + h) + ' ' + (x + r) + ',' + (y + h) +
         'L' + (x + w - r) + ',' + (y + h) +
         'Q' + (x + w) + ',' + (y + h) + ' ' + (x + w) + ',' + (y + h - r) +
         'L' + (x + w) + ',' + y + 'Z';
}

/* ============================================================== TAB 1 ==== */
var askForm = document.getElementById('ask-form');
var askBtn = document.getElementById('ask-btn');
var askStatus = document.getElementById('ask-status');
var askErr = document.getElementById('ask-error');
var askResults = document.getElementById('ask-results');
var questionBox = document.getElementById('question');
var lastSql = null;

document.querySelectorAll('[data-example]').forEach(function (chip) {
  chip.addEventListener('click', function () {
    questionBox.value = chip.dataset.example;
    askForm.requestSubmit();
  });
});

document.getElementById('ask-clear').addEventListener('click', function () {
  questionBox.value = '';
  askResults.classList.add('hidden');
  askErr.classList.add('hidden');
  askStatus.textContent = '';
  questionBox.focus();
});

// Cmd/Ctrl + Enter submits, which is what anyone typing in a textarea expects.
questionBox.addEventListener('keydown', function (e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    askForm.requestSubmit();
  }
});

/* recent questions, kept per browser only */
function loadHistory() {
  try { return JSON.parse(localStorage.getItem('pcard-history') || '[]'); }
  catch (e) { return []; }
}

function saveHistory(list) {
  try { localStorage.setItem('pcard-history', JSON.stringify(list.slice(0, 8))); }
  catch (e) {}
}

function rememberQuestion(q) {
  var list = loadHistory().filter(function (x) { return x !== q; });
  list.unshift(q);
  saveHistory(list);
  renderHistory();
}

function renderHistory() {
  var list = loadHistory();
  var wrap = document.getElementById('history-wrap');
  var box = document.getElementById('history');
  if (!list.length) { wrap.classList.add('hidden'); return; }
  wrap.classList.remove('hidden');
  box.innerHTML = '';
  list.forEach(function (q) {
    var b = document.createElement('button');
    b.className = 'chip';
    b.textContent = q.length > 62 ? q.slice(0, 60) + '…' : q;
    b.title = q;
    b.addEventListener('click', function () {
      questionBox.value = q;
      askForm.requestSubmit();
    });
    box.appendChild(b);
  });
}
renderHistory();

document.getElementById('copy-sql').addEventListener('click', function () {
  if (!lastSql) { return; }
  var done = function () {
    var s = document.getElementById('copy-status');
    s.textContent = 'Copied.';
    setTimeout(function () { s.textContent = ''; }, 1800);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(lastSql).then(done, function () {});
  }
});

document.getElementById('ask-csv').addEventListener('click', function () {
  if (!lastSql) { return; }
  var btn = this;
  btn.disabled = true;
  // The query has to be POSTed as JSON, so fetch it and hand the browser a blob
  // rather than navigating -- a plain link cannot carry a request body.
  fetch('/api/ask.csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql: lastSql })
  })
    .then(function (r) {
      if (!r.ok) { return r.text().then(function (t) { throw new Error(t.slice(0, 200)); }); }
      return r.blob();
    })
    .then(function (blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'pcard_question_result.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
    })
    .catch(function (err) {
      showError(askErr, 'The export failed: ' + (err ? err.message : 'unknown error'));
    })
    .finally(function () { btn.disabled = false; });
});

askForm.addEventListener('submit', function (event) {
  event.preventDefault();
  var question = questionBox.value.trim();
  if (!question) { return; }

  askErr.classList.add('hidden');
  askBtn.disabled = true;
  askStatus.innerHTML = '<span class="spinner"></span> Writing and running the query…';
  askResults.classList.add('is-loading');

  // A model call is slow, and a host's proxy may abandon the request and answer
  // with its own HTML error page. Give up first, with our own message, so the
  // auditor is never shown a JSON parse error.
  var ctl = ('AbortController' in window) ? new AbortController() : null;
  var timer = setTimeout(function () { if (ctl) { ctl.abort(); } }, 95000);

  fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: question }),
    signal: ctl ? ctl.signal : undefined
  })
    .then(function (r) {
      // Read as text first: an error page from the host in front of this app is
      // HTML, and r.json() on it throws something that means nothing to a user.
      return r.text().then(function (body) {
        try {
          return { status: r.status, data: JSON.parse(body) };
        } catch (e) {
          throw new Error(
            r.status >= 500
              ? 'the server took too long and the request was dropped (HTTP ' +
                r.status + '). The model was probably busy — wait a moment and ask again.'
              : 'the server sent an unexpected reply (HTTP ' + r.status + ').'
          );
        }
      });
    })
    .then(function (res) {
      var d = res.data;
      askStatus.textContent = '';

      // Show the query and explanation whenever we got them, even on failure --
      // a rejected or broken query is itself useful information for the auditor.
      lastSql = d.sql || null;
      if (d.sql) {
        document.getElementById('ask-sql').textContent = d.sql;
        document.getElementById('ask-sql-wrap').classList.remove('hidden');
      } else {
        document.getElementById('ask-sql-wrap').classList.add('hidden');
      }
      document.getElementById('ask-explanation').textContent = d.explanation || '';
      document.getElementById('ask-unanswerable')
        .classList.toggle('hidden', d.answerable !== false);

      if (!d.ok) {
        showError(askErr, d.error || 'The request failed.');
        if (d.sql || d.explanation) {
          askResults.classList.remove('hidden');
          renderTable(document.getElementById('ask-table'), [], []);
          document.getElementById('ask-rowcount').textContent = '';
        }
        return;
      }

      rememberQuestion(question);
      askResults.classList.remove('hidden');
      renderTable(document.getElementById('ask-table'), d.columns, d.rows);
      document.getElementById('ask-rowcount').textContent =
        fmtNumber(d.rowcount) + ' row' + (d.rowcount === 1 ? '' : 's') +
        (d.truncated ? ' (capped at 500 — narrow the question for the full population)' : '') +
        (d.model ? ' · ' + d.model : '');
    })
    .catch(function (err) {
      askStatus.textContent = '';
      if (err && err.name === 'AbortError') {
        showError(askErr,
          'The question took more than 95 seconds and was cancelled. That normally ' +
          'means the model provider is busy rather than anything wrong with the ' +
          'question — wait a moment and ask again. The Prohibited purchases tab does ' +
          'not use the model and keeps working.');
      } else {
        showError(askErr, 'The request failed: ' + (err ? err.message : 'unknown error'));
      }
    })
    .finally(function () {
      clearTimeout(timer);
      askBtn.disabled = false;
      askResults.classList.remove('is-loading');
    });
});

/* ============================================================== TAB 2 ==== */
var searchErr = document.getElementById('search-error');
var searchResults = document.getElementById('search-results');
var qDesc = document.getElementById('q-desc');
var qVend = document.getElementById('q-vend');

function currentFilters() {
  return {
    year: document.getElementById('year').value,
    min_amount: document.getElementById('min-amount').value
  };
}

/* `terms` is one keyword or a list; a list is OR-ed by the server. */
function runSearch(field, terms, label) {
  if (typeof terms === 'string') { terms = [terms]; }
  terms = terms.map(function (t) { return (t || '').trim(); }).filter(Boolean);
  if (!terms.length) {
    showError(searchErr, 'Enter a keyword in the ' + field.toLowerCase() + ' search box first.');
    return;
  }
  searchErr.classList.add('hidden');

  var f = currentFilters();
  var params = new URLSearchParams();
  params.set('field', field);
  terms.forEach(function (t) { params.append('q', t); });
  if (f.year) { params.set('year', f.year); }
  if (f.min_amount) { params.set('min_amount', f.min_amount); }

  var title = document.getElementById('search-title');
  searchResults.classList.remove('hidden');
  searchResults.classList.add('is-loading');
  title.innerHTML = '<span class="spinner"></span> Searching…';

  fetch('/api/search?' + params.toString())
    .then(function (r) {
      return r.text().then(function (body) {
        try { return JSON.parse(body); }
        catch (e) { throw new Error('the server sent an unexpected reply (HTTP ' + r.status + ').'); }
      });
    })
    .then(function (d) {
      if (!d.ok) {
        showError(searchErr, d.error || 'The search failed.');
        searchResults.classList.add('hidden');
        return;
      }

      lastSearch = d;
      var scope = f.year ? f.year : 'all years';
      var what = field === 'Vendor' ? 'Vendor' : 'Description';
      title.textContent = label
        ? label + ' — ' + what.toLowerCase() + ' terms — ' + scope
        : what + ' contains “' + terms[0] + '” — ' + scope;

      var s = d.summary || {};
      var tiles = [
        ['Transactions', fmtNumber(s.n || 0), false],
        ['Net amount', fmtMoney(s.total || 0), false],
        ['Largest', fmtMoney(s.largest || 0), false],
        ['Cardholders', fmtNumber(s.cardholders || 0), false],
        ['Vendors', fmtNumber(s.vendors || 0), false]
      ];
      if (s.over_limit) {
        tiles.push(['Over $5,000', fmtNumber(s.over_limit), true]);
      }
      if (s.credits) {
        tiles.push(['Credits', fmtNumber(s.credits), false]);
      }
      document.getElementById('search-stats').innerHTML = tiles.map(function (t) {
        return '<div class="stat' + (t[2] ? ' is-flag' : '') + '">' +
               '<div class="k">' + t[0] + '</div><div class="v">' + t[1] + '</div></div>';
      }).join('');

      var topWrap = document.getElementById('top-cardholders');
      var top = d.top_cardholders || [];
      if (top.length > 1) {
        topWrap.classList.remove('hidden');
        topWrap.innerHTML = '<span class="muted">Most exposed cardholders:</span>' +
          top.map(function (t) {
            return '<span class="pill"><b>' + t.Cardholder + '</b> ' +
                   fmtMoney(t.total) + ' · ' + t.n + '</span>';
          }).join('');
      } else {
        topWrap.classList.add('hidden');
      }

      document.getElementById('search-note').textContent = d.truncated
        ? 'Showing the 500 largest by absolute amount — export the CSV for the full population.'
        : 'Sorted by absolute amount. Click a header to re-sort.';

      renderTable(document.getElementById('search-table'), d.columns, d.rows);
      drawChart(d);
      document.getElementById('csv-link').href = '/api/search.csv?' + params.toString();
      searchResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    })
    .catch(function (err) {
      showError(searchErr, 'The search failed: ' + (err ? err.message : 'unknown error'));
      searchResults.classList.add('hidden');
    })
    .finally(function () { searchResults.classList.remove('is-loading'); });
}

document.getElementById('form-desc').addEventListener('submit', function (e) {
  e.preventDefault();
  runSearch('Description', qDesc.value);
});

document.getElementById('form-vend').addEventListener('submit', function (e) {
  e.preventDefault();
  runSearch('Vendor', qVend.value);
});

// A single term: load it into the box it belongs to, then search.
document.querySelectorAll('.cat .chip[data-term]').forEach(function (chip) {
  chip.addEventListener('click', function () {
    var field = chip.dataset.field;
    var term = chip.dataset.term;
    if (field === 'Vendor') { qVend.value = term; } else { qDesc.value = term; }
    runSearch(field, term);
  });
});

// Every term in a category at once. Description and vendor terms search
// different columns, so whichever list is longer is the more complete test --
// run that one and say so.
document.querySelectorAll('.cat .chip[data-all]').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var cat = (window.CATEGORIES || []).filter(function (c) {
      return c.key === btn.dataset.all;
    })[0];
    if (!cat) { return; }
    var useVendor = (cat.vendor || []).length > (cat.description || []).length;
    var field = useVendor ? 'Vendor' : 'Description';
    var terms = useVendor ? cat.vendor : cat.description;
    if (!terms.length) { return; }
    if (useVendor) { qVend.value = terms.join(', '); } else { qDesc.value = terms.join(', '); }
    runSearch(field, terms, cat.label);
  });
});

// Changing the year or the minimum re-runs whatever search is on screen.
['year', 'min-amount'].forEach(function (id) {
  document.getElementById(id).addEventListener('change', function () {
    if (!lastSearch) { return; }
    var terms = lastSearch.terms || [];
    var field = (lastSearch.sql || '').indexOf('UPPER(Vendor)') !== -1 ? 'Vendor' : 'Description';
    if (terms.length) { runSearch(field, terms, terms.length > 1 ? 'Selected' : null); }
  });
});

window.addEventListener('resize', function () {
  if (lastSearch) { drawChart(lastSearch); }
});
