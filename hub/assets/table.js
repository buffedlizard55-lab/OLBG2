(function () {
  function initFilterableTable(wrapper) {
    var table = wrapper.querySelector("table[data-hub-table]");
    if (!table) return;
    var tbody = table.querySelector("tbody");
    var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
    var searchInput = wrapper.querySelector("[data-filter-search]");
    var confSelect = wrapper.querySelector("[data-filter-conf]");
    var sportSelect = wrapper.querySelector("[data-filter-sport]");
    var counter = wrapper.querySelector("[data-filter-count]");

    function applyFilters() {
      var q = searchInput ? searchInput.value.trim().toLowerCase() : "";
      var cf = confSelect ? confSelect.value : "all";
      var sp = sportSelect ? sportSelect.value : "all";
      var shown = 0;
      rows.forEach(function (tr) {
        var matchQ = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        var matchC = cf === "all" || tr.getAttribute("data-conf") === cf;
        var matchS = sp === "all" || tr.getAttribute("data-sport") === sp;
        var vis = matchQ && matchC && matchS;
        tr.style.display = vis ? "" : "none";
        if (vis) shown += 1;
      });
      if (counter) {
        counter.textContent = "Showing " + shown + " of " + rows.length + " verified rows";
      }
    }

    if (searchInput) searchInput.addEventListener("input", applyFilters);
    if (confSelect) confSelect.addEventListener("change", applyFilters);
    if (sportSelect) sportSelect.addEventListener("change", applyFilters);

    var headers = table.querySelectorAll("thead th");
    headers.forEach(function (th, idx) {
      th.addEventListener("click", function () {
        var asc = th.getAttribute("data-sort-dir") !== "asc";
        headers.forEach(function (h) { h.removeAttribute("data-sort-dir"); });
        th.setAttribute("data-sort-dir", asc ? "asc" : "desc");
        rows.sort(function (a, b) {
          var ta = (a.children[idx] ? a.children[idx].textContent : "").trim();
          var tb = (b.children[idx] ? b.children[idx].textContent : "").trim();
          var na = parseFloat(ta.replace(/[^0-9.-]/g, ""));
          var nb = parseFloat(tb.replace(/[^0-9.-]/g, ""));
          if (!isNaN(na) && !isNaN(nb) && /^[+-]?\d/.test(ta) && /^[+-]?\d/.test(tb)) {
            return asc ? na - nb : nb - na;
          }
          return asc ? ta.localeCompare(tb) : tb.localeCompare(ta);
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
      });
    });

    applyFilters();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-table-section]").forEach(initFilterableTable);
    var pills = document.querySelectorAll("[data-pred-pill]");
    var cards = document.querySelectorAll("[data-pred-card]");
    pills.forEach(function (pill) {
      pill.addEventListener("click", function () {
        var sp = pill.getAttribute("data-pred-pill");
        pills.forEach(function (p) { p.classList.remove("active"); });
        pill.classList.add("active");
        cards.forEach(function (c) {
          c.style.display = (sp === "all" || c.getAttribute("data-sport") === sp) ? "" : "none";
        });
      });
    });
  });
})();
