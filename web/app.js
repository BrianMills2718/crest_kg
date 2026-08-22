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
    collections: [], collectionId: null, jobs: [], polling: null,
    inquiries: [], inquiryPreview: null, activeInquiry: null,
    inquiryPolling: null, inquiryId: null,
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
  function activeCollection() {
    return state.collections.find((item) => item.id === state.collectionId) || null;
  }
  function rememberedCollectionId() {
    return window.localStorage.getItem("crestActiveCollection") || null;
  }
  function rememberCollection(collectionId) {
    if (collectionId) window.localStorage.setItem("crestActiveCollection", collectionId);
    else window.localStorage.removeItem("crestActiveCollection");
  }

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
      $("[data-inquiry-budget]").max = String(state.capabilities.max_evidence_budget_usd);
      updateInquiryEntry();
      updateBuildControls();
    } catch (error) {
      $("[data-connectors]").innerHTML = `<div class="inline-error">Capability request failed: ${escapeHtml(error.message)}</div>`;
    }
  }

  function renderCollectionControls() {
    const picker = $("[data-collection-picker]");
    const active = activeCollection();
    picker.innerHTML = '<option value="">All documents</option>' + state.collections.map((collection) =>
      `<option value="${escapeHtml(collection.id)}">${escapeHtml(collection.title)} · ${collection.document_ids.length}</option>`
    ).join("");
    picker.value = active?.id || "";
    picker.disabled = !state.capabilities?.graph_build_authorized;
    $("[data-collection-new]").disabled = !state.capabilities?.graph_build_authorized;
    $("[data-collection-scope-wrap]").hidden = !active;
    const summary = $("[data-collection-summary]");
    if (!active) {
      summary.textContent = state.capabilities?.graph_build_authorized
        ? "Choose or create a collection to organize a research thread."
        : "Collections are private; open through the tailnet or enter the operator token.";
    } else {
      summary.innerHTML = `<span><strong>${escapeHtml(active.title)}</strong> · ${active.document_ids.length} source${active.document_ids.length === 1 ? "" : "s"}${active.description ? ` · ${escapeHtml(active.description)}` : ""}</span><button class="text-button danger" type="button" data-collection-delete>Delete collection</button>`;
      summary.querySelector("[data-collection-delete]").addEventListener("click", deleteActiveCollection);
    }
    updateInquiryEntry();
  }

  function updateInquiryEntry() {
    const button = $("[data-inquiry-open]");
    if (!button) return;
    const capabilities = state.capabilities;
    const active = activeCollection();
    const authorized = capabilities?.evidence_brief_enabled && capabilities?.evidence_brief_authorized;
    button.disabled = !active || !active.document_ids.length || !authorized;
    if (!active) button.title = "Choose a research collection first.";
    else if (!active.document_ids.length) button.title = "Add at least one source to this collection.";
    else if (!capabilities?.evidence_brief_enabled) button.title = "Evidence briefs are disabled on this server.";
    else if (!capabilities?.evidence_brief_authorized) button.title = "Open through the tailnet or enter the operator token.";
    else button.title = `Ask an evidence-grounded question across ${active.document_ids.length} source${active.document_ids.length === 1 ? "" : "s"}.`;
  }

  async function loadCollections(preferredId = state.collectionId || rememberedCollectionId()) {
    if (!state.capabilities?.graph_build_authorized) {
      state.collections = [];
      state.collectionId = null;
      renderCollectionControls();
      return;
    }
    try {
      const response = await api("collections", { operator: true });
      state.collections = response.collections;
      state.collectionId = state.collections.some((item) => item.id === preferredId) ? preferredId : null;
      rememberCollection(state.collectionId);
      renderCollectionControls();
    } catch (error) {
      state.collections = [];
      state.collectionId = null;
      renderCollectionControls();
      toast(`Collection request failed: ${error.message}`);
    }
  }

  async function createCollection(event) {
    event.preventDefault();
    const submit = $("[data-collection-submit]");
    const status = $("[data-collection-status]");
    submit.disabled = true;
    status.textContent = "Creating durable collection…";
    try {
      const collection = await api("collections", {
        method: "POST", operator: true,
        body: JSON.stringify({
          title: $("[data-collection-title]").value,
          description: $("[data-collection-description]").value,
        }),
      });
      await loadCollections(collection.id);
      rememberCollection(collection.id);
      state.selectedDocuments.clear();
      state.inquiryId = null;
      $("[data-collection-scope]").checked = true;
      $("[data-collection-dialog]").close();
      await runSearch($("#query").value);
      updateBuildControls();
      toast(`${collection.title} is ready for sources.`);
    } catch (error) {
      status.textContent = `Collection creation failed: ${error.message}`;
    } finally {
      submit.disabled = false;
    }
  }

  async function replaceCollectionDocuments(documentIds) {
    const active = activeCollection();
    if (!active) return;
    const updated = await api(`collections/${encodeURIComponent(active.id)}/documents`, {
      method: "PUT", operator: true,
      body: JSON.stringify({ document_ids: documentIds }),
    });
    state.collections = state.collections.map((item) => item.id === updated.id ? updated : item);
    renderCollectionControls();
  }

  async function toggleCollectionMembership(documentId) {
    const active = activeCollection();
    if (!active) return;
    const isMember = active.document_ids.includes(documentId);
    const nextIds = isMember
      ? active.document_ids.filter((item) => item !== documentId)
      : [...active.document_ids, documentId];
    try {
      await replaceCollectionDocuments(nextIds);
      if (isMember) state.selectedDocuments.delete(documentId);
      state.inquiryId = null;
      renderResults();
      updateBuildControls();
      toast(`${isMember ? "Removed from" : "Added to"} ${active.title}.`);
    } catch (error) {
      toast(`Collection update failed: ${error.message}`);
    }
  }

  async function deleteActiveCollection() {
    const active = activeCollection();
    if (!active || !window.confirm(`Delete the collection “${active.title}”? Its source documents and graphs will be retained.`)) return;
    try {
      await api(`collections/${encodeURIComponent(active.id)}`, { method: "DELETE", operator: true });
      state.collectionId = null;
      rememberCollection(null);
      state.selectedDocuments.clear();
      state.inquiryId = null;
      await loadCollections();
      await runSearch($("#query").value);
      updateBuildControls();
      toast("Collection deleted. Its sources and completed graphs were retained.");
    } catch (error) {
      toast(`Collection deletion failed: ${error.message}`);
    }
  }

  async function runSearch(query, connectorId = $("[data-search-connector]").value) {
    const results = $("[data-results]");
    const errorBox = $("[data-search-error]");
    errorBox.hidden = true;
    results.innerHTML = '<div class="empty-state compact">Searching source text…</div>';
    try {
      const scopedCollectionId = state.collectionId && $("[data-collection-scope]").checked ? state.collectionId : null;
      const response = await api("search", {
        method: "POST", operator: true,
        body: JSON.stringify({ query, connector_id: connectorId, limit: 30, collection_id: scopedCollectionId }),
      });
      state.results = response.results;
      $("[data-result-count]").textContent = `${response.total_matches} matches`;
      const sourceLabel = $("[data-search-connector]").selectedOptions[0]?.textContent || response.connector_id;
      const scopeLabel = scopedCollectionId ? ` within ${activeCollection()?.title}` : "";
      $("[data-search-meta]").textContent = `${sourceLabel}${scopeLabel} · query “${response.query}”.`;
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
      const scoped = activeCollection() && $("[data-collection-scope]").checked;
      container.innerHTML = `<div class="empty-state compact">No tracked documents matched this query.${scoped ? " Uncheck collection-only search to find sources to add." : ""}</div>`;
      return;
    }
    container.innerHTML = state.results.map((result) => {
      const selected = state.selectedDocuments.has(result.document_id);
      const collection = activeCollection();
      const isMember = collection?.document_ids.includes(result.document_id) || false;
      const metadata = [result.document_type, result.publication_date, result.page_count ? `${result.page_count} pp.` : null].filter(Boolean).join(" · ");
      return `<article class="result-card ${selected ? "is-selected" : ""}" data-result-id="${escapeHtml(result.document_id)}">
        <input type="checkbox" aria-label="Select ${escapeHtml(result.title)}" ${selected ? "checked" : ""} ${collection && !isMember ? "disabled" : ""} />
        <div><h3>${escapeHtml(result.title)}</h3>
          <div class="result-meta"><span class="source-badge ${result.connector_id === "user-uploads" ? "private" : ""}">${result.connector_id === "user-uploads" ? "Private upload" : result.connector_id === "cia-reading-room-live" ? "CIA live" : "Bundled CREST"}</span> ${escapeHtml(result.document_id)}${metadata ? ` · ${escapeHtml(metadata)}` : ""}</div>
          <p>${escapeHtml(truncate(result.snippet, 280))}</p>
          <div class="result-actions"><button class="text-button" type="button" data-inspect-document>Inspect source</button>${collection ? `<button class="text-button ${isMember ? "danger" : ""}" type="button" data-toggle-membership>${isMember ? "Remove from" : "Add to"} ${escapeHtml(collection.title)}</button>` : ""}</div>
        </div></article>`;
    }).join("");
    container.querySelectorAll("[data-result-id]").forEach((card) => {
      const id = card.dataset.resultId;
      card.querySelector("input").addEventListener("change", (event) => toggleDocument(id, event.target.checked));
      card.querySelector("[data-inspect-document]").addEventListener("click", () => inspectDocument(id));
      card.querySelector("[data-toggle-membership]")?.addEventListener("click", () => toggleCollectionMembership(id));
    });
  }

  function toggleDocument(documentId, shouldSelect) {
    const result = state.results.find((item) => item.document_id === documentId);
    if (shouldSelect && state.selectedDocuments.size >= 3) {
      toast("A graph build is limited to three documents in this development vertical.");
      renderResults();
      return;
    }
    state.inquiryId = null;
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
    const files = [...fileInput.files];
    if (!files.length) { status.textContent = "Choose at least one source file first."; return; }
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    if (state.collectionId) form.append("collection_id", state.collectionId);
    submit.disabled = true;
    const results = $("[data-batch-results]");
    results.hidden = true;
    status.textContent = `Extracting and indexing ${files.length} source${files.length === 1 ? "" : "s"}…`;
    try {
      const receipt = await api("uploads/batch", { method: "POST", body: form, operator: true });
      status.textContent = `${receipt.successes.length} added · ${receipt.failures.length} failed.`;
      results.innerHTML = [
        ...receipt.successes.map((item) => `<div class="batch-result success"><strong>${escapeHtml(item.title)}</strong><span>${item.duplicate ? "Already present" : "Added"} · ${item.body_chars.toLocaleString()} characters · ${escapeHtml(humanize(item.extraction_method))}</span></div>`),
        ...receipt.failures.map((item) => `<div class="batch-result failure"><strong>${escapeHtml(item.filename)}</strong><span>${escapeHtml(item.detail)}</span></div>`),
      ].join("");
      results.hidden = false;
      toast(`${receipt.successes.length} source${receipt.successes.length === 1 ? " is" : "s are"} now searchable${activeCollection() ? ` in ${activeCollection().title}` : ""}.`);
      $("[data-search-connector]").value = "all";
      if (receipt.successes[0]) $("#query").value = receipt.successes[0].title;
      await loadCapabilities();
      await loadCollections(state.collectionId);
      await runSearch($("#query").value, "all");
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
      state.inquiryId = null;
      $("[data-document-dialog]").close();
      toast("Private source deleted. Existing restricted graphs were retained.");
      await loadCapabilities();
      await loadCollections(state.collectionId);
      await runSearch($("#query").value);
      updateBuildControls();
    } catch (error) {
      toast(`Delete failed: ${error.message}`);
    }
  }

  function renderInquiryEvidence(evidence) {
    const container = $("[data-inquiry-evidence]");
    $("[data-inquiry-evidence-count]").textContent = evidence.length ? `${evidence.length} passage${evidence.length === 1 ? "" : "s"}` : "No matches";
    if (!evidence.length) {
      container.innerHTML = '<div class="empty-state compact"><strong>No supported passage found</strong><p>You can still create a zero-cost insufficient-evidence brief, or refine the question.</p></div>';
      return;
    }
    container.innerHTML = evidence.map((item) => `<article class="evidence-card">
      <div class="evidence-card-heading"><span class="evidence-rank">${item.rank}</span><div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.document_id)} · score ${Number(item.score).toFixed(2)}</span></div></div>
      <blockquote>${escapeHtml(item.text)}</blockquote>
      <div class="evidence-card-footer"><span>Exact characters ${item.start_char.toLocaleString()}–${item.end_char.toLocaleString()} · ${escapeHtml(item.matched_terms.join(", ") || "semantic match")}</span><button class="text-button" type="button" data-evidence-source="${escapeHtml(item.document_id)}">Open full source</button></div>
    </article>`).join("");
    container.querySelectorAll("[data-evidence-source]").forEach((button) => button.addEventListener("click", () => inspectDocument(button.dataset.evidenceSource)));
  }

  function citationTitles(citationIds, evidenceById) {
    return citationIds.map((id) => {
      const item = evidenceById.get(id);
      return item ? `<span class="citation-chip" title="${escapeHtml(id)}">${item.rank}. ${escapeHtml(item.title)}</span>` : "";
    }).join("");
  }

  function citedDocumentIds(inquiry) {
    if (!inquiry?.brief) return [];
    const cited = new Set([
      ...inquiry.brief.synthesis_citation_ids,
      ...inquiry.brief.findings.flatMap((finding) => finding.citation_ids),
    ]);
    return inquiry.evidence.filter((item) => cited.has(item.id))
      .map((item) => item.document_id).filter((id, index, ids) => ids.indexOf(id) === index);
  }

  function renderInquiryBrief(inquiry) {
    const container = $("[data-inquiry-brief]");
    const stateLabel = $("[data-inquiry-brief-state]");
    if (!inquiry) {
      stateLabel.textContent = "Preview first";
      container.innerHTML = '<div class="empty-state compact">The brief will preserve support, contradiction, and uncertainty with source citations.</div>';
      return;
    }
    stateLabel.textContent = humanize(inquiry.state);
    if (["queued", "running"].includes(inquiry.state)) {
      container.innerHTML = `<div class="brief-progress"><i></i><strong>${escapeHtml(humanize(inquiry.state))}</strong><span>${escapeHtml(inquiry.progress_detail)}</span><small>The shared provider lane serializes this brief with graph extraction.</small></div>`;
      return;
    }
    if (inquiry.state === "failed") {
      container.innerHTML = `<div class="inline-error"><strong>Brief generation failed.</strong><br>${escapeHtml(inquiry.error || inquiry.progress_detail)}</div><p class="recovery-note">The ranked evidence remains available at left and this failure is preserved in Recent activity.</p>`;
      return;
    }
    const brief = inquiry.brief;
    const evidenceById = new Map(inquiry.evidence.map((item) => [item.id, item]));
    const citedDocuments = citedDocumentIds(inquiry);
    const canHandoff = Boolean(state.collections.find((item) => item.id === inquiry.request.collection_id)) && citedDocuments.length > 0;
    container.innerHTML = `<article class="brief-answer ${escapeHtml(brief.answer_status)}">
      <div class="brief-answer-heading"><span>${escapeHtml(humanize(brief.answer_status))}</span><small>$${Number(brief.observed_cost_usd).toFixed(4)} · ${escapeHtml(brief.model)}</small></div>
      <p>${escapeHtml(brief.synthesis)}</p>
      <div class="citation-row">${citationTitles(brief.synthesis_citation_ids, evidenceById)}</div>
    </article>
    <div class="brief-findings">${brief.findings.map((finding) => `<article class="brief-finding ${escapeHtml(finding.classification)}"><span>${escapeHtml(humanize(finding.classification))}</span><p>${escapeHtml(finding.statement)}</p><div class="citation-row">${citationTitles(finding.citation_ids, evidenceById)}</div></article>`).join("") || '<p class="recovery-note">No supported findings were returned.</p>'}</div>
    ${brief.unresolved_questions.length ? `<div class="unresolved"><strong>Still unresolved</strong><ul>${brief.unresolved_questions.map((question) => `<li>${escapeHtml(question)}</li>`).join("")}</ul></div>` : ""}
    <div class="brief-handoff"><button class="button primary" type="button" data-inquiry-handoff ${canHandoff ? "" : "disabled"}>Use cited sources for a focused graph</button><span>${canHandoff ? `${citedDocuments.length} cited source${citedDocuments.length === 1 ? "" : "s"} will be selected; graph extraction has its own stated ceiling.` : "The original collection or cited source is no longer available for a graph build."}</span></div>`;
    container.querySelector("[data-inquiry-handoff]")?.addEventListener("click", () => handoffInquiryToGraph(inquiry));
  }

  function renderInquiry() {
    const inquiry = state.activeInquiry;
    const preview = state.inquiryPreview;
    const evidence = inquiry?.evidence || preview?.evidence || [];
    renderInquiryEvidence(evidence);
    renderInquiryBrief(inquiry);
    const status = $("[data-inquiry-status]");
    const generate = $("[data-inquiry-generate]");
    if (inquiry) {
      status.textContent = inquiry.state === "completed" ? `Completed · trace ${inquiry.trace_id}` : inquiry.progress_detail;
      generate.disabled = true;
    } else if (preview) {
      status.textContent = evidence.length
        ? "Evidence ranked deterministically · no model spend yet."
        : "No passage matched · an insufficient-evidence brief costs $0.";
      generate.disabled = !state.capabilities?.evidence_brief_authorized;
    } else {
      status.textContent = "Preview ranked passages before authorizing a brief.";
      generate.disabled = true;
    }
  }

  function openInquiryDialog(inquiry = null) {
    const active = activeCollection();
    if (!inquiry && !active) return;
    window.clearTimeout(state.inquiryPolling);
    state.activeInquiry = inquiry;
    state.inquiryPreview = inquiry ? { collection_id: inquiry.request.collection_id, question: inquiry.request.question, evidence: inquiry.evidence } : null;
    $("[data-inquiry-form]").reset();
    $("[data-inquiry-question]").value = inquiry?.request.question || "";
    $("[data-inquiry-question]").disabled = Boolean(inquiry);
    $("[data-inquiry-preview]").disabled = Boolean(inquiry);
    const ceiling = Math.min(0.06, Number(state.capabilities?.max_evidence_budget_usd || 0.06));
    $("[data-inquiry-budget]").value = String(inquiry?.request.max_budget_usd || ceiling);
    $("[data-inquiry-budget]").disabled = Boolean(inquiry);
    $("[data-inquiry-title]").textContent = inquiry ? inquiry.collection_title : `Ask ${active.title}`;
    renderInquiry();
    $("[data-inquiry-dialog]").showModal();
    if (!inquiry) $("[data-inquiry-question]").focus();
    else if (["queued", "running"].includes(inquiry.state)) pollInquiry(inquiry.id);
  }

  async function previewInquiry(event) {
    event.preventDefault();
    const active = activeCollection();
    const question = $("[data-inquiry-question]").value.trim();
    if (!active || question.length < 3) return;
    $("[data-inquiry-preview]").disabled = true;
    $("[data-inquiry-generate]").disabled = true;
    $("[data-inquiry-status]").textContent = "Ranking exact collection passages…";
    try {
      state.activeInquiry = null;
      state.inquiryPreview = await api("evidence/preview", {
        method: "POST", operator: true,
        body: JSON.stringify({ collection_id: active.id, question, evidence_limit: 6 }),
      });
      renderInquiry();
    } catch (error) {
      state.inquiryPreview = null;
      renderInquiry();
      $("[data-inquiry-status]").textContent = `Evidence preview failed: ${error.message}`;
    } finally {
      $("[data-inquiry-preview]").disabled = false;
    }
  }

  async function submitInquiry() {
    const preview = state.inquiryPreview;
    if (!preview || state.activeInquiry) return;
    const generate = $("[data-inquiry-generate]");
    generate.disabled = true;
    $("[data-inquiry-status]").textContent = "Persisting evidence and requesting one traced brief…";
    try {
      state.activeInquiry = await api("inquiries", {
        method: "POST", operator: true,
        body: JSON.stringify({
          collection_id: preview.collection_id,
          question: preview.question,
          evidence_limit: 6,
          max_budget_usd: Number($("[data-inquiry-budget]").value),
        }),
      });
      renderInquiry();
      await loadInquiries();
      pollInquiry(state.activeInquiry.id);
    } catch (error) {
      $("[data-inquiry-status]").textContent = `Brief request rejected: ${error.message}`;
      generate.disabled = false;
    }
  }

  async function pollInquiry(inquiryId) {
    window.clearTimeout(state.inquiryPolling);
    try {
      const inquiry = await api(`inquiries/${encodeURIComponent(inquiryId)}`, { operator: true });
      state.activeInquiry = inquiry;
      renderInquiry();
      await loadInquiries();
      if (["queued", "running"].includes(inquiry.state)) {
        state.inquiryPolling = window.setTimeout(() => pollInquiry(inquiryId), 1400);
      } else if (inquiry.state === "completed") toast("Evidence brief completed with inspectable citations.");
    } catch (error) {
      $("[data-inquiry-status]").textContent = `Inquiry status failed: ${error.message}`;
    }
  }

  async function handoffInquiryToGraph(inquiry) {
    const collection = state.collections.find((item) => item.id === inquiry.request.collection_id);
    if (!collection) { toast("The original collection is no longer available for graph handoff."); return; }
    const citedIds = citedDocumentIds(inquiry);
    const selectedIds = citedIds.slice(0, 3);
    state.collectionId = collection.id;
    rememberCollection(collection.id);
    state.selectedDocuments = new Map(selectedIds.map((documentId) => {
      const evidence = inquiry.evidence.find((item) => item.document_id === documentId);
      return [documentId, { document_id: documentId, title: evidence?.title || documentId }];
    }));
    state.inquiryId = inquiry.id;
    $("[data-collection-scope]").checked = true;
    renderCollectionControls();
    await runSearch(inquiry.request.question);
    updateBuildControls();
    $("[data-inquiry-dialog]").close();
    $("[data-history-dialog]").close();
    $("[data-build-button]").scrollIntoView({ behavior: "smooth", block: "center" });
    toast(citedIds.length > 3 ? "The three highest-ranked cited sources are ready for the focused graph." : `${selectedIds.length} cited source${selectedIds.length === 1 ? " is" : "s are"} ready for the focused graph.`);
  }

  function renderInquiries() {
    const container = $("[data-inquiry-history]");
    if (!state.capabilities?.evidence_brief_authorized) {
      container.innerHTML = '<div class="empty-state compact">Evidence inquiries are private. Open through the tailnet or enter the operator token.</div>';
      return;
    }
    if (!state.inquiries.length) {
      container.innerHTML = '<div class="empty-state compact">No evidence inquiries have been submitted yet.</div>';
      return;
    }
    container.innerHTML = state.inquiries.map((inquiry) => `<article class="job-card ${escapeHtml(inquiry.state)}">
      <div class="job-card-heading"><strong>${escapeHtml(inquiry.collection_title)}</strong><time>${escapeHtml(new Date(inquiry.updated_at).toLocaleString())}</time></div>
      <p>${escapeHtml(truncate(inquiry.request.question, 150))}</p>
      <span>${escapeHtml(inquiry.error || inquiry.progress_detail)} · ${inquiry.evidence.length} retained passage${inquiry.evidence.length === 1 ? "" : "s"}</span>
      <button class="button ghost small" type="button" data-open-inquiry="${escapeHtml(inquiry.id)}">Open ${inquiry.state === "completed" ? "evidence brief" : "inquiry"}</button>
    </article>`).join("");
    container.querySelectorAll("[data-open-inquiry]").forEach((button) => button.addEventListener("click", () => {
      const inquiry = state.inquiries.find((item) => item.id === button.dataset.openInquiry);
      if (!inquiry) return;
      $("[data-history-dialog]").close();
      openInquiryDialog(inquiry);
    }));
  }

  async function loadInquiries() {
    if (!state.capabilities?.evidence_brief_authorized) {
      state.inquiries = [];
      renderInquiries();
      return;
    }
    try {
      state.inquiries = (await api("inquiries", { operator: true })).inquiries;
      renderInquiries();
    } catch (error) {
      $("[data-inquiry-history]").innerHTML = `<div class="inline-error">Inquiry history failed: ${escapeHtml(error.message)}</div>`;
    }
  }

  function updateBuildControls() {
    const count = state.selectedDocuments.size;
    $("[data-selected-count]").textContent = count;
    const labels = [...state.selectedDocuments.values()].map((item) => item.title);
    $("[data-selected-labels]").textContent = labels.length
      ? `${state.inquiryId ? "Cited evidence handoff · " : ""}${labels.join(" · ")}`
      : "Choose up to three search results.";
    const button = $("[data-build-button]");
    const status = $("[data-build-status]");
    const capabilities = state.capabilities;
    const collection = activeCollection();
    const outsideCollection = collection && [...state.selectedDocuments.keys()].some((id) => !collection.document_ids.includes(id));
    button.disabled = !count || !capabilities || !capabilities.graph_build_enabled || !capabilities.graph_build_authorized || outsideCollection;
    if (!count) status.textContent = "Search and select a document to begin.";
    else if (!capabilities?.graph_build_enabled) status.textContent = "Graph building is disabled on this server.";
    else if (!capabilities.graph_build_authorized) status.textContent = "Open through the tailnet or enter the operator token.";
    else if (outsideCollection) status.textContent = `Add every selected source to ${collection.title} before building.`;
    else status.textContent = state.inquiryId
      ? "Cited sources only · the graph will retain the evidence-inquiry provenance."
      : "Authorized · one traced build will use the stated ceiling.";
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
          collection_id: state.collectionId,
          inquiry_id: state.inquiryId,
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
        await loadJobs();
        updateBuildControls();
      } else if (job.state === "failed") {
        $("[data-build-status]").textContent = `Build failed: ${job.error}`;
        await loadJobs();
        updateBuildControls();
      } else {
        await loadJobs();
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

  function renderJobs() {
    const container = $("[data-job-history]");
    if (!state.capabilities?.graph_build_authorized) {
      container.innerHTML = '<div class="empty-state compact">Recent jobs are private. Open through the tailnet or enter the operator token.</div>';
      return;
    }
    if (!state.jobs.length) {
      container.innerHTML = '<div class="empty-state compact">No graph builds have been submitted yet.</div>';
      return;
    }
    container.innerHTML = state.jobs.map((job) => `<article class="job-card ${escapeHtml(job.state)}">
      <div class="job-card-heading"><strong>${escapeHtml(humanize(job.state))}</strong><time>${escapeHtml(new Date(job.updated_at).toLocaleString())}</time></div>
      <p>${job.request.document_ids.length} document${job.request.document_ids.length === 1 ? "" : "s"}${job.request.collection_id ? " · collection build" : ""} · ceiling $${Number(job.request.max_budget_usd).toFixed(2)}</p>
      <span>${escapeHtml(job.error || job.progress_detail)}</span>
      ${job.graph_id ? `<button class="button ghost small" type="button" data-open-job-graph="${escapeHtml(job.graph_id)}">Open completed graph</button>` : ""}
    </article>`).join("");
    container.querySelectorAll("[data-open-job-graph]").forEach((button) => button.addEventListener("click", async () => {
      await loadGraph(button.dataset.openJobGraph);
      $("[data-history-dialog]").close();
    }));
  }

  async function loadJobs() {
    if (!state.capabilities?.graph_build_authorized) {
      state.jobs = [];
      renderJobs();
      return;
    }
    try {
      state.jobs = (await api("jobs", { operator: true })).jobs;
      renderJobs();
    } catch (error) {
      $("[data-job-history]").innerHTML = `<div class="inline-error">Job history failed: ${escapeHtml(error.message)}</div>`;
    }
  }

  function requireGraph(payload) {
    if (!payload || payload.schema_version !== "crest-kg-v2") throw new Error("Expected a crest-kg-v2 graph artifact.");
    for (const field of ["documents", "entities", "relationships"]) {
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
    // Name the example as an example in the page's largest text. It was titled
    // like saved work, so it read as the viewer's own graph on a panel they
    // never asked to fill -- the landing view is step 03 of a five-step tool.
    $("[data-graph-title]").textContent = example
      ? "Example graph · five-document evidence checkpoint"
      : `${graph.documents.length}-document generated graph`;
    for (const field of ["documents", "entities", "relationships"]) {
      $(`[data-metric="${field}"]`).textContent = graph[field].length.toLocaleString();
    }
    // Rejected candidates belong with provenance, not in the headline metrics:
    // they are what the extractor discarded, not something the reader can act on.
    const discarded = `${graph.rejections.length.toLocaleString()} candidates discarded`;
    $("[data-graph-provenance]").textContent = example
      ? `Labeled example · fixed artifact · ${discarded} · corpus recall remains unknown.`
      : `Generated ${new Date(graph.generated_at).toLocaleString()} · ${discarded} · trace ${graph.trace_id}`;
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
    $("[data-collection-picker]").addEventListener("change", async (event) => {
      state.collectionId = event.target.value || null;
      rememberCollection(state.collectionId);
      state.selectedDocuments.clear();
      state.inquiryId = null;
      $("[data-collection-scope]").checked = Boolean(state.collectionId);
      renderCollectionControls();
      await runSearch($("#query").value);
      updateBuildControls();
    });
    $("[data-collection-scope]").addEventListener("change", () => runSearch($("#query").value));
    $("[data-collection-new]").addEventListener("click", () => {
      $("[data-collection-form]").reset();
      $("[data-collection-status]").textContent = "Sources can be added after creation or during upload.";
      $("[data-collection-dialog]").showModal();
      $("[data-collection-title]").focus();
    });
    $("[data-collection-close]").addEventListener("click", () => $("[data-collection-dialog]").close());
    $("[data-collection-form]").addEventListener("submit", createCollection);
    $("[data-inquiry-open]").addEventListener("click", () => openInquiryDialog());
    $("[data-inquiry-close]").addEventListener("click", () => {
      window.clearTimeout(state.inquiryPolling);
      $("[data-inquiry-dialog]").close();
    });
    $("[data-inquiry-form]").addEventListener("submit", previewInquiry);
    $("[data-inquiry-generate]").addEventListener("click", submitInquiry);
    $("[data-build-button]").addEventListener("click", startBuild);
    $("[data-token]").value = window.sessionStorage.getItem("crestOperatorToken") || "";
    $("[data-token]").addEventListener("change", async (event) => {
      if (event.target.value) window.sessionStorage.setItem("crestOperatorToken", event.target.value);
      else window.sessionStorage.removeItem("crestOperatorToken");
      await loadCapabilities();
      await loadCollections();
      await loadGraphList();
      await Promise.all([loadInquiries(), loadJobs()]);
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
      const files = [...event.target.files];
      const totalBytes = files.reduce((sum, file) => sum + file.size, 0);
      $("[data-upload-file-label]").textContent = files.length ? `${files.length} file${files.length === 1 ? "" : "s"} · ${(totalBytes / 1024 / 1024).toFixed(2)} MB total` : "Up to 10 PDF, image, text, Markdown, CSV, or TSV files";
    });
    $("[data-help-button]").addEventListener("click", () => $("[data-help-dialog]").showModal());
    $("[data-help-close]").addEventListener("click", () => $("[data-help-dialog]").close());
    $("[data-history-open]").addEventListener("click", async () => {
      $("[data-history-dialog]").showModal();
      await Promise.all([loadInquiries(), loadJobs()]);
    });
    $("[data-history-close]").addEventListener("click", () => $("[data-history-dialog]").close());
  }

  async function initialize() {
    wireEvents();
    await loadCapabilities();
    await loadCollections();
    await Promise.all([loadGraphList(), loadInquiries(), loadJobs(), runSearch("disinformation")]);
    await loadGraph("example-fixed-v2");
  }
  initialize().catch((error) => { $("[data-graph-empty]").textContent = `Workbench initialization failed: ${error.message}`; });
})();
