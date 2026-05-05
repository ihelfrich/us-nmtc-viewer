/* ============================================================
   NMTC viewer — Cesium map with 8,019 project points
   Depends on:
     window.Cesium
     window.NMTC_PROJECTS   (array of {project_id, year, metro, qalicb_type, state,
                              city, project_qlici, project_cost, leverage_win, lat, lon})
   ============================================================ */

(function () {
  "use strict";

  if (!window.Cesium) {
    console.error("CesiumJS failed to load.");
    return;
  }
  const C = window.Cesium;

  // No Ion token needed — we use tokenless Esri imagery.
  C.Ion.defaultAccessToken = "";

  // ---------- boot viewer with Esri World Imagery ----------
  const esri = C.ImageryLayer.fromProviderAsync(
    C.ArcGisMapServerImageryProvider.fromUrl(
      "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
      { enablePickFeatures: false }
    )
  );

  const viewer = new C.Viewer("cesiumContainer", {
    baseLayer: esri,
    animation: false,
    timeline: false,
    geocoder: false,
    baseLayerPicker: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    homeButton: true,
    fullscreenButton: true,
    infoBox: false,
    selectionIndicator: false,
    skyAtmosphere: false,
    shouldAnimate: false,
  });
  // gentle dark ambient
  viewer.scene.backgroundColor = C.Color.fromCssColorString("#000000");
  viewer.scene.globe.baseColor  = C.Color.fromCssColorString("#0b1220");
  viewer.scene.skyBox.show = true;

  // Fly to continental US
  viewer.camera.flyTo({
    destination: C.Cartesian3.fromDegrees(-96.5, 37.8, 5_500_000),
    duration: 0,
  });
  // set the homeButton target to the same
  viewer.homeButton.viewModel.command.beforeExecute.addEventListener(e => {
    e.cancel = true;
    viewer.camera.flyTo({
      destination: C.Cartesian3.fromDegrees(-96.5, 37.8, 5_500_000),
      duration: 1.2,
    });
  });

  // ---------- projects → primitives ----------
  const projects = window.NMTC_PROJECTS || [];
  // Per-project colors by metro
  const METRO_COLOR    = C.Color.fromCssColorString("#3d8ecc").withAlpha(0.85);
  const NONMETRO_COLOR = C.Color.fromCssColorString("#e05555").withAlpha(0.85);

  // QALICB type palette (matching matplotlib palette)
  const TYPE_COLOR = {
    RE:  C.Color.fromCssColorString("#4c72b0").withAlpha(0.85),
    NRE: C.Color.fromCssColorString("#55a868").withAlpha(0.85),
    SPE: C.Color.fromCssColorString("#c44e52").withAlpha(0.85),
    CDE: C.Color.fromCssColorString("#8172b2").withAlpha(0.85),
  };
  const OUTLINE = C.Color.BLACK.withAlpha(0.5);

  // Leverage color ramp: white (low) → amber (high), winsorized 1..4
  function leverageColor(lev) {
    const t = Math.max(0, Math.min(1, (lev - 1) / 3));  // 1x → 0, 4x → 1
    // interpolate #9fb4d0 → #fbbf24
    const r = Math.round((1 - t) * 159 + t * 251);
    const g = Math.round((1 - t) * 180 + t * 191);
    const b = Math.round((1 - t) * 208 + t *  36);
    return C.Color.fromBytes(r, g, b, 220);
  }

  // Build a PointPrimitiveCollection for perf
  const pointColl = viewer.scene.primitives.add(new C.PointPrimitiveCollection());
  const primRefs  = new Array(projects.length);    // primitive for each project
  const sizeFor   = q => 3.5 + Math.min(12, Math.sqrt((q || 0) / 1e6) * 1.1);

  projects.forEach((p, i) => {
    const prim = pointColl.add({
      position: C.Cartesian3.fromDegrees(p.lon, p.lat),
      color:   p.metro === "non_metro" ? NONMETRO_COLOR : METRO_COLOR,
      pixelSize: sizeFor(p.project_qlici),
      outlineColor: OUTLINE,
      outlineWidth: 0.5,
      // stash record so pick handler can find it
      id: { idx: i, kind: "nmtcProject" },
    });
    primRefs[i] = prim;
  });

  // ---------- filtering + color recoloring ----------
  const ui = {
    yrMin:    document.getElementById("yrMin"),
    yrMax:    document.getElementById("yrMax"),
    yrLabel:  document.getElementById("yrLabel"),
    showMetro:    document.getElementById("showMetro"),
    showNonMetro: document.getElementById("showNonMetro"),
    qTypes:   Array.from(document.querySelectorAll(".qType")),
    colorMode: document.getElementById("colorMode"),
    countShown:  document.getElementById("countShown"),
    dollarShown: document.getElementById("dollarShown"),
  };

  function currentColorFor(p) {
    const mode = ui.colorMode.value;
    if (mode === "leverage") return leverageColor(p.leverage_win || 1);
    if (mode === "qalicb")   return TYPE_COLOR[p.qalicb_type] || METRO_COLOR;
    return p.metro === "non_metro" ? NONMETRO_COLOR : METRO_COLOR;
  }

  function applyFilters() {
    let ymin = +ui.yrMin.value, ymax = +ui.yrMax.value;
    if (ymin > ymax) { const t = ymin; ymin = ymax; ymax = t; }
    ui.yrLabel.textContent = `${ymin} – ${ymax}`;

    const wantMetro = ui.showMetro.checked;
    const wantNM    = ui.showNonMetro.checked;
    const wantTypes = new Set(ui.qTypes.filter(x => x.checked).map(x => x.value));

    let n = 0, dollar = 0;
    for (let i = 0; i < projects.length; i++) {
      const p = projects[i];
      const prim = primRefs[i];
      const show =
        p.year >= ymin && p.year <= ymax &&
        ((p.metro === "non_metro" && wantNM) || (p.metro !== "non_metro" && wantMetro)) &&
        wantTypes.has(p.qalicb_type);
      prim.show = show;
      if (show) {
        prim.color = currentColorFor(p);
        n += 1;
        dollar += (p.project_qlici || 0);
      }
    }
    ui.countShown.textContent  = n.toLocaleString();
    ui.dollarShown.textContent = `$${(dollar / 1e9).toFixed(2)} B QLICI`;
  }

  // two-sided year slider: keep ymin ≤ ymax
  function enforceOrdering(which) {
    return () => {
      let lo = +ui.yrMin.value, hi = +ui.yrMax.value;
      if (lo > hi) {
        if (which === "lo") ui.yrMax.value = lo; else ui.yrMin.value = hi;
      }
      applyFilters();
    };
  }
  ui.yrMin.addEventListener("input", enforceOrdering("lo"));
  ui.yrMax.addEventListener("input", enforceOrdering("hi"));
  ui.showMetro.addEventListener("change", applyFilters);
  ui.showNonMetro.addEventListener("change", applyFilters);
  ui.qTypes.forEach(cb => cb.addEventListener("change", applyFilters));
  ui.colorMode.addEventListener("change", applyFilters);

  applyFilters();

  // ---------- hover / click info panel ----------
  const info = document.getElementById("mapInfo");
  const fmtMoney = v => {
    if (v == null) return "—";
    if (v >= 1e6) return `$${(v / 1e6).toFixed(2)} M`;
    if (v >= 1e3) return `$${(v / 1e3).toFixed(0)} k`;
    return `$${v.toLocaleString()}`;
  };
  const QALICB_LABEL = {
    RE:  "Real Estate",
    NRE: "Non-Real-Estate (operating business)",
    SPE: "Special-Purpose Entity",
    CDE: "Loan to another CDE",
  };

  function renderInfo(p, pinned) {
    info.innerHTML = `
      <h4>Project ${p.project_id} ${pinned ? "· pinned" : ""}</h4>
      <div class="info-kv">
        <div class="k">Year</div><div class="v">${p.year}</div>
        <div class="k">Location</div><div class="v">${p.city || "—"}, ${p.state || "—"}</div>
        <div class="k">Metro?</div><div class="v">${p.metro === "non_metro" ? "Non-metro" : p.metro === "metro" ? "Metro" : "—"}</div>
        <div class="k">QALICB type</div><div class="v">${QALICB_LABEL[p.qalicb_type] || p.qalicb_type || "—"}</div>
        <div class="k">QLICI amount</div><div class="v">${fmtMoney(p.project_qlici)}</div>
        <div class="k">Total project cost</div><div class="v">${fmtMoney(p.project_cost)}</div>
        <div class="k">Leverage (winsorized)</div><div class="v">${p.leverage_win != null ? p.leverage_win.toFixed(2) + "×" : "—"}</div>
        <div class="k">Mobilization</div><div class="v">${p.leverage_win != null ? (p.leverage_win - 1).toFixed(2) + "×" : "—"}</div>
      </div>`;
  }

  const handler = new C.ScreenSpaceEventHandler(viewer.scene.canvas);
  let pinnedIdx = null;

  handler.setInputAction(movement => {
    const picked = viewer.scene.pick(movement.endPosition);
    if (picked && picked.id && picked.id.kind === "nmtcProject" && pinnedIdx == null) {
      renderInfo(projects[picked.id.idx], false);
    } else if (pinnedIdx == null) {
      info.innerHTML = `<h4>Hover a dot</h4><p class="dim">Or click to pin the info here.</p>`;
    }
  }, C.ScreenSpaceEventType.MOUSE_MOVE);

  handler.setInputAction(click => {
    const picked = viewer.scene.pick(click.position);
    if (picked && picked.id && picked.id.kind === "nmtcProject") {
      pinnedIdx = picked.id.idx;
      renderInfo(projects[pinnedIdx], true);
    } else {
      pinnedIdx = null;
      info.innerHTML = `<h4>Hover a dot</h4><p class="dim">Or click to pin the info here.</p>`;
    }
  }, C.ScreenSpaceEventType.LEFT_CLICK);
})();
