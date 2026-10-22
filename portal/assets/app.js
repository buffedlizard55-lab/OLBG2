(function () {
  function initFilterableTable(root) {
    var search = root.querySelector("[data-filter-search]");
    var sportSel = root.querySelector("[data-filter-sport]");
    var confSel = root.querySelector("[data-filter-conf]");
    var typeSel = root.querySelector("[data-filter-type]");
    var countEl = root.querySelector("[data-filter-count]");
    var emptyEl = root.querySelector("[data-filter-empty]");
    var rows = Array.prototype.slice.call(root.querySelectorAll("tbody tr[data-row]"));
    if (!rows.length) {
      if (countEl) countEl.textContent = "No rows available";
      if (emptyEl) emptyEl.hidden = false;
      return;
    }

    function apply() {
      var q = search ? search.value.trim().toLowerCase() : "";
      var sp = sportSel ? sportSel.value : "all";
      var cf = confSel ? confSel.value : "all";
      var tp = typeSel ? typeSel.value : "all";
      var shown = 0;
      rows.forEach(function (tr) {
        var ok = true;
        if (sp !== "all" && tr.getAttribute("data-sport") !== sp) ok = false;
        if (cf !== "all" && tr.getAttribute("data-conf") !== cf) ok = false;
        if (tp !== "all" && tr.getAttribute("data-type") !== tp) ok = false;
        if (ok && q && tr.textContent.toLowerCase().indexOf(q) === -1) ok = false;
        tr.hidden = !ok;
        if (ok) shown += 1;
      });
      if (countEl) {
        countEl.textContent = "Showing " + shown + " of " + rows.length + " rows";
      }
      if (emptyEl) emptyEl.hidden = shown > 0;
    }

    [search, sportSel, confSel, typeSel].forEach(function (el) {
      if (!el) return;
      el.addEventListener("input", apply);
      el.addEventListener("change", apply);
    });
    apply();
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.slice.call(document.querySelectorAll("[data-filter-root]")).forEach(initFilterableTable);
  });
})();
