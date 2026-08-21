(function () {
  "use strict";

  const TYPE_COLORS = {
    person: "#d96643", organization: "#476f86", location: "#5b8969",
    concept: "#8b688c", event: "#d9a944", time: "#748f86",
    work: "#397675", other: "#7d817e",
  };
  const state = {
    capabilities: null, results: [], selectedDocuments: new Map(), graph: null,
    graphId: "example-fixed-v2", entitiesById: new Map(), selectedItem: null,
    polling: null,
  };
  const $ = (selector) => document.querySelector(selector);

  function escapeHtml(value) {
    return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }
  function humanize(value) {
    return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
  }
  function truncate(value, length) {
    const text = String(value || "");
    return text.length > length ? `${text.slice(0, length - 1)}…` : text;
  }
  function token() { return $("[data-token]").value.trim(); }

  async function api(path, options = {}) {
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    if (options.operator && token()) headers.Authorization = `Bearer ${token()}`;
    const response = await fetch(`./api/${path}`, { ...options, headers });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) {
      const detail = typeof payload === "object" ? payload.detail : payload;
      throw new Error(detail || `Request failed with status ${response.status}`);
    }
    return payload;
  }

  function toast(message) {
    const element = $("[data-toast]");
    element.textContent = message;
    element.hidden = false;
    window.clearTimeout(toast.timer);
    toast.timer = window.setTimeout(() => { element.hidden = true; }, 4200);
  }

  async function loadCapabilities() {
    try {
      state.capabilities = await api("capabilities", { operator: true });
      $("[data-connectors]").innerHTML = state.capabilities.connectors.map((connector) => `
        <div class="connector ${connector.state}"><i class="connector-dot"></i><div>
          <strong>${escapeHtml(connector.label)}${connector.document_count ? ` · ${connector.document_count}` : ""}</strong>
          <span>${escapeHtml(connector.detail)}</span>
          ${connector.id === "cia-reading-room-live" && state.capabilities.graph_build_authorized ? '<button class="text-button connector-action" type="button" data-probe-cia>Recheck official endpoint</button>' : ""}
        </div></div>`).join("");
      $("[data-probe-cia]")?.addEventListener("click", probeCiaConnector);
      $("[data-budget]").max = String(state.capabilities.max_build_budget_usd);
      const uploadButton = $("[data-upload-open]");
      uploadButton.disabled = !state.capabilities.document_upload_enabled || !state.capabilities.document_upload_authorized;
      uploadButton.title = uploadButton.disabled ? "Open through the tailnet or enter the operator token." : "Add a private source document";
      const searchConnector = $("[data-search-connector]");
      searchConnector.querySelector('option[value="user-uploads"]').disabled = !state.capabilities.document_upload_authorized;
      const live = state.capabilities.connectors.find((item) => item.id === "cia-reading-room-live");
      searchConnector.querySelector('option[value="cia-reading-room-live"]').disabled = !state.capabilities.graph_build_authorized || live?.state !== "available";
      updateBuildControls();
    } catch (error) {
      $("[data-connectors]").innerHTML = `<div class="inline-error">Capability request failed: ${escapeHtml(error.message)}</div>`;
    }
  }

  async function runSearch(query, connectorId = $("[data-search-connector]").value) {
    const results = $("[data-results]");
    const errorBox = $("[data-search-error]");
    errorBox.hidden = true;
    results.innerHTML = '<div class="empty-state compact">Searching source text…</div>';
    try {
      const response = await api("search", {
        method: "POST", operator: true,
        body: JSON.stringify({ query, connector_id: connectorId, limit: 30 }),
      });
      state.results = response.results;
      $("[data-result-count]").textContent = `${response.total_matches} matches`;
      const sourceLabel = $("[data-search-connector]").selectedOptions[0]?.textContent || response.connector_id;
      $("[data-search-meta]").textContent = `${sourceLabel} · query “${response.query}”.`;
      renderResults();
    } catch (error) {
      results.replaceChildren();
      errorBox.textContent = `Search failed: ${error.message}`;
      errorBox.hidden = false;
    }
  }

  function renderResults() {
    const container = $("[data-results]");
    if (!state.results.length) {
      container.innerHTML = '<div class="empty-state compact">No tracked documents matched this query.</div>';
      return;
    }
    container.innerHTML = state.results.map((result) => {
      const selected = state.selectedDocuments.has(result.document_id);
      const metadata = [result.document_type, result.publication_date, result.page_count ? `${result.page_count} pp.` : null].filter(Boolean).join(" · ");
      return `<article class="result-card ${selected ? "is-selected" : ""}" data-result-id="${escapeHtml(result.document_id)}">
        <input type="checkbox" aria-label="Select ${escapeHtml(result.title)}" ${selected ? "checked" : ""} />
        <div><h3>${escapeHtml(result.title)}</h3>
          <div class="result-meta"><span class="source-badge ${result.connector_id === "user-uploads" ? "private" : ""}">${result.connector_id === "user-uploads" ? "Private upload" : result.connector_id === "cia-reading-room-live" ? "CIA live" : "Bundled CREST"}</span> ${escapeHtml(result.document_id)}${metadata ? ` · ${escapeHtml(metadata)}` : ""}</div>
          <p>${escapeHtml(truncate(result.snippet, 280))}</p>
          <div class="result-actions"><button class="text-button" type="button" data-inspect-document>Inspect source</button></div>
        </div></article>`;
    }).join("");
    container.querySelectorAll("[data-result-id]").forEach((card) => {
      const id = card.dataset.resultId;
      card.querySelector("input").addEventListener("change", (event) => toggleDocument(id, event.target.checked));
      card.querySelector("[data-inspect-document]").addEventListener("click", () => inspectDocument(id));
    });
  }

  function toggleDocument(documentId, shouldSelect) {
    const result = state.results.find((item) => item.document_id === documentId);
    if (shouldSelect && state.selectedDocuments.size >= 3) {
      toast("A graph build is limited to three documents in this development vertical.");
      renderResults();
      return;
    }
    if (shouldSelect) state.selectedDocuments.set(documentId, result);
    else state.selectedDocuments.delete(documentId);
    renderResults();
    updateBuildControls();
  }

  async function inspectDocument(documentId) {
    const dialog = $("[data-document-dialog]");
    const content = $("[data-document-content]");
    content.innerHTML = '<div class="empty-state compact">Loading the tracked source…</div>';
    dialog.showModal();
    try {
      const detail = await api(`documents/${encodeURIComponent(documentId)}`, { operator: true });
      const metadata = Object.entries(detail.metadata).filter(([, value]) => value)
        .map(([key, value]) => `<span>${escapeHtml(key)}: ${escapeHtml(value)}</span>`).join("");
      content.innerHTML = `<div class="eyebrow">${detail.connector_id === "user-uploads" ? "Private uploaded source" : "Tracked source document"}</div>
        <h2>${escapeHtml(detail.title)}</h2>
        <p class="evidence-meta">${escapeHtml(detail.document_id)} · ${detail.body_chars.toLocaleString()} source characters · SHA-256 ${escapeHtml(detail.body_sha256.slice(0, 12))}…</p>
        <div class="document-meta">${metadata}</div>
        ${detail.source_url ? `<p><a href="${escapeHtml(detail.source_url)}" rel="noreferrer">Open CIA source record ↗</a></p>` : ""}
        ${detail.connector_id === "user-uploads" ? `<div class="document-actions"><a class="button ghost small" href="./api/uploads/${encodeURIComponent(detail.document_id)}/original">Download original</a><button class="text-button danger" type="button" data-delete-upload="${escapeHtml(detail.document_id)}">Delete private source</button></div>` : ""}
        <div class="source-preview">${escapeHtml(detail.body_preview)}</div>`;
      content.querySelector("[data-delete-upload]")?.addEventListener("click", () => deleteUpload(detail.document_id, detail.title));
    } catch (error) {
      content.innerHTML = `<div class="inline-error">Document request failed: ${escapeHtml(error.message)}</div>`;
    }
  }

  async function probeCiaConnector() {
    const button = $("[data-probe-cia]");
    if (button) { button.disabled = true; button.textContent = "Checking…"; }
    try {
      const probe = await api("connectors/cia-reading-room-live/probe", { method: "POST", operator: true });
      toast(`CIA connector ${probe.connector.state}: ${probe.connector.detail}`);
      await loadCapabilities();
    } catch (error) {
      toast(`CIA connector probe failed: ${error.message}`);
      await loadCapabilities();
    }
  }

  async function uploadDocument(event) {
    event.preventDefault();
    const fileInput = $("[data-upload-file]");
    const submit = $("[data-upload-submit]");
    const status = $("[data-upload-status]");
    const file = fileInput.files[0];
    if (!file) { status.textContent = "Choose a source file first."; return; }
    const form = new FormData();
    form.append("file", file);
    const title = $("[data-upload-title]").value.trim();
    if (title) form.append("title", title);
    submit.disabled = true;
    status.textContent = file.type.startsWith("image/") ? "Running local OCR…" : "Extracting and indexing source text…";
    try {
      const receipt = await api("uploads", { method: "POST", body: form, operator: true });
      status.textContent = `${receipt.duplicate ? "Already present" : "Added"} · ${receipt.body_chars.toLocaleString()} characters · ${humanize(receipt.extraction_method)}.`;
      toast(`${receipt.title} is now searchable and ready for graph building.`);
      $("[data-search-connector]").value = "all";
      $("#query").value = receipt.title;
      await loadCapabilities();
      await runSearch(receipt.title, "all");
      const uploaded = state.results.find((item) => item.document_id === receipt.document_id);
      if (uploaded) {
        state.selectedDocuments.set(uploaded.document_id, uploaded);
        renderResults();
        updateBuildControls();
      }
    } catch (error) {
      status.textContent = `Upload failed: ${error.message}`;
    } finally {
      submit.disabled = false;
    }
  }

  async function deleteUpload(documentId, title) {
    if (!window.confirm(`Delete the private source “${title}”? Existing graph artifacts are retained.`)) return;
    try {
      await api(`uploads/${encodeURIComponent(documentId)}`, { method: "DELETE", operator: true });
      state.selectedDocuments.delete(documentId);
      $("[data-document-dialog]").close();
      toast("Private source deleted. Existing restricted graphs were retained.");
      await loadCapabilities();
      await runSearch($("#query").value);
      updateBuildControls();
    } catch (error) {
      toast(`Delete failed: ${error.message}`);
    }
  }

  function updateBuildControls() {
    const count = state.selectedDocuments.size;
    $("[data-selected-count]").textContent = count;
    const labels = [...state.selectedDocuments.values()].map((item) => item.title);
    $("[data-selected-labels]").textContent = labels.length ? labels.join(" · ") : "Choose up to three search results.";
    const button = $("[data-build-button]");
    const status = $("[data-build-status]");
    const capabilities = state.capabilities;
    button.disabled = !count || !capabilities || !capabilities.graph_build_enabled || !capabilities.graph_build_authorized;
    if (!count) status.textContent = "Search and select a document to begin.";
    else if (!capabilities?.graph_build_enabled) status.textContent = "Graph building is disabled on this server.";
    else if (!capabilities.graph_build_authorized) status.textContent = "Open through the tailnet or enter the operator token.";
    else status.textContent = "Authorized · one traced build will use the stated ceiling.";
  }

  async function startBuild() {
    const button = $("[data-build-button]");
    const status = $("[data-build-status]");
    button.disabled = true;
    status.textContent = "Submitting build…";
    try {
      const job = await api("graphs", {
        method: "POST", operator: true,
        body: JSON.stringify({
          document_ids: [...state.selectedDocuments.keys()],
          max_chars_per_document: Number($("[data-max-chars]").value),
          max_budget_usd: Number($("[data-budget]").value),
          refine_relationships: false,
        }),
      });
      pollJob(job.id);
    } catch (error) {
      status.textContent = `Build rejected: ${error.message}`;
      updateBuildControls();
    }
  }

  async function pollJob(jobId) {
    window.clearTimeout(state.polling);
    try {
      const job = await api(`jobs/${jobId}`, { operator: true });
      $("[data-build-status]").textContent = `${humanize(job.state)} · ${job.progress_detail}`;
      if (job.state === "completed") {
        toast("Knowledge graph completed and opened.");
        await loadGraphList(job.graph_id);
        await loadGraph(job.graph_id);
        updateBuildControls();
      } else if (job.state === "failed") {
        $("[data-build-status]").textContent = `Build failed: ${job.error}`;
        updateBuildControls();
      } else {
        state.polling = window.setTimeout(() => pollJob(jobId), 1600);
      }
    } catch (error) {
      $("[data-build-status]").textContent = `Job status failed: ${error.message}`;
      updateBuildControls();
    }
  }

  async function loadGraphList(preferredId) {
    try {
      const response = await api("graphs", { operator: true });
      const picker = $("[data-graph-picker]");
      picker.innerHTML = response.graphs.map((graph) => `<option value="${escapeHtml(graph.id)}">${escapeHtml(graph.label)} · ${graph.entities}E/${graph.relationships}R</option>`).join("");
      picker.value = preferredId || state.graphId;
    } catch (error) { toast(`Saved graphs request failed: ${error.message}`); }
  }

  function requireGraph(payload) {
    if (!payload || payload.schema_version !== "crest-kg-v2") throw new Error("Expected a crest-kg-v2 graph artifact.");
    for (const field of ["documents", "entities", "relationships", "rejections"]) {
      if (!Array.isArray(payload[field])) throw new Error(`Graph field ${field} is missing or invalid.`);
    }
    const ids = new Set(payload.entities.map((entity) => entity.id));
    for (const relationship of payload.relationships) {
      if (!ids.has(relationship.source) || !ids.has(relationship.target)) throw new Error(`Relationship ${relationship.id} has a missing endpoint.`);
      if (!Array.isArray(relationship.groundings) || !relationship.groundings.length) throw new Error(`Relationship ${relationship.id} has no exact grounding.`);
    }
    return payload;
  }

  async function loadGraph(graphId) {
    $("[data-graph-empty]").hidden = false;
    $("[data-graph-empty]").textContent = "Loading graph artifact…";
    try {
      state.graph = requireGraph(await api(`graphs/${encodeURIComponent(graphId)}`, { operator: true }));
      state.graphId = graphId;
      state.entitiesById = new Map(state.graph.entities.map((entity) => [entity.id, entity]));
      state.selectedItem = null;
      $("[data-graph-picker]").value = graphId;
      $("[data-export-link]").href = `./api/graphs/${encodeURIComponent(graphId)}/export.json`;
      renderGraphHeader();
      renderGraph();
      renderInspector();
    } catch (error) {
      $("[data-graph-empty]").textContent = `Graph request failed: ${error.message}`;
    }
  }

  function renderGraphHeader() {
    const graph = state.graph;
    const example = state.graphId === "example-fixed-v2";
    $("[data-graph-title]").textContent = example ? "Five-document evidence checkpoint" : `${graph.documents.length}-document generated graph`;
    for (const field of ["documents", "entities", "relationships", "rejections"]) {
      $(`[data-metric="${field}"]`).textContent = graph[field].length.toLocaleString();
    }
    $("[data-graph-provenance]").textContent = example
      ? "Labeled example · fixed artifact · corpus recall remains unknown."
      : `Generated ${new Date(graph.generated_at).toLocaleString()} · trace ${graph.trace_id}`;
    $("[data-graph-cost]").textContent = `Observed model cost $${Number(graph.observed_cost_usd).toFixed(4)}`;
  }

  function svg(name, attributes = {}) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }
  function graphSelection() {
    const graph = state.graph;
    if (!$("[data-connected-only]").checked || !graph.relationships.length) return { entities: graph.entities, relationships: graph.relationships };
    const connectedIds = new Set(graph.relationships.flatMap((item) => [item.source, item.target]));
    return { entities: graph.entities.filter((entity) => connectedIds.has(entity.id)), relationships: graph.relationships };
  }
  function positionsFor(entities) {
    const positions = new Map();
    const count = Math.max(entities.length, 1);
    const rings = count > 24 ? 3 : count > 10 ? 2 : 1;
    entities.forEach((entity, index) => {
      const ring = index % rings;
      const ringItems = Math.ceil((count - ring) / rings);
      const angle = -Math.PI / 2 + (Math.floor(index / rings) / ringItems) * Math.PI * 2 + ring * 0.27;
      const radius = 150 + ring * 95;
      positions.set(entity.id, { x: 450 + Math.cos(angle) * radius, y: 295 + Math.sin(angle) * radius });
    });
    return positions;
  }

  function renderGraph() {
    const nodeLayer = $("[data-node-layer]");
    const edgeLayer = $("[data-edge-layer]");
    nodeLayer.replaceChildren();
    edgeLayer.replaceChildren();
    const selection = graphSelection();
    const visibleIds = new Set(selection.entities.map((entity) => entity.id));
    const relationships = selection.relationships.filter((item) => visibleIds.has(item.source) && visibleIds.has(item.target));
    const positions = positionsFor(selection.entities);
    $("[data-graph-empty]").hidden = selection.entities.length > 0;
    if (!selection.entities.length) $("[data-graph-empty]").textContent = "This graph contains no accepted entities.";
    relationships.forEach((relationship) => {
      const source = positions.get(relationship.source);
      const target = positions.get(relationship.target);
      const line = svg("line", { x1: source.x, y1: source.y, x2: target.x, y2: target.y, class: `graph-edge ${state.selectedItem?.id === relationship.id ? "selected" : ""}`, tabindex: 0 });
      line.addEventListener("click", () => selectRelationship(relationship.id));
      line.addEventListener("keydown", (event) => { if (["Enter", " "].includes(event.key)) selectRelationship(relationship.id); });
      edgeLayer.appendChild(line);
      const label = svg("text", { x: (source.x + target.x) / 2, y: (source.y + target.y) / 2 - 6, class: "edge-label", "text-anchor": "middle" });
      label.textContent = truncate(humanize(relationship.type), 28);
      label.addEventListener("click", () => selectRelationship(relationship.id));
      edgeLayer.appendChild(label);
    });
    selection.entities.forEach((entity) => {
      const position = positions.get(entity.id);
      const group = svg("g", { class: `graph-node ${state.selectedItem?.id === entity.id ? "selected" : ""}`, transform: `translate(${position.x} ${position.y})`, tabindex: 0, role: "button", "aria-label": `${entity.name}, ${entity.type}` });
      group.appendChild(svg("circle", { r: 24, fill: TYPE_COLORS[entity.type] || TYPE_COLORS.other }));
      const name = svg("text", { y: 39 }); name.textContent = truncate(entity.name, 30); group.appendChild(name);
      const type = svg("text", { y: 52, class: "node-type" }); type.textContent = entity.type; group.appendChild(type);
      group.addEventListener("click", () => selectEntity(entity.id));
      group.addEventListener("keydown", (event) => { if (["Enter", " "].includes(event.key)) selectEntity(entity.id); });
      nodeLayer.appendChild(group);
    });
    const types = [...new Set(selection.entities.map((entity) => entity.type))].sort();
    $("[data-legend]").innerHTML = types.map((type) => `<span><i style="background:${TYPE_COLORS[type] || TYPE_COLORS.other}"></i>${escapeHtml(type)}</span>`).join("");
  }

  function selectEntity(id) { state.selectedItem = { kind: "entity", id }; renderGraph(); renderInspector(); }
  function selectRelationship(id) { state.selectedItem = { kind: "relationship", id }; renderGraph(); renderInspector(); }
  function evidenceHtml(evidence, grounding) {
    return `<div class="evidence-block"><p class="detail-label">Exact source quote</p>
      <blockquote>${escapeHtml(evidence.quote)}</blockquote>
      <p class="evidence-meta">Document ${escapeHtml(evidence.document_id)} · lines ${evidence.line_start}–${evidence.line_end}</p>
      ${evidence.source_url ? `<a href="${escapeHtml(evidence.source_url)}" rel="noreferrer">Open CIA source record ↗</a>` : ""}</div>
      ${grounding ? `<div class="evidence-block"><p class="detail-label">Grounded spans</p><div class="grounding">
        <div><span>Source mention</span><strong>${escapeHtml(grounding.source_mention)}</strong></div>
        <div><span>Relationship phrase</span><strong>${escapeHtml(grounding.relation_phrase)}</strong></div>
        <div><span>Target mention</span><strong>${escapeHtml(grounding.target_mention)}</strong></div>
      </div><p class="evidence-meta">${escapeHtml(grounding.support_reasoning)}</p></div>` : ""}`;
  }

  function renderInspector() {
    const container = $("[data-inspector]");
    if (!state.selectedItem) {
      container.innerHTML = '<div class="empty-state"><span class="empty-icon">⌁</span><strong>Select a node or relationship</strong><p>See its source document, exact quote, and extraction grounding here.</p></div>';
      return;
    }
    if (state.selectedItem.kind === "entity") {
      const entity = state.entitiesById.get(state.selectedItem.id);
      const attributes = Object.entries(entity.attributes || {}).map(([key, value]) => `<div><dt>${escapeHtml(humanize(key))}</dt><dd>${escapeHtml(Array.isArray(value) ? value.join(", ") : value)}</dd></div>`).join("");
      container.innerHTML = `<div class="inspector-kind">Entity · ${escapeHtml(entity.type)}</div><h3>${escapeHtml(entity.name)}</h3>
        <div class="inspector-subtitle">${entity.evidence.length} grounded source reference(s)</div>
        ${attributes ? `<div class="evidence-block"><p class="detail-label">Attributes</p><dl class="attribute-list">${attributes}</dl></div>` : ""}
        ${entity.evidence.map((item) => evidenceHtml(item)).join("")}`;
      return;
    }
    const relationship = state.graph.relationships.find((item) => item.id === state.selectedItem.id);
    const source = state.entitiesById.get(relationship.source);
    const target = state.entitiesById.get(relationship.target);
    container.innerHTML = `<div class="inspector-kind">Grounded relationship</div><h3>${escapeHtml(humanize(relationship.type))}</h3>
      <div class="expression"><strong>${escapeHtml(source.name)}</strong><span>${escapeHtml(humanize(relationship.type))} →</span><strong>${escapeHtml(target.name)}</strong></div>
      ${relationship.evidence.map((item, index) => evidenceHtml(item, relationship.groundings[index])).join("")}`;
  }

  async function downloadCurrentGraph(event) {
    if (!token()) return;
    event.preventDefault();
    try {
      const response = await fetch(`./api/graphs/${encodeURIComponent(state.graphId)}/export.json`, {
        headers: { Authorization: `Bearer ${token()}` },
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail || `Export failed with status ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `crest-${state.graphId}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast(`Export failed: ${error.message}`);
    }
  }

  function wireEvents() {
    $("[data-search-form]").addEventListener("submit", (event) => { event.preventDefault(); runSearch(new FormData(event.currentTarget).get("query"), $("[data-search-connector]").value); });
    $("[data-search-connector]").addEventListener("change", () => runSearch($("#query").value));
    $("[data-build-button]").addEventListener("click", startBuild);
    $("[data-token]").value = window.sessionStorage.getItem("crestOperatorToken") || "";
    $("[data-token]").addEventListener("change", async (event) => {
      if (event.target.value) window.sessionStorage.setItem("crestOperatorToken", event.target.value);
      else window.sessionStorage.removeItem("crestOperatorToken");
      await loadCapabilities();
      await loadGraphList();
      await runSearch($("#query").value);
    });
    $("[data-export-link]").addEventListener("click", downloadCurrentGraph);
    $("[data-graph-picker]").addEventListener("change", (event) => loadGraph(event.target.value));
    $("[data-connected-only]").addEventListener("change", renderGraph);
    $("[data-fit-button]").addEventListener("click", () => { $("#knowledge-graph").setAttribute("viewBox", "0 0 900 620"); toast("Graph fitted to the available canvas."); });
    $("[data-dialog-close]").addEventListener("click", () => $("[data-document-dialog]").close());
    $("[data-upload-open]").addEventListener("click", () => $("[data-upload-dialog]").showModal());
    $("[data-upload-close]").addEventListener("click", () => $("[data-upload-dialog]").close());
    $("[data-upload-form]").addEventListener("submit", uploadDocument);
    $("[data-upload-file]").addEventListener("change", (event) => {
      const file = event.target.files[0];
      $("[data-upload-file-label]").textContent = file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB` : "PDF, image, text, Markdown, CSV, or TSV";
    });
    $("[data-help-button]").addEventListener("click", () => $("[data-help-dialog]").showModal());
    $("[data-help-close]").addEventListener("click", () => $("[data-help-dialog]").close());
  }

  async function initialize() {
    wireEvents();
    await Promise.all([loadCapabilities(), loadGraphList(), runSearch("disinformation")]);
    await loadGraph("example-fixed-v2");
  }
  initialize().catch((error) => { $("[data-graph-empty]").textContent = `Workbench initialization failed: ${error.message}`; });
})();
