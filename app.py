import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Neon Dodger",
    page_icon="🚀",
    layout="centered",
)

st.title("🚀 Neon Dodger")
st.caption(
    "Drag inside the arena to move. Dodge red meteors, "
    "collect gold stars, and grab blue shields."
)

components.html(
    r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    color: #e2e8f0;
    background: #070b18;
    font-family: system-ui, sans-serif;
}

.wrap {
    max-width: 480px;
    margin: auto;
    padding: 10px;
}

.hud {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    padding: 12px 4px;
    font-size: 14px;
    font-weight: 700;
}

canvas {
    display: block;
    width: 100%;
    height: auto;
    background: #080d21;
    border: 2px solid #334155;
    border-radius: 16px;
    touch-action: none;
    user-select: none;
    -webkit-user-select: none;
}

.controls {
    display: flex;
    gap: 10px;
    margin-top: 12px;
}

button {
    flex: 1;
    padding: 13px;
    border: 0;
    border-radius: 12px;
    background: #22d3ee;
    color: #07111f;
    font-size: 16px;
    font-weight: 800;
    cursor: pointer;
}

#pause { background: #c4b5fd; }

p {
    color: #94a3b8;
    font-size: 13px;
    line-height: 1.5;
}
</style>
</head>
<body>
<div class="wrap">
    <div class="hud">
        <span id="score">Score: 0</span>
        <span id="level">Level: 1</span>
        <span id="shield">Shield: OFF</span>
    </div>

    <canvas id="game" width="480" height="600"
            tabindex="0" aria-label="Neon Dodger game arena"></canvas>

    <div class="controls">
        <button id="start">Start game</button>
        <button id="pause">Pause</button>
    </div>

    <p>
        iPad: drag anywhere inside the arena.
        Computer: drag with your mouse or use arrow keys.<br>
        Gold star: +100 points · Blue orb: one-hit shield.<br>
        High score: <strong id="best">0</strong>
    </p>
</div>

<script>
"use strict";

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const el = id => document.getElementById(id);
const W = 480, H = 600;

let state = "ready";
let ship, objects, particles;
let elapsed = 0, bonus = 0, score = 0;
let meteorTimer = 0, pickupTimer = 0;
let invincible = 0, shake = 0;
let best = 0;
let pointerId = null;
let previousPointer = null;
const keys = new Set();

try {
    best = Number(localStorage.getItem("neon-dodger-best")) || 0;
} catch (_) {}
el("best").textContent = best;

const stars = Array.from({length: 65}, () => ({
    x: Math.random() * W,
    y: Math.random() * H,
    r: Math.random() * 1.8 + 0.4,
    speed: Math.random() * 50 + 20
}));

function reset() {
    ship = {x: W / 2, y: H - 90, r: 14, shield: false};
    objects = [];
    particles = [];
    elapsed = bonus = score = 0;
    meteorTimer = 0.6;
    pickupTimer = 1.8;
    invincible = shake = 0;
    pointerId = null;
    previousPointer = null;
    keys.clear();
    state = "playing";
    el("start").textContent = "Restart";
    el("pause").textContent = "Pause";
    updateHUD();
}

function updateHUD() {
    el("score").textContent = "Score: " + score;
    el("level").textContent = "Level: " + (1 + Math.floor(elapsed / 15));
    el("shield").textContent = "Shield: " + (ship.shield ? "ON" : "OFF");
}

function burst(x, y, color, count = 22) {
    for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 40 + Math.random() * 180;
        particles.push({
            x, y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            life: 0.7,
            color
        });
    }
}

function finish() {
    state = "over";
    burst(ship.x, ship.y, "#fb7185", 45);

    best = Math.max(best, score);
    el("best").textContent = best;
    try {
        localStorage.setItem("neon-dodger-best", String(best));
    } catch (_) {}
}

function pause() {
    if (state === "playing") {
        state = "paused";
        keys.clear();
        el("pause").textContent = "Resume";
    } else if (state === "paused") {
        state = "playing";
        el("pause").textContent = "Pause";
    }
}

el("start").onclick = reset;
el("pause").onclick = pause;

function point(event) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: (event.clientX - rect.left) * W / rect.width,
        y: (event.clientY - rect.top) * H / rect.height
    };
}

canvas.addEventListener("pointerdown", event => {
    if (state !== "playing" || pointerId !== null) return;
    pointerId = event.pointerId;
    previousPointer = point(event);
    canvas.setPointerCapture(pointerId);
    canvas.focus();
    event.preventDefault();
});

canvas.addEventListener("pointermove", event => {
    if (event.pointerId !== pointerId) return;

    const current = point(event);
    if (state === "playing" && previousPointer) {
        // Relative dragging keeps your finger from hiding the ship.
        ship.x += current.x - previousPointer.x;
        ship.y += current.y - previousPointer.y;
        clampShip();
    }
    previousPointer = current;
    event.preventDefault();
});

function release(event) {
    if (event.pointerId === pointerId) {
        pointerId = null;
        previousPointer = null;
    }
}

canvas.addEventListener("pointerup", release);
canvas.addEventListener("pointercancel", release);
canvas.addEventListener("lostpointercapture", release);

window.addEventListener("keydown", event => {
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) {
        event.preventDefault();
        keys.add(event.key);
    }
});
window.addEventListener("keyup", event => keys.delete(event.key));
window.addEventListener("blur", () => {
    keys.clear();
    if (state === "playing") pause();
});
document.addEventListener("visibilitychange", () => {
    if (document.hidden && state === "playing") pause();
});

function clampShip() {
    ship.x = Math.max(20, Math.min(W - 20, ship.x));
    ship.y = Math.max(35, Math.min(H - 25, ship.y));
}

function update(dt) {
    for (const star of stars) {
        star.y = (star.y + star.speed * dt) % H;
    }

    particles = particles.filter(p => p.life > 0);
    for (const p of particles) {
        p.life -= dt;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
    }

    shake = Math.max(0, shake - dt);
    if (state !== "playing") return;

    elapsed += dt;
    invincible = Math.max(0, invincible - dt);
    score = Math.floor(elapsed * 10) + bonus;
    const level = 1 + Math.floor(elapsed / 15);

    let dx = Number(keys.has("ArrowRight")) - Number(keys.has("ArrowLeft"));
    let dy = Number(keys.has("ArrowDown")) - Number(keys.has("ArrowUp"));
    const length = Math.hypot(dx, dy) || 1;
    ship.x += dx / length * 300 * dt;
    ship.y += dy / length * 300 * dt;
    clampShip();

    meteorTimer -= dt;
    if (meteorTimer <= 0) {
        meteorTimer = Math.max(0.16, 0.7 - level * 0.055);
        const radius = 15 + Math.random() * 17;
        objects.push({
            type: "meteor",
            x: radius + Math.random() * (W - radius * 2),
            y: -45,
            r: radius,
            speed: 145 + level * 22 + Math.random() * 70,
            angle: Math.random() * 6.28,
            spin: Math.random() * 3 - 1.5
        });
    }

    pickupTimer -= dt;
    if (pickupTimer <= 0) {
        pickupTimer = 2 + Math.random() * 1.8;
        objects.push({
            type: Math.random() < 0.28 ? "shield" : "star",
            x: 30 + Math.random() * (W - 60),
            y: -30,
            r: 14,
            speed: 135,
            angle: 0,
            spin: 2
        });
    }

    for (const object of objects) {
        object.y += object.speed * dt;
        object.angle += object.spin * dt;

        if (object.dead) continue;

        const hit = Math.hypot(
            object.x - ship.x, object.y - ship.y
        ) < object.r + ship.r;

        if (!hit) continue;

        if (object.type === "meteor") {
            if (invincible > 0) continue;

            object.dead = true;
            if (ship.shield) {
                ship.shield = false;
                invincible = 1.2;
                shake = 0.2;
                burst(object.x, object.y, "#22d3ee");
            } else {
                shake = 0.35;
                finish();
                break;
            }
        } else {
            object.dead = true;
            if (object.type === "star") {
                bonus += 100;
                burst(object.x, object.y, "#facc15", 15);
            } else {
                ship.shield = true;
                burst(object.x, object.y, "#22d3ee", 15);
            }
        }
    }

    objects = objects.filter(o => !o.dead && o.y < H + 60);
    score = Math.floor(elapsed * 10) + bonus;
    updateHUD();
}

function drawStar(radius) {
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
        const angle = i * Math.PI / 5 - Math.PI / 2;
        const r = i % 2 === 0 ? radius : radius * 0.45;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
}

function overlay(title, subtitle) {
    ctx.fillStyle = "rgba(4,8,22,0.78)";
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = "center";
    ctx.shadowBlur = 0;
    ctx.fillStyle = "#67e8f9";
    ctx.font = "bold 35px system-ui";
    ctx.fillText(title, W / 2, H / 2 - 20);
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "16px system-ui";
    ctx.fillText(subtitle, W / 2, H / 2 + 22);
}

function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.save();

    if (shake > 0) {
        ctx.translate((Math.random() - 0.5) * 10,
                      (Math.random() - 0.5) * 10);
    }

    ctx.fillStyle = "#cbd5e1";
    for (const star of stars) {
        ctx.globalAlpha = 0.3 + star.r / 3;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.globalAlpha = 1;

    for (const object of objects) {
        ctx.save();
        ctx.translate(object.x, object.y);
        ctx.rotate(object.angle);
        ctx.shadowBlur = 16;

        if (object.type === "meteor") {
            ctx.fillStyle = "#9f1239";
            ctx.strokeStyle = "#fb7185";
            ctx.shadowColor = "#fb7185";
            ctx.lineWidth = 2;
            ctx.beginPath();
            for (let i = 0; i < 8; i++) {
                const angle = i * Math.PI / 4;
                const r = object.r * (i % 2 ? 0.8 : 1);
                const x = Math.cos(angle) * r;
                const y = Math.sin(angle) * r;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
        } else if (object.type === "star") {
            ctx.fillStyle = "#facc15";
            ctx.shadowColor = "#facc15";
            drawStar(16);
        } else {
            ctx.strokeStyle = "#22d3ee";
            ctx.shadowColor = "#22d3ee";
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(0, 0, 13, 0, Math.PI * 2);
            ctx.stroke();
            ctx.fillStyle = "#a5f3fc";
            ctx.fillRect(-3, -7, 6, 14);
        }

        ctx.restore();
    }

    if (state !== "over") {
        ctx.save();
        ctx.translate(ship.x, ship.y);
        ctx.globalAlpha = invincible > 0
            ? 0.45 + Math.abs(Math.sin(elapsed * 20)) * 0.55 : 1;

        ctx.fillStyle = "#fb923c";
        ctx.beginPath();
        ctx.moveTo(-7, 12);
        ctx.lineTo(0, 29 + Math.random() * 10);
        ctx.lineTo(7, 12);
        ctx.fill();

        ctx.shadowBlur = 20;
        ctx.shadowColor = "#22d3ee";
        ctx.fillStyle = "#67e8f9";
        ctx.beginPath();
        ctx.moveTo(0, -22);
        ctx.lineTo(17, 17);
        ctx.lineTo(0, 9);
        ctx.lineTo(-17, 17);
        ctx.closePath();
        ctx.fill();

        if (ship.shield) {
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(0, 0, 30, 0, Math.PI * 2);
            ctx.stroke();
        }
        ctx.restore();
    }

    for (const p of particles) {
        ctx.globalAlpha = Math.max(0, p.life / 0.7);
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x, p.y, 4, 4);
    }
    ctx.globalAlpha = 1;
    ctx.restore();

    if (state === "ready") {
        overlay("NEON DODGER", "Tap Start game below to launch");
    } else if (state === "paused") {
        overlay("PAUSED", "Tap Resume to continue");
    } else if (state === "over") {
        overlay("SHIP DESTROYED", "Score: " + score + " — tap Restart");
    }
}

reset();
state = "ready";
el("start").textContent = "Start game";

let previousTime = performance.now();

function frame(time) {
    const dt = Math.min((time - previousTime) / 1000, 0.033);
    previousTime = time;
    update(dt);
    draw();
    requestAnimationFrame(frame);
}

requestAnimationFrame(frame);
</script>
</body>
</html>
""",
    height=850,
    scrolling=True,
)
