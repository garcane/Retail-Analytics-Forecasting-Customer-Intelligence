// Classic (non-module) script. Browsers block ES modules and fetch() for pages opened from the file system, so a
// double-clicked index.html would stay blank. Explain how to serve it instead; also report a failed start.
(function () {
  "use strict";

  function show(title, lines) {
    var main = document.getElementById("main");
    if (!main) return;
    while (main.firstChild) main.removeChild(main.firstChild);
    var box = document.createElement("div");
    box.className = "boot-error";
    var h = document.createElement("h1");
    h.textContent = title;
    box.appendChild(h);
    lines.forEach(function (line) {
      var p = document.createElement("p");
      if (line.code) {
        var c = document.createElement("code");
        c.textContent = line.code;
        p.appendChild(c);
      } else {
        p.textContent = line;
      }
      box.appendChild(p);
    });
    main.appendChild(box);
  }

  if (location.protocol === "file:") {
    show("Serve the dashboard over HTTP", [
      "This page loads its data and modules with fetch(), which browsers block for files opened from disk.",
      "From the repository root, run:",
      { code: "uv run python src/dashboard/serve.py" },
      "then open http://127.0.0.1:8000 (it turns caching off, so edits and rebuilt data always show). To refresh the data first (Snowflake by default, or offline from DuckDB):",
      { code: "uv run python src/dashboard/build_data.py --yes" },
      { code: "uv run python src/dashboard/build_data.py --backend duckdb" },
    ]);
    return;
  }

  window.setTimeout(function () {
    if (!window.__dashboardReady) {
      show("The dashboard did not start", [
        "The application module failed to load. Check the browser console, and that dashboard/data/manifest.json exists",
        "(build it with: uv run python src/dashboard/build_data.py --yes, or --backend duckdb offline).",
      ]);
    }
  }, 8000);
})();
