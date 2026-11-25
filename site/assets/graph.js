(() => {
  "use strict";

  const workspace = document.getElementById("graph-workspace");
  if (!workspace) return;

  const ui = {
    workspace,
    canvas: document.getElementById("graph-canvas"),
    controls: document.getElementById("graph-view-controls"),
    status: document.getElementById("graph-status"),
    list: document.getElementById("graph-list"),
    inspector: document.getElementById("graph-inspector"),
    search: document.getElementById("graph-search"),
    kind: document.getElementById("graph-kind"),
    isolated: document.getElementById("graph-show-isolated"),
    reset: document.getElementById("graph-reset"),
  };
  if (Object.values(ui).some((element) => !element)) return;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const viewButtons = [...document.querySelectorAll("[data-graph-view]")];
  const focusLinks = [...document.querySelectorAll("[data-node-focus]")];
  let graph = null;
  let nodeById = new Map();
  let selectedId = "";
  let view = "list";

  function svgElement(tag, attributes = {}, content = "") {
    const element = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attributes)) {
      element.setAttribute(name, String(value));
    }
    if (content) element.textContent = content;
    return element;
  }

  function htmlElement(tag, className = "", content = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content) element.textContent = content;
    return element;
  }

  function setStatus(message = "") {
    ui.status.textContent = message;
    ui.status.hidden = !message;
  }

  function nodeAnchor(nodeId) {
    return `#node-${encodeURIComponent(nodeId)}`;
  }

  function idFromHash() {
    let anchor = "";
    try {
      anchor = decodeURIComponent(window.location.hash.slice(1));
    } catch (_error) {
      return "";
    }
    if (!anchor.startsWith("node-")) return "";
    const nodeId = anchor.slice(5);
    return nodeById.has(nodeId) ? nodeId : "";
  }

  function replaceHash(nodeId = "") {
    const next = nodeId ? nodeAnchor(nodeId) : `${window.location.pathname}${window.location.search}`;
    window.history.replaceState(null, "", next);
  }

  function filteredEdges() {
    const kind = ui.kind.value;
    return graph.edges.filter((edge) => kind === "all" || edge.kind === kind);
  }

  function currentSelection() {
    const edges = filteredEdges();
    const query = ui.search.value.trim().toLocaleLowerCase();
    const activeIds = new Set(edges.flatMap((edge) => [edge.source, edge.target]));
    const matches = new Set(
      graph.nodes
        .filter((node) => {
          if (!query) return false;
          return `${node.编号} ${node.id} ${node.title || node.标题}`.toLocaleLowerCase().includes(query);
        })
        .map((node) => node.id),
    );

    let visibleIds;
    if (query) {
      visibleIds = new Set(matches);
      for (const edge of edges) {
        if (matches.has(edge.source) || matches.has(edge.target)) {
          visibleIds.add(edge.source);
          visibleIds.add(edge.target);
        }
      }
    } else {
      visibleIds = ui.isolated.checked ? new Set(nodeById.keys()) : new Set(activeIds);
    }

    const visibleNodes = graph.nodes.filter((node) => visibleIds.has(node.id));
    const visibleEdges = edges.filter((edge) => {
      if (!visibleIds.has(edge.source) || !visibleIds.has(edge.target)) return false;
      return !query || matches.has(edge.source) || matches.has(edge.target);
    });
    return { visibleNodes, visibleEdges, matches, query, totalEdges: edges.length };
  }

  function connectedGroups(nodes, edges) {
    const ids = new Set(nodes.map((node) => node.id));
    const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
    for (const edge of edges) {
      if (!ids.has(edge.source) || !ids.has(edge.target)) continue;
      adjacency.get(edge.source).add(edge.target);
      adjacency.get(edge.target).add(edge.source);
    }
    const visited = new Set();
    const connected = [];
    const singles = [];
    for (const node of nodes) {
      if (visited.has(node.id)) continue;
      const stack = [node.id];
      const members = [];
      visited.add(node.id);
      while (stack.length) {
        const current = stack.pop();
        members.push(current);
        for (const next of adjacency.get(current) || []) {
          if (!visited.has(next)) {
            visited.add(next);
            stack.push(next);
          }
        }
      }
      if (members.length === 1 && adjacency.get(members[0]).size === 0) {
        singles.push(members[0]);
      } else {
        connected.push(members);
      }
    }
    const order = new Map(nodes.map((node, index) => [node.id, index]));
    const byPageOrder = (left, right) => order.get(left) - order.get(right);
    const groups = connected.map((members) => ({
      members: members.sort(byPageOrder),
      isolated: false,
    }));
    if (singles.length) groups.push({ members: singles.sort(byPageOrder), isolated: true });
    groups.sort((left, right) => {
      if (left.isolated !== right.isolated) return left.isolated ? 1 : -1;
      if (left.members.length !== right.members.length) return right.members.length - left.members.length;
      return order.get(left.members[0]) - order.get(right.members[0]);
    });
    return groups;
  }

  function gridPositions(members, frame) {
    const positions = new Map();
    const inner = innerFrame(frame);
    const columns = Math.max(1, Math.ceil(Math.sqrt(members.length * inner.width / inner.height)));
    const rows = Math.max(1, Math.ceil(members.length / columns));
    members.forEach((nodeId, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      positions.set(nodeId, {
        x: inner.x + (column + 0.5) * inner.width / columns,
        y: inner.y + (row + 0.5) * inner.height / rows,
      });
    });
    return positions;
  }

  function innerFrame(frame) {
    return {
      x: frame.x + 34,
      y: frame.y + 58,
      width: Math.max(80, frame.width - 68),
      height: Math.max(80, frame.height - 92),
    };
  }

  function forcePositions(members, edges, frame) {
    const inner = innerFrame(frame);
    const center = { x: inner.x + inner.width / 2, y: inner.y + inner.height / 2 };
    const positions = gridPositions(members, frame);
    const memberSet = new Set(members);
    if (members.length <= 4) return positions;

    const localEdges = edges.filter((edge) => memberSet.has(edge.source) && memberSet.has(edge.target));
    const desired = Math.max(126, Math.min(178, Math.min(inner.width, inner.height) / Math.sqrt(members.length) * 1.2));
    const clampPoint = (point) => {
      point.x = Math.max(inner.x + 54, Math.min(inner.x + inner.width - 54, point.x));
      point.y = Math.max(inner.y + 26, Math.min(inner.y + inner.height - 64, point.y));
    };
    const separateLabels = () => {
      for (let left = 0; left < members.length; left += 1) {
        for (let right = left + 1; right < members.length; right += 1) {
          const a = positions.get(members[left]);
          const b = positions.get(members[right]);
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const overlapX = 126 - Math.abs(dx);
          const overlapY = 100 - Math.abs(dy);
          if (overlapX <= 0 || overlapY <= 0) continue;
          if (overlapX < overlapY) {
            const direction = dx === 0 ? (left < right ? -1 : 1) : Math.sign(dx);
            const shift = overlapX / 2 + 0.5;
            a.x += direction * shift;
            b.x -= direction * shift;
          } else {
            const direction = dy === 0 ? (left < right ? -1 : 1) : Math.sign(dy);
            const shift = overlapY / 2 + 0.5;
            a.y += direction * shift;
            b.y -= direction * shift;
          }
          clampPoint(a);
          clampPoint(b);
        }
      }
    };

    const iterations = members.length <= 4 ? 80 : 220;
    for (let iteration = 0; iteration < iterations; iteration += 1) {
      const forces = new Map(members.map((nodeId) => [nodeId, { x: 0, y: 0 }]));
      for (let left = 0; left < members.length; left += 1) {
        for (let right = left + 1; right < members.length; right += 1) {
          const a = positions.get(members[left]);
          const b = positions.get(members[right]);
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let distance = Math.hypot(dx, dy);
          if (distance < 0.01) {
            const angle = (left + 1) * (right + 2) * 0.61803398875;
            dx = Math.cos(angle);
            dy = Math.sin(angle);
            distance = 1;
          }
          const repulsion = Math.min(3, 2400 / (distance * distance));
          const fx = dx / distance * repulsion;
          const fy = dy / distance * repulsion;
          forces.get(members[left]).x += fx;
          forces.get(members[left]).y += fy;
          forces.get(members[right]).x -= fx;
          forces.get(members[right]).y -= fy;
        }
      }
      for (const edge of localEdges) {
        const a = positions.get(edge.source);
        const b = positions.get(edge.target);
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const spring = (distance - desired) * 0.008;
        const fx = dx / distance * spring;
        const fy = dy / distance * spring;
        forces.get(edge.source).x += fx;
        forces.get(edge.source).y += fy;
        forces.get(edge.target).x -= fx;
        forces.get(edge.target).y -= fy;
      }
      const cooling = 0.2 + 0.8 * (1 - iteration / iterations);
      for (const nodeId of members) {
        const point = positions.get(nodeId);
        const force = forces.get(nodeId);
        force.x += (center.x - point.x) * 0.004;
        force.y += (center.y - point.y) * 0.004;
        point.x += Math.max(-5, Math.min(5, force.x)) * cooling;
        point.y += Math.max(-5, Math.min(5, force.y)) * cooling;
        clampPoint(point);
      }
      separateLabels();
    }
    for (let pass = 0; pass < 16; pass += 1) separateLabels();
    for (const nodeId of members) clampPoint(positions.get(nodeId));
    return positions;
  }

  function layoutGraph(nodes, edges) {
    const groups = connectedGroups(nodes, edges);
    const maxWidth = 1200;
    const gap = 24;
    const frames = [];
    let shelf = [];
    let shelfWidth = 0;
    let y = 12;

    function flushShelf() {
      if (!shelf.length) return;
      const height = Math.max(...shelf.map((frame) => frame.height));
      const offset = Math.max(12, (maxWidth - shelfWidth) / 2);
      shelf.forEach((frame, index) => {
        frame.x = offset + index * 0 + shelf.slice(0, index).reduce((sum, item) => sum + item.width + gap, 0);
        frame.y = y;
        frame.height = height;
        frames.push(frame);
      });
      y += height + gap;
      shelf = [];
      shelfWidth = 0;
    }

    for (const group of groups) {
      const count = group.members.length;
      const columns = count <= 4
        ? Math.ceil(Math.sqrt(count))
        : Math.ceil(Math.sqrt(count * 1.35));
      const rows = Math.ceil(count / columns);
      const columnWidth = group.isolated ? 142 : 150;
      const rowHeight = group.isolated ? 122 : 140;
      const width = Math.max(300, columns * columnWidth + 68);
      const height = Math.max(240, rows * rowHeight + 100);
      const frame = { group, width, height, x: 0, y: 0 };
      const nextWidth = shelfWidth + (shelf.length ? gap : 0) + width;
      if (shelf.length && nextWidth > maxWidth - 24) flushShelf();
      shelf.push(frame);
      shelfWidth += (shelf.length > 1 ? gap : 0) + width;
    }
    flushShelf();

    const positions = new Map();
    const frameData = [];
    for (const frame of frames) {
      const group = frame.group;
      const localPositions = group.isolated
        ? gridPositions(group.members, frame)
        : forcePositions(group.members, edges, frame);
      for (const [nodeId, point] of localPositions) positions.set(nodeId, point);
      const first = nodeById.get(group.members[0]);
      frameData.push({
        ...frame,
        label: group.isolated
          ? `当前视图无连接 · ${group.members.length} 个节点`
          : `关系簇 · 起于 #${first.编号} · ${group.members.length} 个节点`,
      });
    }
    return { positions, frames: frameData, width: maxWidth, height: Math.max(320, y + 4) };
  }

  function labelLines(value) {
    const characters = Array.from(value || "未命名节点");
    const lines = [characters.slice(0, 7).join("")];
    if (characters.length > 7) {
      lines.push(`${characters.slice(7, characters.length > 14 ? 13 : 14).join("")}${characters.length > 14 ? "…" : ""}`);
    }
    return lines;
  }

  function renderInspector() {
    ui.inspector.replaceChildren();
    ui.inspector.append(htmlElement("p", "kicker", "Node inspector"));
    const node = nodeById.get(selectedId);
    if (!node) {
      ui.inspector.append(
        htmlElement("h2", "", "选择一个节点"),
        htmlElement("p", "", "在图中选择节点，查看完整名称、状态与双端关系说明。也可使用键盘 Tab 移动焦点，Enter 或空格选择。"),
      );
      return;
    }
    const title = htmlElement("h2", "", node.标题);
    title.id = "graph-inspector-title";
    const detailLink = htmlElement("a", "graph-detail-link", "阅读完整档案 →");
    detailLink.href = node.页面;
    ui.inspector.append(
      title,
      htmlElement("p", "record-id", `#${node.编号} · ${node.id}`),
      htmlElement("p", "graph-inspector-meta", `${node.领域} · ${node.档案类型} · ${node.复活状态}`),
      detailLink,
    );
    const relatedEdges = graph.edges.filter((edge) => edge.source === node.id || edge.target === node.id);
    ui.inspector.append(htmlElement("h3", "", `显式关系 · ${relatedEdges.length} 对`));
    if (!relatedEdges.length) {
      ui.inspector.append(htmlElement("p", "graph-no-relations", "该节点暂无显式关系，保留为孤立档案。"));
      return;
    }
    const list = htmlElement("ul", "relations-list graph-inspector-relations");
    for (const edge of relatedEdges) {
      const otherId = edge.source === node.id ? edge.target : edge.source;
      const other = nodeById.get(otherId);
      const item = htmlElement("li");
      const heading = htmlElement(
        "p",
        "relation-type",
        edge.directed
          ? `直接派生：#${nodeById.get(edge.source).编号} → #${nodeById.get(edge.target).编号}`
          : `一般相关：#${node.编号} ↔ #${other.编号}`,
      );
      const otherLink = htmlElement("a", "", `#${other.编号} · ${other.标题}`);
      otherLink.href = other.页面;
      item.append(heading, otherLink);
      for (const declaration of edge.declarations) {
        item.append(htmlElement(
          "p",
          "graph-declaration",
          `#${nodeById.get(declaration.来源).编号} 对 #${nodeById.get(declaration.目标).编号}：${declaration.关系}`,
        ));
        if (declaration.说明) item.append(htmlElement("p", "relation-note", declaration.说明));
      }
      list.append(item);
    }
    ui.inspector.append(list);
  }

  function focusGraphNode(nodeId) {
    const target = ui.canvas.querySelector(`[data-node-id="${CSS.escape(nodeId)}"]`);
    if (!target) return;
    target.focus({ preventScroll: true });
    target.scrollIntoView({ block: "center", inline: "center" });
  }

  function selectNode(nodeId, { updateHash = true, focusGraph = false } = {}) {
    if (!nodeById.has(nodeId)) return;
    selectedId = nodeId;
    if (updateHash) replaceHash(nodeId);
    setView("graph", false);
    if (focusGraph) focusGraphNode(nodeId);
  }

  function renderGraph() {
    if (!graph || view !== "graph") return;
    const selection = currentSelection();
    if (selectedId && !selection.visibleNodes.some((node) => node.id === selectedId)) {
      selectedId = "";
      replaceHash();
    }
    const { visibleNodes, visibleEdges, matches, query, totalEdges } = selection;
    ui.canvas.replaceChildren();
    if (!visibleNodes.length) {
      setStatus(query ? "没有匹配当前条件的节点。完整列表仍可查看全部正式档案。" : "当前筛选没有可显示的连接节点。");
      renderInspector();
      return;
    }

    const layout = layoutGraph(visibleNodes, visibleEdges);
    const svg = svgElement("svg", {
      class: "graph-svg",
      viewBox: `0 0 ${layout.width} ${layout.height}`,
      role: "group",
      "aria-label": `科技树关系图，显示 ${visibleNodes.length} 个节点和 ${visibleEdges.length} 对关系`,
    });
    svg.append(
      svgElement("title", {}, "idea-tree 科技树关系图"),
      svgElement("desc", {}, "金色实线箭头表示直接派生，青色虚线表示一般相关。所有节点另有完整文字列表。"),
    );
    const defs = svgElement("defs");
    const marker = svgElement("marker", {
      id: "graph-arrow",
      viewBox: "0 0 10 10",
      refX: 9,
      refY: 5,
      markerWidth: 8,
      markerHeight: 8,
      markerUnits: "userSpaceOnUse",
      orient: "auto-start-reverse",
    });
    marker.append(svgElement("path", { d: "M 0 0 L 10 5 L 0 10 z", class: "graph-arrow" }));
    defs.append(marker);
    svg.append(defs);

    const frameLayer = svgElement("g", { "aria-hidden": "true", class: "graph-frames" });
    for (const frame of layout.frames) {
      frameLayer.append(
        svgElement("rect", {
          x: frame.x,
          y: frame.y,
          width: frame.width,
          height: frame.height,
          class: `graph-component-frame${frame.group.isolated ? " isolated" : ""}`,
        }),
        svgElement("text", { x: frame.x + 18, y: frame.y + 28, class: "graph-component-label" }, frame.label),
      );
    }
    svg.append(frameLayer);

    const neighbors = new Set();
    if (selectedId) {
      for (const edge of visibleEdges) {
        if (edge.source === selectedId) neighbors.add(edge.target);
        if (edge.target === selectedId) neighbors.add(edge.source);
      }
    }
    const edgeLayer = svgElement("g", { "aria-hidden": "true" });
    for (const edge of visibleEdges) {
      const source = layout.positions.get(edge.source);
      const target = layout.positions.get(edge.target);
      if (!source || !target) continue;
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const sourceGap = 29;
      const targetGap = edge.directed ? 37 : 29;
      const active = selectedId && (edge.source === selectedId || edge.target === selectedId);
      const classes = ["graph-edge", edge.kind];
      if (active) classes.push("is-active");
      if (selectedId && !active) classes.push("is-dimmed");
      const line = svgElement("line", {
        x1: source.x + dx / distance * sourceGap,
        y1: source.y + dy / distance * sourceGap,
        x2: target.x - dx / distance * targetGap,
        y2: target.y - dy / distance * targetGap,
        class: classes.join(" "),
        "data-edge-id": edge.id,
      });
      if (edge.directed) line.setAttribute("marker-end", "url(#graph-arrow)");
      edgeLayer.append(line);
    }
    svg.append(edgeLayer);

    const nodeLayer = svgElement("g");
    for (const node of visibleNodes) {
      const point = layout.positions.get(node.id);
      if (!point) continue;
      const classes = ["graph-node"];
      if (node.id === selectedId) classes.push("is-selected");
      if (neighbors.has(node.id)) classes.push("is-neighbor");
      if (selectedId && node.id !== selectedId && !neighbors.has(node.id)) classes.push("is-dimmed");
      if (matches.has(node.id)) classes.push("is-search-match");
      if (query && !matches.has(node.id)) classes.push("is-context");
      const link = svgElement("a", {
        href: nodeAnchor(node.id),
        class: classes.join(" "),
        tabindex: "0",
        role: "button",
        "aria-pressed": node.id === selectedId ? "true" : "false",
        "aria-label": `#${node.编号}，${node.标题}，${node.连接数} 对关系。按 Enter 或空格聚焦。`,
        "data-node-id": node.id,
        transform: `translate(${point.x} ${point.y})`,
      });
      const label = svgElement("text", { y: 40, class: "graph-node-label", "aria-hidden": "true" });
      labelLines(node.标题).forEach((line, index) => {
        label.append(svgElement("tspan", { x: 0, dy: index === 0 ? 0 : 18 }, line));
      });
      link.append(
        svgElement("title", {}, `#${node.编号} · ${node.标题}`),
        svgElement("circle", { r: 32, class: "graph-node-hit", "aria-hidden": "true" }),
        svgElement("circle", { r: 20, class: "graph-node-circle", "aria-hidden": "true" }),
        svgElement("text", { y: 4, class: "graph-node-number", "aria-hidden": "true" }, node.编号),
        label,
      );
      link.addEventListener("click", (event) => {
        event.preventDefault();
        selectNode(node.id);
      });
      link.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectNode(node.id);
        }
      });
      nodeLayer.append(link);
    }
    svg.append(nodeLayer);
    ui.canvas.append(svg);
    const matchText = query ? `；${matches.size} 个搜索匹配，相邻节点一并保留` : "";
    setStatus(`显示 ${visibleNodes.length} / ${graph.nodes.length} 个节点，${visibleEdges.length} / ${totalEdges} 对当前类型关系${matchText}。`);
    renderInspector();
  }

  function setView(nextView, resetStatus = true) {
    view = nextView === "graph" ? "graph" : "list";
    ui.workspace.hidden = view !== "graph";
    ui.list.hidden = view !== "list";
    for (const button of viewButtons) {
      button.setAttribute("aria-pressed", button.dataset.graphView === view ? "true" : "false");
    }
    if (resetStatus) setStatus();
    if (view === "graph") renderGraph();
  }

  function clearFilters() {
    ui.search.value = "";
    ui.kind.value = "all";
    ui.isolated.checked = false;
    selectedId = "";
    replaceHash();
    setView("graph");
  }

  function initialise(payload) {
    if (!payload || !Array.isArray(payload.nodes) || !Array.isArray(payload.edges)) {
      throw new Error("invalid graph payload");
    }
    const ids = payload.nodes.map((node) => node && node.id);
    if (ids.some((id) => typeof id !== "string" || !id) || new Set(ids).size !== ids.length) {
      throw new Error("invalid graph nodes");
    }
    graph = payload;
    nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
    for (const edge of graph.edges) {
      if (!nodeById.has(edge.source) || !nodeById.has(edge.target)) throw new Error("invalid graph edge");
    }

    ui.controls.hidden = false;
    focusLinks.forEach((link) => { link.hidden = false; });
    viewButtons.forEach((button) => {
      button.addEventListener("click", () => setView(button.dataset.graphView));
    });
    focusLinks.forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        selectNode(link.dataset.nodeFocus, { focusGraph: true });
      });
    });
    ui.search.addEventListener("input", () => {
      selectedId = "";
      replaceHash();
      renderGraph();
    });
    ui.kind.addEventListener("change", () => {
      selectedId = "";
      replaceHash();
      renderGraph();
    });
    ui.isolated.addEventListener("change", () => {
      selectedId = "";
      replaceHash();
      renderGraph();
    });
    ui.reset.addEventListener("click", clearFilters);
    window.addEventListener("hashchange", () => {
      selectedId = idFromHash();
      if (selectedId) {
        setView("graph");
        focusGraphNode(selectedId);
      } else {
        renderGraph();
        renderInspector();
      }
    });

    selectedId = idFromHash();
    const desktop = window.matchMedia("(min-width: 900px)").matches;
    setView(selectedId || desktop ? "graph" : "list");
    if (selectedId) focusGraphNode(selectedId);
  }

  fetch("data/graph.json", { headers: { Accept: "application/json" } })
    .then((response) => {
      if (!response.ok) throw new Error(`graph data HTTP ${response.status}`);
      return response.json();
    })
    .then(initialise)
    .catch(() => {
      selectedId = "";
      ui.workspace.hidden = true;
      ui.controls.hidden = true;
      ui.list.hidden = false;
      focusLinks.forEach((link) => { link.hidden = true; });
      setStatus("图形数据未能加载。以下完整静态关系列表仍可使用；请稍后重试或检查部署资源。");
    });
})();
