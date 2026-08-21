(function () {
  "use strict";

  const TYPE_COLORS = {
    person: "#b24b3b",
    organization: "#244f72",
    location: "#547a56",
    concept: "#7b5b91",
    event: "#a06a2b",
    work: "#397675",
    other: "#6f7479",
  };

  const state = {
    graph: null,
    entitiesById: new Map(),
    selectedKind: null,
    selectedId: null,
    positions: new Map(),
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function humanize(value) {
    return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function truncate(value, length) {
    const text = String(value || "");
    return text.length > length ? `${text.slice(0, length - 1)}…` : text;
  }

  function requireGraph(payload) {
    if (!payload || payload.schema_version !== "crest-kg-v2") {
      throw new Error("Expected a crest-kg-v2 graph artifact.");
    }
    for (const key of ["documents", "entities", "relationships", "rejections"]) {
      if (!Array.isArray(payload[key])) throw new Error(`Graph field ${key} is missing or invalid.`);
    }
    const ids = new Set(payload.entities.map((entity) => entity.id));
    for (const relationship of payload.relationships) {
      if (!ids.has(relationship.source) || !ids.has(relationship.target)) {
        throw new Error(`Relationship ${relationship.id} has a missing endpoint.`);
      }
      if (!Array.isArray(relationship.groundings) || relationship.groundings.length === 0) {
        throw new Error(`Relationship ${relationship.id} has no exact grounding.`);
      }
    }
    return payload;
  }

  function setView(viewName) {
    document.querySelectorAll("[data-view-panel]").forEach((panel) => {
      panel.hidden = panel.dataset.viewPanel !== viewName;
    });
    document.querySelectorAll("[data-view-button]").forEach((button) => {
      const active = button.dataset.viewButton === viewName;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function updateMetrics(graph) {
    const values = {
      documents: graph.documents.length,
      entities: graph.entities.length,
      relationships: graph.relationships.length,
      rejections: graph.rejections.length,
    };
    Object.entries(values).forEach(([key, value]) => {
      document.querySelector(`[data-metric="${key}"]`).textContent = value.toLocaleString();
    });
  }

  function connectedComponents(relationships) {
    const adjacency = new Map();
    relationships.forEach((relationship) => {
      if (!adjacency.has(relationship.source)) adjacency.set(relationship.source, new Set());
      if (!adjacency.has(relationship.target)) adjacency.set(relationship.target, new Set());
      adjacency.get(relationship.source).add(relationship.target);
      adjacency.get(relationship.target).add(relationship.source);
    });
    const seen = new Set();
    const components = [];
    [...adjacency.keys()].sort().forEach((start) => {
      if (seen.has(start)) return;
      const component = [];
      const queue = [start];
      seen.add(start);
      while (queue.length) {
        const current = queue.shift();
        component.push(current);
        [...adjacency.get(current)].sort().forEach((neighbor) => {
          if (!seen.has(neighbor)) {
            seen.add(neighbor);
            queue.push(neighbor);
          }
        });
      }
      components.push(component);
    });
    return components.sort((a, b) => b.length - a.length || a[0].localeCompare(b[0]));
  }

  function computePositions(graph) {
    const components = connectedComponents(graph.relationships);
    const height = Math.max(430, components.length * 210 + 30);
    const positions = new Map();
    const indegree = new Map();
    graph.relationships.forEach((relationship) => {
      indegree.set(relationship.source, indegree.get(relationship.source) || 0);
      indegree.set(relationship.target, (indegree.get(relationship.target) || 0) + 1);
    });
    components.forEach((component, componentIndex) => {
      const bandTop = 20 + componentIndex * 210;
      const sources = component.filter((id) => (indegree.get(id) || 0) === 0);
      const targets = component.filter((id) => !sources.includes(id));
      const left = sources.length ? sources : component.slice(0, 1);
      const right = targets.length ? targets : component.slice(1);
      left.forEach((id, index) => positions.set(id, { x: 150, y: bandTop + ((index + 1) * 170) / (left.length + 1) }));
      right.forEach((id, index) => positions.set(id, { x: 610, y: bandTop + ((index + 1) * 170) / (right.length + 1) }));
    });
    return { positions, height };
  }

  function svgElement(name, attributes = {}) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
  }

  function relationshipLabel(relationship) {
    const source = state.entitiesById.get(relationship.source);
    const target = state.entitiesById.get(relationship.target);
    return `${source.name} · ${humanize(relationship.type)} · ${target.name}`;
  }

  function renderGraph() {
    const graph = state.graph;
    const layer = document.querySelector("[data-graph-layer]");
    layer.replaceChildren();
    const layout = computePositions(graph);
    state.positions = layout.positions;
    const svg = document.getElementById("relationship-graph");
    svg.setAttribute("viewBox", `0 0 760 ${layout.height}`);

    graph.relationships.forEach((relationship) => {
      const source = layout.positions.get(relationship.source);
      const target = layout.positions.get(relationship.target);
      const dx = target.x - source.x;
      const startX = source.x + Math.sign(dx) * 47;
      const endX = target.x - Math.sign(dx) * 47;
      const path = svgElement("path", {
        d: `M ${startX} ${source.y} L ${endX} ${target.y}`,
        class: "graph-edge",
        "data-relationship-id": relationship.id,
        "marker-end": "url(#arrowhead)",
        tabindex: "0",
        role: "button",
        "aria-label": relationshipLabel(relationship),
      });
      path.addEventListener("click", () => selectRelationship(relationship.id));
      path.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") selectRelationship(relationship.id);
      });
      layer.appendChild(path);
      const label = svgElement("text", {
        x: String((source.x + target.x) / 2),
        y: String((source.y + target.y) / 2 - 8),
        class: "graph-edge-label",
        "text-anchor": "middle",
        "data-relationship-id": relationship.id,
      });
      label.textContent = humanize(relationship.type);
      label.addEventListener("click", () => selectRelationship(relationship.id));
      layer.appendChild(label);
    });

    [...layout.positions.entries()].forEach(([entityId, position]) => {
      const entity = state.entitiesById.get(entityId);
      const group = svgElement("g", {
        class: "graph-node",
        transform: `translate(${position.x} ${position.y})`,
        tabindex: "0",
        role: "button",
        "aria-label": `${entity.name}, ${entity.type}`,
        "data-entity-id": entity.id,
      });
      group.appendChild(svgElement("circle", { r: "40", fill: TYPE_COLORS[entity.type] || TYPE_COLORS.other }));
      const name = svgElement("text", { y: "58" });
      name.textContent = truncate(entity.name, 28);
      group.appendChild(name);
      const type = svgElement("text", { y: "73", class: "graph-node-type" });
      type.textContent = entity.type;
      group.appendChild(type);
      group.addEventListener("click", () => selectEntity(entity.id));
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") selectEntity(entity.id);
      });
      layer.appendChild(group);
    });
  }

  function renderRelationshipList() {
    const container = document.querySelector("[data-relationship-list]");
    container.replaceChildren();
    state.graph.relationships.forEach((relationship) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "relationship-button";
      button.dataset.relationshipId = relationship.id;
      button.innerHTML = `<span><strong>${escapeHtml(relationshipLabel(relationship))}</strong><span>Document ${escapeHtml(relationship.evidence[0].document_id)} · lines ${relationship.evidence[0].line_start}–${relationship.evidence[0].line_end}</span></span><span class="status-badge">Supported</span>`;
      button.addEventListener("click", () => selectRelationship(relationship.id));
      container.appendChild(button);
    });
  }

  function sourceLink(evidence) {
    return evidence.source_url ? `<a class="inline-link" href="${escapeHtml(evidence.source_url)}" rel="noreferrer">Open CIA source record</a>` : "";
  }

  function relationshipDetail(relationship) {
    const source = state.entitiesById.get(relationship.source);
    const target = state.entitiesById.get(relationship.target);
    const evidence = relationship.evidence[0];
    const grounding = relationship.groundings[0];
    return `
      <div class="detail-section">
        <span class="status-badge">Supported in fixed artifact</span>
      </div>
      <div class="detail-section relationship-expression">
        <strong>${escapeHtml(source.name)}</strong>
        <span>${escapeHtml(humanize(relationship.type))} →</span>
        <strong>${escapeHtml(target.name)}</strong>
      </div>
      <div class="detail-section">
        <p class="detail-label">Exact source quote</p>
        <blockquote>${escapeHtml(evidence.quote)}</blockquote>
        <p class="detail-value">Document ${escapeHtml(evidence.document_id)}, lines ${evidence.line_start}–${evidence.line_end}</p>
        ${sourceLink(evidence)}
      </div>
      <div class="detail-section">
        <p class="detail-label">Grounded spans</p>
        <div class="grounding-grid">
          <div><span>Source mention</span><strong>${escapeHtml(grounding.source_mention)}</strong></div>
          <div><span>Relationship phrase</span><strong>${escapeHtml(grounding.relation_phrase)}</strong></div>
          <div><span>Target mention</span><strong>${escapeHtml(grounding.target_mention)}</strong></div>
        </div>
      </div>
      <div class="detail-section">
        <p class="detail-label">Extraction rationale</p>
        <p class="detail-value">${escapeHtml(grounding.support_reasoning)}</p>
      </div>`;
  }

  function entityDetail(entity) {
    const evidence = entity.evidence[0];
    const connected = state.graph.relationships.filter((relationship) => relationship.source === entity.id || relationship.target === entity.id);
    return `
      <div class="detail-section"><span class="type-badge">${escapeHtml(entity.type)}</span></div>
      <div class="detail-section">
        <p class="detail-label">Graph status</p>
        <p class="detail-value">${connected.length ? `${connected.length} accepted relationship${connected.length === 1 ? "" : "s"}` : "No accepted relationships in this checkpoint"}</p>
      </div>
      <div class="detail-section">
        <p class="detail-label">Exact source quote</p>
        <blockquote>${escapeHtml(evidence.quote)}</blockquote>
        <p class="detail-value">Document ${escapeHtml(evidence.document_id)}, lines ${evidence.line_start}–${evidence.line_end}</p>
        ${sourceLink(evidence)}
      </div>
      <div class="detail-section">
        <p class="detail-label">Canonical identifier</p>
        <p class="detail-value">${escapeHtml(entity.id)}</p>
      </div>`;
  }

  function updateSelectionClasses() {
    document.querySelectorAll("[data-relationship-id]").forEach((element) => {
      element.classList.toggle("is-selected", state.selectedKind === "relationship" && element.dataset.relationshipId === state.selectedId);
    });
    document.querySelectorAll("[data-entity-id]").forEach((element) => {
      element.classList.toggle("is-selected", state.selectedKind === "entity" && element.dataset.entityId === state.selectedId);
    });
  }

  function selectRelationship(relationshipId) {
    const relationship = state.graph.relationships.find((item) => item.id === relationshipId);
    if (!relationship) return;
    state.selectedKind = "relationship";
    state.selectedId = relationshipId;
    document.getElementById("detail-title").textContent = humanize(relationship.type);
    document.querySelector("[data-detail-content]").innerHTML = relationshipDetail(relationship);
    updateSelectionClasses();
  }

  function selectEntity(entityId) {
    const entity = state.entitiesById.get(entityId);
    if (!entity) return;
    state.selectedKind = "entity";
    state.selectedId = entityId;
    document.getElementById("detail-title").textContent = entity.name;
    document.querySelector("[data-detail-content]").innerHTML = entityDetail(entity);
    updateSelectionClasses();
    if (window.innerWidth < 980) document.querySelector(".detail-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderEntityFilters() {
    const select = document.getElementById("entity-type-filter");
    [...new Set(state.graph.entities.map((entity) => entity.type))].sort().forEach((type) => {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = humanize(type);
      select.appendChild(option);
    });
  }

  function renderEntities() {
    const query = document.getElementById("entity-search").value.trim().toLowerCase();
    const type = document.getElementById("entity-type-filter").value;
    const connectedIds = new Set(state.graph.relationships.flatMap((relationship) => [relationship.source, relationship.target]));
    const entities = state.graph.entities
      .filter((entity) => (!query || `${entity.name} ${entity.id}`.toLowerCase().includes(query)) && (!type || entity.type === type))
      .sort((a, b) => a.name.localeCompare(b.name));
    const container = document.querySelector("[data-entity-list]");
    container.replaceChildren();
    entities.forEach((entity) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "entity-button";
      button.dataset.entityId = entity.id;
      button.innerHTML = `<strong>${escapeHtml(entity.name)}</strong><span class="entity-meta"><span class="type-badge">${escapeHtml(entity.type)}</span><span class="connection-badge">${connectedIds.has(entity.id) ? "Connected" : "No accepted edge"}</span></span>`;
      button.addEventListener("click", () => selectEntity(entity.id));
      container.appendChild(button);
    });
    document.querySelector("[data-entity-result-count]").textContent = `${entities.length} of ${state.graph.entities.length} entities`;
  }

  function renderDocuments() {
    const container = document.querySelector("[data-document-list]");
    const entityCounts = new Map();
    const relationshipCounts = new Map();
    state.graph.entities.forEach((entity) => entity.evidence.forEach((evidence) => entityCounts.set(evidence.document_id, (entityCounts.get(evidence.document_id) || 0) + 1)));
    state.graph.relationships.forEach((relationship) => relationship.evidence.forEach((evidence) => relationshipCounts.set(evidence.document_id, (relationshipCounts.get(evidence.document_id) || 0) + 1)));
    container.replaceChildren();
    state.graph.documents.forEach((sourceDocument) => {
      const article = window.document.createElement("article");
      article.className = "document-card";
      article.innerHTML = `
        <span class="type-badge">Document ${escapeHtml(sourceDocument.document_id)}</span>
        <h4>${escapeHtml(sourceDocument.title)}</h4>
        <dl>
          <div><dt>Entities</dt><dd>${entityCounts.get(sourceDocument.document_id) || 0}</dd></div>
          <div><dt>Accepted edges</dt><dd>${relationshipCounts.get(sourceDocument.document_id) || 0}</dd></div>
          <div><dt>Analyzed lines</dt><dd>${sourceDocument.analyzed_lines}</dd></div>
        </dl>
        <a class="inline-link" href="${escapeHtml(sourceDocument.source_url)}" rel="noreferrer">Open CIA source record</a>`;
      container.appendChild(article);
    });
  }

  function fail(error) {
    const panel = document.getElementById("load-error");
    panel.hidden = false;
    panel.querySelector("[data-error-message]").textContent = error instanceof Error ? error.message : String(error);
    document.querySelector(".explorer-grid").hidden = true;
  }

  async function initialize() {
    try {
      const [graphResponse, buildResponse] = await Promise.all([fetch("./data/graph.json"), fetch("./data/build.json")]);
      if (!graphResponse.ok) throw new Error(`Graph request failed with HTTP ${graphResponse.status}.`);
      state.graph = requireGraph(await graphResponse.json());
      state.entitiesById = new Map(state.graph.entities.map((entity) => [entity.id, entity]));
      updateMetrics(state.graph);
      renderGraph();
      renderRelationshipList();
      renderEntityFilters();
      renderEntities();
      renderDocuments();
      selectRelationship(state.graph.relationships[0].id);
      if (buildResponse.ok) {
        const build = await buildResponse.json();
        document.querySelector("[data-build-revision]").textContent = `Deployed revision ${truncate(build.source_revision, 12)} · graph ${state.graph.schema_version}`;
      } else {
        document.querySelector("[data-build-revision]").textContent = `Graph ${state.graph.schema_version}`;
      }
    } catch (error) {
      fail(error);
    }
  }

  document.querySelectorAll("[data-view-button]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewButton)));
  document.getElementById("entity-search").addEventListener("input", renderEntities);
  document.getElementById("entity-type-filter").addEventListener("change", renderEntities);
  document.getElementById("fit-graph").addEventListener("click", () => {
    const graph = document.getElementById("relationship-graph");
    graph.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  initialize();
})();
