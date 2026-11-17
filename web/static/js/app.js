/* RankPilot web UI behaviors: mobile sidebar, analysis loading state,
   and an optional Chart.js donut of check outcomes. */

(function () {
  "use strict";

  var toggle = document.getElementById("menuToggle");
  var sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  var form = document.getElementById("analyzeForm");
  var overlay = document.getElementById("loadingOverlay");
  if (form && overlay) {
    form.addEventListener("submit", function () {
      var input = form.querySelector("input[name='url']");
      if (input && input.value.trim() === "") {
        return; // let native validation show its message
      }
      overlay.classList.add("visible");
    });
  }

  var canvas = document.getElementById("outcomesChart");
  if (canvas && window.Chart) {
    new window.Chart(canvas, {
      type: "doughnut",
      data: {
        labels: [canvas.dataset.passedLabel, canvas.dataset.failedLabel, canvas.dataset.warnLabel],
        datasets: [{
          data: [
            Number(canvas.dataset.passed || 0),
            Number(canvas.dataset.failed || 0),
            Number(canvas.dataset.warn || 0)
          ],
          backgroundColor: ["#16a34a", "#dc2626", "#d97706"],
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        cutout: "62%"
      }
    });
  }
})();
