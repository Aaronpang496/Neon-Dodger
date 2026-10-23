import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="My Mind Map",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🧠 My Mind Map")
st.caption(
    "Select a topic to edit it. Add branches, drag topics, "
    "and download your map to keep it."
)

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: system-ui, -apple-system, sans-serif;
    color: #172033;
    background: #f8fafc;
}

button, input {
    font: inherit;
}

button {
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    padding: 9px 12px;
    background: white;
    color: #172033;
    cursor: pointer;
}

button:hover {
    background: #eef2ff;
}

button:disabled {
    opacity: 0.4;
    cursor: default;
}

button.primary {
    background: #4f46e5;
    color: white;
    border-color: #4f46e5;
}

.toolbar, .editor {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding: 10px;
    background: white;
    border-bottom: 1px solid #e2e8f0;
}

.editor label {
    font-size: 14px;
}

#topicText {
    flex: 1;
    min-width: 150px;
    max-width: 450px;
    padding: 10px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

#topicColor {
    width: 44px;
    height: 40px;
    padding: 3px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: white;
}

#board {
    width: 100%;
    height: 590px;
    display: block;
    background: #f8fafc;
    touch-action: none;
    user-select: none;
    -webkit-user-select: none;
}

.node {
    cursor: grab;
}

.node:active {
    cursor: grabbing;
}

.node text {
    pointer-events: none;
}

.help {
    padding: 10px 12px;
    font-size: 13px;
    color: #64748b;
    background: white;
}

#status {
    min-height: 25px;
    padding: 4px 12px;
    font-size: 13px;
    color: #475569;
}

@media (max-width: 600px) {
    button {
        font-size: 13px;
        padding: 8px;
    }

    #board {
        height: 530px;
    }
}
</style>
</head>

<body>

<div class="toolbar">
    <button class="primary" id="addChild">＋ Subtopic</button>
    <button id="addSibling">＋ Sibling</button>
    <button id="deleteTopic">Delete</button>
    <button id="tidy">Arrange</button>
    <button id="zoomOut">−</button>
    <button id="zoomIn">＋</button>
    <button id="fit">Fit map</button>
    <button id="save">Save map</button>
    <button id="load">Open map</button>
    <button id="svgExport">Export SVG</button>
    <button id="newMap">New map</button>
    <input id="fileInput" type="file"
           accept=".json,application/json" hidden>
</div>

<div class="editor">
    <label for="topicText">Topic</label>
    <input id="topicText" maxlength="120"
           placeholder="Write your topic">
    <label for="topicColor">Color</label>
    <input id="topicColor" type="color" value="#4f46e5">
</div>

<svg id="board" xmlns="http://www.w3.org/2000/svg"
     aria-label="Mind map canvas">
    <defs>
        <pattern id="dots" width="24" height="24"
                 patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="#dbe3ed"/>
        </pattern>
    </defs>

    <rect id="background" width="100%" height="100%"
          fill="url(#dots)"/>

    <g id="viewport">
        <g id="edges"></g>
        <g id="nodes"></g>
    </g>
</svg>

<div class="help">
    Tap a topic, then edit its text above.
    Drag a topic to move it. Drag empty space to pan.
    “Subtopic” adds a child; “Sibling” adds a topic at the same level.
    Save a JSON file before leaving.
</div>

<div id="status" role="status"></div>

<script>
"use strict";

const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";

const board = $("board");
const viewport = $("viewport");
const edgeLayer = $("edges");
const nodeLayer = $("nodes");

const NODE_W = 180;
const NODE_H = 76;
const COLORS = [
    "#4f46e5", "#0284c7", "#059669",
    "#d97706", "#db2777", "#7c3aed"
];

let topics = [];
let selectedId = null;
let nextId = 1;
let scale = 1;
let offset = {x: 0, y: 0};
let gesture = null;

function status(message) {
    $("status").textContent = message;
}

function svgElement(tag, attributes = {}) {
    const element = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attributes)) {
        element.setAttribute(key, String(value));
    }
    return element;
}

function topicById(id) {
    return topics.find(topic => topic.id === id);
}

function childrenOf(id) {
    return topics.filter(topic => topic.parent === id);
}

function selectedTopic() {
    return topicById(selectedId);
}

function applyView() {
    viewport.setAttribute(
        "transform",
        `translate(${offset.x},${offset.y}) scale(${scale})`
    );
}

function labelLines(text) {
    const characters = Array.from(text || "Untitled");
    const lines = [];

    while (characters.length && lines.length < 3) {
        lines.push(characters.splice(0, 18).join(""));
    }

    if (characters.length) {
        lines[2] = lines[2].slice(0, 16) + "…";
    }

    return lines;
}

function textColor(hex) {
    const value = hex.replace("#", "");
    const r = parseInt(value.slice(0, 2), 16);
    const g = parseInt(value.slice(2, 4), 16);
    const b = parseInt(value.slice(4, 6), 16);

    return (r * 299 + g * 587 + b * 114) / 1000 > 155
        ? "#172033"
        : "#ffffff";
}

function draw() {
    edgeLayer.replaceChildren();
    nodeLayer.replaceChildren();

    for (const topic of topics) {
        if (topic.parent === null) continue;

        const parent = topicById(topic.parent);
        if (!parent) continue;

        const direction = topic.x >= parent.x ? 1 : -1;
        const x1 = parent.x + direction * NODE_W / 2;
        const x2 = topic.x - direction * NODE_W / 2;
        const mid = (x1 + x2) / 2;

        edgeLayer.appendChild(svgElement("path", {
            d: `M ${x1} ${parent.y}
                C ${mid} ${parent.y},
                  ${mid} ${topic.y},
                  ${x2} ${topic.y}`,
            fill: "none",
            stroke: topic.color,
            "stroke-width": 3,
            opacity: 0.7
        }));
    }

    for (const topic of topics) {
        const group = svgElement("g", {
            class: "node",
            "data-id": topic.id,
            transform: `translate(${topic.x},${topic.y})`
        });

        group.appendChild(svgElement("rect", {
            x: -NODE_W / 2,
            y: -NODE_H / 2,
            width: NODE_W,
            height: NODE_H,
            rx: 15,
            fill: topic.color,
            stroke: topic.id === selectedId ? "#0f172a" : "#ffffff",
            "stroke-width": topic.id === selectedId ? 4 : 2
        }));

        const lines = labelLines(topic.text);
        const text = svgElement("text", {
            "text-anchor": "middle",
            fill: textColor(topic.color),
            "font-family": "system-ui, sans-serif",
            "font-size": 15,
            "font-weight": 600
        });

        lines.forEach((line, index) => {
            const span = svgElement("tspan", {
                x: 0,
                y: (index - (lines.length - 1) / 2) * 18 + 5
            });

            span.textContent = line;
            text.appendChild(span);
        });

        const title = svgElement("title");
        title.textContent = topic.text;
        group.append(title, text);
        nodeLayer.appendChild(group);
    }

    applyView();
}

function updateEditor() {
    const topic = selectedTopic();

    $("topicText").value = topic ? topic.text : "";
    $("topicColor").value = topic ? topic.color : "#4f46e5";

    const isRoot = !topic || topic.parent === null;
    $("deleteTopic").disabled = isRoot;
    $("addSibling").disabled = isRoot;
}

function select(id) {
    selectedId = id;
    updateEditor();
    draw();
}

function fitMap() {
    if (!topics.length) return;

    const width = board.clientWidth;
    const height = board.clientHeight;

    const minX = Math.min(...topics.map(t => t.x)) - NODE_W / 2 - 35;
    const maxX = Math.max(...topics.map(t => t.x)) + NODE_W / 2 + 35;
    const minY = Math.min(...topics.map(t => t.y)) - NODE_H / 2 - 35;
    const maxY = Math.max(...topics.map(t => t.y)) + NODE_H / 2 + 35;

    scale = Math.max(
        0.05,
        Math.min(1.3, width / (maxX - minX), height / (maxY - minY))
    );

    offset = {
        x: width / 2 - ((minX + maxX) / 2) * scale,
        y: height / 2 - ((minY + maxY) / 2) * scale
    };

    applyView();
}

function resetMap() {
    topics = [{
        id: "n0",
        parent: null,
        text: "Central Topic",
        color: "#4f46e5",
        x: 0,
        y: 0
    }];

    nextId = 1;
    selectedId = "n0";
    updateEditor();
    draw();
    fitMap();
    status("Blank map ready. Rename the central topic to begin.");
}

function newId() {
    let id;
    do {
        id = "n" + nextId++;
    } while (topicById(id));
    return id;
}

function addTopic(parentId) {
    if (topics.length >= 500) {
        status("This starter app supports up to 500 topics.");
        return;
    }

    const parent = topicById(parentId);
    if (!parent) return;

    const siblings = childrenOf(parentId);
    const root = topics.find(t => t.parent === null);

    let direction = parent.x < root.x ? -1 : 1;
    if (parent.parent === null) {
        direction = siblings.length % 2 === 0 ? 1 : -1;
    }

    const id = newId();
    const color = parent.parent === null
        ? COLORS[siblings.length % COLORS.length]
        : parent.color;

    topics.push({
        id,
        parent: parentId,
        text: "New Topic",
        color,
        x: parent.x + direction * 250,
        y: parent.y + Math.floor(siblings.length / 2) * 110
    });

    select(id);
    $("topicText").focus();
    $("topicText").select();
    status("New topic added. Type its name above.");
}

function descendants(id) {
    const result = new Set([id]);
    const queue = [id];

    for (let i = 0; i < queue.length; i++) {
        for (const child of childrenOf(queue[i])) {
            result.add(child.id);
            queue.push(child.id);
        }
    }

    return result;
}

function arrangeMap() {
    const root = topics.find(t => t.parent === null);
    root.x = 0;
    root.y = 0;

    const spans = new Map();

    function measure(topic) {
        const children = childrenOf(topic.id);
        const span = Math.max(
            110,
            children.reduce((sum, child) => sum + measure(child), 0)
        );
        spans.set(topic.id, span);
        return span;
    }

    measure(root);

    function place(topic, depth, direction, top) {
        topic.x = direction * depth * 250;
        topic.y = top + spans.get(topic.id) / 2;

        let cursor = top;
        for (const child of childrenOf(topic.id)) {
            place(child, depth + 1, direction, cursor);
            cursor += spans.get(child.id);
        }
    }

    const firstLevel = childrenOf(root.id);
    const right = firstLevel.filter((_, index) => index % 2 === 0);
    const left = firstLevel.filter((_, index) => index % 2 === 1);

    for (const [group, direction] of [[right, 1], [left, -1]]) {
        const total = group.reduce(
            (sum, child) => sum + spans.get(child.id), 0
        );

        let cursor = -total / 2;
        for (const child of group) {
            place(child, 1, direction, cursor);
            cursor += spans.get(child.id);
        }
    }

    draw();
    fitMap();
    status("Topics arranged.");
}

function zoom(factor) {
    const oldScale = scale;
    scale = Math.max(0.05, Math.min(3, scale * factor));

    const cx = board.clientWidth / 2;
    const cy = board.clientHeight / 2;
    const ratio = scale / oldScale;

    offset.x = cx - (cx - offset.x) * ratio;
    offset.y = cy - (cy - offset.y) * ratio;
    applyView();
}

function download(contents, filename, type) {
    const blob = new Blob([contents], {type});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
}

function validateMap(data) {
    if (!data || !Array.isArray(data.topics)) {
        throw new Error("This is not a mind-map JSON file.");
    }

    if (data.topics.length < 1 || data.topics.length > 500) {
        throw new Error("A map must contain 1–500 topics.");
    }

    const clean = data.topics.map(t => {
        if (
            !t || typeof t.id !== "string" ||
            t.id.length > 100 ||
            !(t.parent === null || typeof t.parent === "string") ||
            typeof t.text !== "string" ||
            t.text.length > 120 ||
            typeof t.color !== "string" ||
            !/^#[0-9a-f]{6}$/i.test(t.color) ||
            !Number.isFinite(t.x) || !Number.isFinite(t.y) ||
            Math.abs(t.x) > 1000000 || Math.abs(t.y) > 1000000
        ) {
            throw new Error("The file contains an invalid topic.");
        }

        return {
            id: t.id,
            parent: t.parent,
            text: t.text,
            color: t.color,
            x: t.x,
            y: t.y
        };
    });

    const ids = new Set(clean.map(t => t.id));
    if (ids.size !== clean.length) {
        throw new Error("Topic IDs must be unique.");
    }

    if (clean.filter(t => t.parent === null).length !== 1) {
        throw new Error("The map must have exactly one central topic.");
    }

    const byId = new Map(clean.map(t => [t.id, t]));

    for (const topic of clean) {
        const visited = new Set();
        let current = topic;

        while (current !== undefined) {
            if (visited.has(current.id)) {
                throw new Error("The map contains a circular branch.");
            }

            visited.add(current.id);
            if (current.parent === null) break;

            if (!byId.has(current.parent)) {
                throw new Error("A topic refers to a missing parent.");
            }

            current = byId.get(current.parent);
        }
    }

    return clean;
}

$("topicText").addEventListener("input", event => {
    const topic = selectedTopic();
    if (!topic) return;
    topic.text = event.target.value;
    draw();
});

$("topicColor").addEventListener("input", event => {
    const topic = selectedTopic();
    if (!topic) return;
    topic.color = event.target.value;
    draw();
});

$("addChild").onclick = () => {
    const topic = selectedTopic();
    if (topic) addTopic(topic.id);
};

$("addSibling").onclick = () => {
    const topic = selectedTopic();
    if (topic && topic.parent !== null) addTopic(topic.parent);
};

$("deleteTopic").onclick = () => {
    const topic = selectedTopic();
    if (!topic || topic.parent === null) return;

    const removed = descendants(topic.id);
    if (!confirm(`Delete this topic and its subtopics (${removed.size} total)?`)) {
        return;
    }

    const parentId = topic.parent;
    topics = topics.filter(t => !removed.has(t.id));
    select(parentId);
    status("Topic deleted.");
};

$("tidy").onclick = arrangeMap;
$("fit").onclick = fitMap;
$("zoomIn").onclick = () => zoom(1.2);
$("zoomOut").onclick = () => zoom(1 / 1.2);

$("newMap").onclick = () => {
    if (confirm("Start a blank map? Save your current map first.")) {
        resetMap();
    }
};

$("save").onclick = () => {
    download(
        JSON.stringify({version: 1, topics}, null, 2),
        "mind-map.json",
        "application/json"
    );
    status("Map download requested. Keep the JSON file to reopen it later.");
};

$("load").onclick = () => $("fileInput").click();

$("fileInput").addEventListener("change", async event => {
    const file = event.target.files[0];
    if (!file) return;

    try {
        if (file.size > 2000000) {
            throw new Error("Please choose a JSON file smaller than 2 MB.");
        }

        const clean = validateMap(JSON.parse(await file.text()));

        if (!confirm("Replace the current map with this file?")) return;

        topics = clean;
        selectedId = topics.find(t => t.parent === null).id;
        nextId = 1;

        updateEditor();
        draw();
        fitMap();
        status("Map opened.");
    } catch (error) {
        status("Could not open map: " + error.message);
    } finally {
        event.target.value = "";
    }
});

$("svgExport").onclick = () => {
    const minX = Math.min(...topics.map(t => t.x)) - NODE_W / 2 - 30;
    const maxX = Math.max(...topics.map(t => t.x)) + NODE_W / 2 + 30;
    const minY = Math.min(...topics.map(t => t.y)) - NODE_H / 2 - 30;
    const maxY = Math.max(...topics.map(t => t.y)) + NODE_H / 2 + 30;

    const output = svgElement("svg", {
        xmlns: NS,
        viewBox: `${minX} ${minY} ${maxX - minX} ${maxY - minY}`,
        width: maxX - minX,
        height: maxY - minY
    });

    output.appendChild(svgElement("rect", {
        x: minX, y: minY,
        width: maxX - minX,
        height: maxY - minY,
        fill: "#ffffff"
    }));

    output.append(
        edgeLayer.cloneNode(true),
        nodeLayer.cloneNode(true)
    );

    download(
        new XMLSerializer().serializeToString(output),
        "mind-map.svg",
        "image/svg+xml"
    );

    status("SVG download requested.");
});

board.addEventListener("pointerdown", event => {
    if (gesture || (event.pointerType === "mouse" && event.button !== 0)) {
        return;
    }

    const node = event.target.closest(".node");
    const id = node ? node.getAttribute("data-id") : null;

    if (id) select(id);

    const topic = id ? topicById(id) : null;

    gesture = {
        pointerId: event.pointerId,
        id,
        startX: event.clientX,
        startY: event.clientY,
        topicX: topic ? topic.x : 0,
        topicY: topic ? topic.y : 0,
        offsetX: offset.x,
        offsetY: offset.y
    };

    board.setPointerCapture(event.pointerId);
    event.preventDefault();
});

board.addEventListener("pointermove", event => {
    if (!gesture || event.pointerId !== gesture.pointerId) return;

    const dx = event.clientX - gesture.startX;
    const dy = event.clientY - gesture.startY;

    if (gesture.id) {
        const topic = topicById(gesture.id);
        topic.x = gesture.topicX + dx / scale;
        topic.y = gesture.topicY + dy / scale;
        draw();
    } else {
        offset.x = gesture.offsetX + dx;
        offset.y = gesture.offsetY + dy;
        applyView();
    }
});

function endGesture(event) {
    if (gesture && gesture.pointerId === event.pointerId) {
        gesture = null;
    }
}

board.addEventListener("pointerup", endGesture);
board.addEventListener("pointercancel", endGesture);
board.addEventListener("lostpointercapture", endGesture);

window.addEventListener("resize", fitMap);

resetMap();
</script>
</body>
</html>
"""

components.html(HTML, height=850, scrolling=True)

st.info(
    "Your map is edited inside your browser. "
    "Use Save map to download a JSON backup before refreshing "
    "or closing the app. Open map restores that file. "
    "This starter does not save maps to a server."
)
