(function () {
  function norm(value) { return (value || '').toString().toLowerCase(); }
  function initLocalFilters() {
    document.querySelectorAll('[data-v3-table-filter]').forEach(function(input) {
      var target = document.querySelector(input.getAttribute('data-v3-table-filter'));
      if (!target) return;
      input.addEventListener('input', function () {
        var q = norm(input.value);
        target.querySelectorAll('tbody tr').forEach(function (row) {
          row.hidden = q && norm(row.textContent).indexOf(q) === -1;
        });
      });
    });
  }
  function initKeyboardSearch() {
    document.addEventListener('keydown', function (event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        var input = document.querySelector('[data-v3-global-search]');
        if (input) { event.preventDefault(); input.focus(); }
      }
    });
  }
  document.addEventListener('DOMContentLoaded', function () {
    initLocalFilters();
    initKeyboardSearch();
  });
})();

document.addEventListener('input', function (event) {
  var input = event.target;
  if (!input || !input.matches || !input.matches('[data-v3-command-filter]')) return;
  var root = input.closest('[data-v3-command-palette-root]') || document;
  var query = (input.value || '').toLowerCase();
  root.querySelectorAll('[data-v3-command-list] .v3-list-item').forEach(function (row) {
    row.hidden = row.textContent.toLowerCase().indexOf(query) === -1;
  });
});

document.addEventListener('keydown', function (event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    var field = document.querySelector('[data-v3-command-filter]') || document.querySelector('[data-v3-global-search]');
    if (field) { event.preventDefault(); field.focus(); }
  }
});
