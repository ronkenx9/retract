/* RETRACT G3 editorial desk — vanilla client */
(() => {
  const LOCKED = {
    control: "8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7",
    pressFriday: "746e9d25a3756bd775702b5e2976cb2a1ab70c4a432a4e9f4b6824a8761e9096",
    pressMonday: "37437dcd61110f51274bfe64b727d9c448b8e2b2329efacd4b7f9b473aab0e03",
    pressDispute: "8fa56152e8f681171fb82e8cd186bbd23e9b98850a703af4687df4023624cb67",
  };

  const state = {
    view: "desk", // desk | correct | after
    payload: null,
    selectedArtifact: null,
    event: null,
    decision: null,
  };

  const $ = (id) => document.getElementById(id);

  function shortHash(h, n = 8) {
    if (!h) return "—";
    return h.length > n ? h.slice(0, n) + "…" : h;
  }

  function statusLabel(status) {
    if (!status) return "Active";
    if (status === "active") return "Active";
    if (status === "superseded") return "Superseded";
    if (status === "not_established") return "Not established";
    if (status === "disputed") return "Not established";
    return status;
  }

  function chipClass(status) {
    if (status === "active") return "active";
    if (status === "not_established" || status === "disputed") return "not_established";
    return "superseded";
  }

  function artifactBodyLines(text) {
    if (!text) return "";
    return text
      .split("\n")
      .filter((l) => l && !l.startsWith("PRESS BRIEF") && !l.startsWith("COMPANY BLURB"))
      .join("\n")
      .trim();
  }

  /** Normalize API payload → {graph, checks, phase, hash_check, event, decision} */
  function normalize(data) {
    const phase = data.phase || "before";
    const checks = data.checks || {};
    const passed = !!(checks.control_ok && checks.press_ok);
    const hash_check = {
      phase:
        phase === "after"
          ? "after_approved"
          : phase === "dispute"
            ? "after_dispute"
            : "before",
      control_ok: !!checks.control_ok,
      press_ok: !!checks.press_ok,
      passed: phase === "before" ? true : passed,
      control_sha256: checks.actual && checks.actual.control,
      press_sha256: checks.actual && checks.actual.press,
      fail_reason: passed
        ? null
        : !checks.control_ok
          ? "control hash moved"
          : "press hash mismatch",
    };
    return {
      ...data,
      phase,
      checks,
      hash_check,
      event: data.event || null,
      decision: data.decision || (phase === "dispute" ? "disputed" : phase === "after" ? "approved" : null),
    };
  }

  async function api(path, opts) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(opts && opts.headers) },
      ...opts,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data.detail || data.message || res.statusText;
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return normalize(data);
  }

  function liveSource(graph) {
    return (graph.sources || []).find((s) => !s.archived) || null;
  }

  function archivedSources(graph) {
    return (graph.sources || []).filter((s) => s.archived);
  }

  function byName(graph, name) {
    return (graph.artifacts || []).find((a) => a.name === name);
  }

  function setBusy(msg) {
    const el = $("busy");
    if (!msg) {
      el.classList.remove("on");
      el.textContent = "";
      return;
    }
    el.textContent = msg;
    el.classList.add("on");
  }

  function showView(view) {
    state.view = view;
    const desk = $("screen-desk");
    const correct = $("screen-correct");
    const actions = $("chrome-actions");

    if (view === "correct") {
      desk.classList.add("hidden");
      correct.classList.remove("hidden");
      actions.classList.add("hidden");
      $("event-strip").classList.add("hidden");
      $("proof-banner").classList.add("hidden");
      renderCorrectPreview();
    } else {
      desk.classList.remove("hidden");
      correct.classList.add("hidden");
      actions.classList.remove("hidden");
      const btn = $("btn-correct-source");
      const live = state.payload && liveSource(state.payload.graph);
      const canCorrect = live && live.day === "Friday" && live.status === "active";
      btn.disabled = !canCorrect;
      btn.textContent = "Correct source";
      renderDesk();
    }
  }

  function renderProofBanner(hashCheck, decision) {
    const banner = $("proof-banner");
    if (!hashCheck || state.view === "correct") {
      banner.classList.add("hidden");
      return;
    }
    const phase = hashCheck.phase || "";
    if (phase === "before") {
      banner.classList.add("hidden");
      return;
    }
    banner.classList.remove("hidden");
    if (hashCheck.passed) {
      banner.className = "banner pass";
      banner.textContent =
        decision === "disputed"
          ? "PASS · press rebuilt to not_established · control unchanged"
          : "PASS · press rebuilt Monday · control unchanged";
    } else {
      banner.className = "banner fail";
      banner.textContent =
        "Proof failed · selective invalidation broken." +
        (hashCheck.fail_reason ? " · " + hashCheck.fail_reason : "");
    }
  }

  function renderEvent() {
    const el = $("event-strip");
    if (state.event && state.view !== "correct") {
      el.textContent = state.event;
      el.classList.remove("hidden");
    } else {
      el.classList.add("hidden");
    }
  }

  function renderSources(graph) {
    const root = $("sources");
    const live = liveSource(graph);
    const archived = archivedSources(graph);
    if (!live) {
      root.innerHTML = '<article class="card"><p class="claim">No live source.</p></article>';
      return;
    }

    const svidShort = shortHash(live.source_version_id);
    const status = live.status || "active";
    let eye = `${live.name || "novadesk-launch"} · v${live.version} · ${statusLabel(status).toLowerCase()}`;
    if (live.supersedes) {
      eye += ` · supersedes ${shortHash(live.supersedes)}`;
    } else {
      eye += ` · ${svidShort}`;
    }

    const hot =
      state.selectedArtifact === "press-brief" || !state.selectedArtifact
        ? " hot"
        : state.selectedArtifact === "company-blurb"
          ? ""
          : " hot";

    let html = `<article class="card${hot}" data-svid="${live.source_version_id || ""}">
      <div class="eye">${escapeHtml(eye)}</div>
      <span class="chip ${chipClass(status)}">${statusLabel(status)}</span>
      <p class="claim">${escapeHtml(live.claim || "")}</p>`;

    if (archived.length) {
      html += archived
        .map((a) => {
          const reason = a.archive_reason || "archived";
          return `<div class="archive">v${a.version} · ${escapeHtml(a.day || "—")} · archived · ${escapeHtml(reason)}</div>`;
        })
        .join("");
    }
    html += "</article>";
    root.innerHTML = html;
  }

  function renderArtifacts(graph, hashCheck) {
    const root = $("artifacts");
    const press = byName(graph, "press-brief");
    const control = byName(graph, "company-blurb");
    const after = hashCheck && hashCheck.phase && hashCheck.phase.startsWith("after");

    const parts = [];

    if (press) {
      let status = "depends on launch";
      let statusCls = "";
      if (after) {
        status =
          hashCheck.phase === "after_dispute"
            ? "rebuilt (not “no regen”)"
            : "rebuilt";
        statusCls = "rebuild";
      }
      const selected = state.selectedArtifact === "press-brief" ? " hot" : "";
      parts.push(`<article class="card selectable${selected}" data-art="press-brief">
        <div class="status ${statusCls}">press-brief · ${status}</div>
        <pre>${escapeHtml(artifactBodyLines(press.text))}</pre>
        <span class="hash" title="${escapeHtml(press.content_sha256 || "")}">${shortHash(press.content_sha256)}</span>
      </article>`);
    }

    if (control) {
      let status = "Control · no launch-day claim";
      let statusCls = "";
      if (after) {
        status = "unchanged";
        statusCls = "ok";
      }
      const selected = state.selectedArtifact === "company-blurb" ? " hot" : "";
      parts.push(`<article class="card selectable${selected}" data-art="company-blurb">
        <div class="status ${statusCls}">company-blurb · ${status}</div>
        <pre>${escapeHtml(artifactBodyLines(control.text))}</pre>
        <span class="hash" title="${escapeHtml(control.content_sha256 || "")}">${shortHash(control.content_sha256)}</span>
      </article>`);
    }

    root.innerHTML = parts.join("");
    root.querySelectorAll("[data-art]").forEach((el) => {
      el.addEventListener("click", () => {
        state.selectedArtifact = el.getAttribute("data-art");
        renderDesk();
      });
    });
  }

  function renderDesk() {
    if (!state.payload) return;
    const { graph, hash_check } = state.payload;
    renderEvent();
    renderProofBanner(hash_check, state.decision);
    renderSources(graph);
    renderArtifacts(graph, hash_check);
  }

  function renderCorrectPreview() {
    const graph = state.payload && state.payload.graph;
    const live = graph && liveSource(graph);
    const oldCard = $("old-source-card");
    if (live) {
      oldCard.innerHTML = `
        <div class="eye">Current · v${live.version} · ${shortHash(live.source_version_id)}</div>
        <p class="claim">${escapeHtml(live.claim || "")}</p>`;
    }
    updateClaimPreview();
    const day = $("field-day").value.trim() || "Monday";
    const press = graph && byName(graph, "press-brief");
    const friHash = (press && press.content_sha256) || LOCKED.pressFriday;
    $("will-change").innerHTML = `
      <div class="status">press-brief · hash moves off ${shortHash(friHash)}</div>
      <pre class="diff">Embargo lifts: <del>Friday</del> <ins>${escapeHtml(day)}</ins>
Headline: NovaDesk launches to the public on <del>Friday</del> <ins>${escapeHtml(day)}</ins>.
Call to action: Mark your calendar for <del>Friday</del> <ins>${escapeHtml(day)}</ins>.</pre>
      <p style="color:var(--mute);font-size:13px;margin:10px 0 0">Dispute: press-brief rebuilds to not-established text (hash 8fa56152…). Not “no regen.”</p>`;
    syncCtas();
  }

  function updateClaimPreview() {
    const day = $("field-day").value.trim() || "Monday";
    $("claim-preview").textContent = `NovaDesk public launch is on ${day}.`;
  }

  function syncCtas() {
    const reason = $("field-reason").value.trim();
    const ok = reason.length >= 8;
    $("btn-apply").disabled = !ok;
    $("btn-dispute").disabled = !ok;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function loadState() {
    const data = await api("/api/state");
    state.payload = data;
    state.event = data.event;
    state.decision = data.decision;
    showView("desk");
  }

  async function reseed() {
    const data = await api("/api/reset", { method: "POST", body: "{}" });
    state.payload = data;
    state.event = null;
    state.decision = null;
    showView("desk");
  }

  async function applyCorrection() {
    const day = $("field-day").value.trim() || "Monday";
    const reason = $("field-reason").value.trim();
    setBusy("Cold start · reading Sibyl…");
    $("btn-apply").disabled = true;
    $("btn-dispute").disabled = true;
    try {
      await new Promise((r) => setTimeout(r, 280));
      setBusy("Withdrawing dependents…");
      const data = await api("/api/correct", {
        method: "POST",
        body: JSON.stringify({ day, reason }),
      });
      state.payload = data;
      state.event = data.event;
      state.decision = data.decision;
      setBusy("");
      showView("after");
    } catch (e) {
      setBusy("");
      syncCtas();
      alert(e.message || String(e));
    }
  }

  async function applyDispute() {
    const reason = $("field-reason").value.trim();
    setBusy("Cold start · reading Sibyl…");
    $("btn-apply").disabled = true;
    $("btn-dispute").disabled = true;
    try {
      await new Promise((r) => setTimeout(r, 280));
      setBusy("Withdrawing dependents…");
      const data = await api("/api/dispute", {
        method: "POST",
        body: JSON.stringify({ reason }),
      });
      state.payload = data;
      state.event = data.event;
      state.decision = data.decision;
      setBusy("");
      showView("after");
    } catch (e) {
      setBusy("");
      syncCtas();
      alert(e.message || String(e));
    }
  }

  function bind() {
    $("btn-correct-source").addEventListener("click", () => showView("correct"));
    $("btn-back").addEventListener("click", () => showView("desk"));
    $("btn-reseed").addEventListener("click", () => reseed().catch((e) => alert(e.message)));
    $("field-day").addEventListener("input", () => {
      updateClaimPreview();
      renderCorrectPreview();
    });
    $("field-reason").addEventListener("input", syncCtas);
    $("btn-apply").addEventListener("click", applyCorrection);
    $("btn-dispute").addEventListener("click", applyDispute);
  }

  bind();
  const params = new URLSearchParams(location.search);
  const wantScreen = params.get("screen"); // desk | correct | after | dispute
  loadState()
    .then(async () => {
      if (!wantScreen || wantScreen === "desk") return;
      if (wantScreen === "correct") {
        showView("correct");
        return;
      }
      if (wantScreen === "after") {
        await api("/api/seed", { method: "POST", body: "{}" });
        const data = await api("/api/correct", {
          method: "POST",
          body: JSON.stringify({ day: "Monday", reason: "Calendar confirmed Monday." }),
        });
        state.payload = data;
        state.event = data.event;
        state.decision = data.decision;
        showView("after");
        return;
      }
      if (wantScreen === "dispute") {
        await api("/api/seed", { method: "POST", body: "{}" });
        const data = await api("/api/dispute", {
          method: "POST",
          body: JSON.stringify({ reason: "Launch day disputed; treat as not established." }),
        });
        state.payload = data;
        state.event = data.event;
        state.decision = data.decision;
        showView("after");
      }
    })
    .catch((e) => {
    document.body.insertAdjacentHTML(
      "beforeend",
      `<pre style="color:#e8b4b4;padding:20px">${escapeHtml(e.message)}</pre>`
    );
  });
})();
