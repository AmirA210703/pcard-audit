'use strict';

/* ------------------------------------------------------------------ tabs -- */
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

/* --------------------------------------------------------------- helpers -- */
var MONEY_COLS = ['Amount', 'Total', 'Spend', 'Value', 'Overpayment', 'Charge', 'Sum'];
// Identifiers and periods are numbers but must not get thousands separators.
var PLAIN_COLS = ['Year', 'Month', 'MonthNo', 'ID', 'AgencyNumber', 'Digit'];

function isMoney(col) {
  return MONEY_COLS.some(function (m) { return col.indexOf(m) !== -1; });
}

function fmtMoney(v) {
  if (v === null || v === undefined || v === '') { return ''; }
  var n = Number(v);
  if (!isFinite(n)) { return String(v); }
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

function renderTable(table, columns, rows) {
  table.innerHTML = '';
  if (!rows.length) {
    var p = document.createElement('caption');
    p.textContent = 'No transactions matched.';
    p.style.padding = '16px';
    p.style.captionSide = 'bottom';
    p.style.textAlign = 'left';
    p.style.color = '#5b6875';
    table.appendChild(p);
    return;
  }

  var thead = document.createElement('thead');
  var hr = document.createElement('tr');
  columns.forEach(function (c) {
    var th = document.createElement('th');
    th.textContent = c;
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  table.appendChild(thead);

  var tbody = document.createElement('tbody');
  rows.forEach(function (row) {
    var tr = document.createElement('tr');
    columns.forEach(function (c) {
      var td = document.createElement('td');
      var v = row[c];
      if (isMoney(c) && typeof v === 'number') {
        td.className = 'num' + (v < 0 ? ' neg' : '');
        td.textContent = fmtMoney(v);
      } else if (typeof v === 'number') {
        td.className = 'num';
        td.textContent = PLAIN_COLS.indexOf(c) !== -1 ? String(v) : fmtNumber(v);
      } else if (/Date$/.test(c)) {
        td.textContent = cleanDate(v);
      } else {
        if (c === 'Description' || c === 'MCC' || c === 'Vendor') { td.className = 'wrap'; }
        td.textContent = v === null || v === undefined ? '' : String(v);
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
}

function showError(el, message) {
  el.textContent = message;
  el.classList.remove('hidden');
}

/* =============================================================== TAB 1 ==== */
var askForm = document.getElementById('ask-form');
var askBtn = document.getElementById('ask-btn');
var askStatus = document.getElementById('ask-status');
var askErr = document.getElementById('ask-error');
var askResults = document.getElementById('ask-results');
var questionBox = document.getElementById('question');

document.querySelectorAll('[data-example]').forEach(function (chip) {
  chip.addEventListener('click', function () {
    questionBox.value = chip.dataset.example;
    questionBox.focus();
    askForm.requestSubmit();
  });
});

document.getElementById('ask-clear').addEventListener('click', function () {
  questionBox.value = '';
  askResults.classList.add('hidden');
  askErr.classList.add('hidden');
  askStatus.textContent = '';
});

askForm.addEventListener('submit', function (event) {
  event.preventDefault();
  var question = questionBox.value.trim();
  if (!question) { return; }

  askErr.classList.add('hidden');
  askBtn.disabled = true;
  askStatus.textContent = 'Writing and running the query…';

  fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: question })
  })
    .then(function (r) { return r.json().then(function (d) { return { status: r.status, data: d }; }); })
    .then(function (res) {
      var d = res.data;
      askStatus.textContent = '';

      // Show the query and explanation whenever we got them, even on failure --
      // a rejected or broken query is itself useful information for the auditor.
      if (d.sql) {
        document.getElementById('ask-sql').textContent = d.sql;
        document.getElementById('ask-sql-wrap').classList.remove('hidden');
      } else {
        document.getElementById('ask-sql-wrap').classList.add('hidden');
      }
      document.getElementById('ask-explanation').textContent = d.explanation || '';

      if (!d.ok) {
        showError(askErr, d.error || 'The request failed.');
        if (d.sql || d.explanation) {
          askResults.classList.remove('hidden');
          renderTable(document.getElementById('ask-table'), [], []);
          document.getElementById('ask-rowcount').textContent = '';
        }
        return;
      }

      askResults.classList.remove('hidden');
      renderTable(document.getElementById('ask-table'), d.columns, d.rows);
      document.getElementById('ask-rowcount').textContent =
        fmtNumber(d.rowcount) + ' row' + (d.rowcount === 1 ? '' : 's') +
        (d.truncated ? ' (capped at 500 — narrow the question for the full population)' : '');
    })
    .catch(function (err) {
      askStatus.textContent = '';
      showError(askErr, 'Could not reach the server: ' + err.message);
    })
    .finally(function () { askBtn.disabled = false; });
});

/* =============================================================== TAB 2 ==== */
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

function runSearch(field, keyword) {
  keyword = (keyword || '').trim();
  if (!keyword) {
    showError(searchErr, 'Enter a keyword in the ' + field.toLowerCase() + ' search box first.');
    return;
  }
  searchErr.classList.add('hidden');

  var f = currentFilters();
  var params = new URLSearchParams({ field: field, q: keyword });
  if (f.year) { params.set('year', f.year); }
  if (f.min_amount) { params.set('min_amount', f.min_amount); }

  var title = document.getElementById('search-title');
  title.textContent = 'Searching…';
  searchResults.classList.remove('hidden');

  fetch('/api/search?' + params.toString())
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d.ok) {
        searchResults.classList.add('hidden');
        showError(searchErr, d.error || 'The search failed.');
        return;
      }

      var scope = f.year ? f.year : 'all years';
      title.textContent = (field === 'Vendor' ? 'Vendor' : 'Description') +
        ' contains “' + keyword + '” — ' + scope;

      var s = d.summary || {};
      document.getElementById('search-stats').innerHTML = [
        ['Transactions', fmtNumber(s.n || 0)],
        ['Net amount', fmtMoney(s.total || 0)],
        ['Cardholders', fmtNumber(s.cardholders || 0)],
        ['Vendors', fmtNumber(s.vendors || 0)]
      ].map(function (kv) {
        return '<div class="stat"><div class="k">' + kv[0] + '</div><div class="v">' + kv[1] + '</div></div>';
      }).join('');

      document.getElementById('search-note').textContent = d.truncated
        ? 'Showing the 500 largest by absolute amount. Export the CSV for the full population, '
          + 'or raise the minimum amount to narrow it.'
        : 'Sorted by absolute amount, largest first. Every hit is a lead for follow-up, not a finding.';

      renderTable(document.getElementById('search-table'), d.columns, d.rows);
      document.getElementById('csv-link').href = '/api/search.csv?' + params.toString();
      searchResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    })
    .catch(function (err) {
      searchResults.classList.add('hidden');
      showError(searchErr, 'Could not reach the server: ' + err.message);
    });
}

document.getElementById('form-desc').addEventListener('submit', function (e) {
  e.preventDefault();
  runSearch('Description', qDesc.value);
});

document.getElementById('form-vend').addEventListener('submit', function (e) {
  e.preventDefault();
  runSearch('Vendor', qVend.value);
});

// Category term chips: load the term into the box it belongs to, then search.
document.querySelectorAll('.cat .chip').forEach(function (chip) {
  chip.addEventListener('click', function () {
    var field = chip.dataset.field;
    var term = chip.dataset.term;
    if (field === 'Vendor') {
      qVend.value = term;
    } else {
      qDesc.value = term;
    }
    runSearch(field, term);
  });
});
