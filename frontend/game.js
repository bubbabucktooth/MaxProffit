/* Game state stays local; the cinematic is owned by the cancellable Finale. */
import { Finale } from './animations.js';
(() => {
  "use strict";
  const stage = document.querySelector(".stage");
  const character = document.getElementById("character");
  const motionButton = document.querySelector(".motion-toggle");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let svgSource = "";
  let paused = reducedMotion.matches;
  const throwButton = document.querySelector(".throw-button");
  const bubble = document.querySelector(".speech-bubble");
  const flightLayer = document.querySelector(".flight-layer");
  const restartButton = document.querySelector(".restart-button");
  const finale = new Finale(document.querySelector(".finale-layer"));
  const state = { phase: "idle", hits: 0, accepted: 0, queue: [], flights: new Map(), decks: new Map(), level: null, round: 0, initialized: false };
  let config;
  let quotes = [];
  let moneySvg = "";
  let earthSvg = "";
  let reactionTimer;
  let bubbleTimer;
  let hitAnimation;

  function setPhase(phase) {
    state.phase = phase;
    stage.dataset.phase = phase;
  }

  function updateReceipt() {
    if (!config) return;
    document.getElementById("money-count").value = String(state.hits);
    const pending = state.queue.length + state.flights.size;
    document.getElementById("pending-count").textContent = pending ? `(+${pending} in flight)` : "";
    throwButton.disabled = !state.initialized || state.accepted >= config.max_bills || ["finale", "game_over"].includes(state.phase);
    document.getElementById("throw-label").textContent = state.accepted >= config.max_bills ? "FULLY FUNDED" : "FEED THE EGO ↗";
  }

  function shuffled(items) {
    const deck = [...items];
    for (let index = deck.length - 1; index > 0; index -= 1) {
      const other = Math.floor(Math.random() * (index + 1));
      [deck[index], deck[other]] = [deck[other], deck[index]];
    }
    return deck;
  }

  function updateMotivation() {
    const levelIndex = config.levels.findLastIndex((level) => level.from_hit <= Math.max(1, state.hits));
    const level = config.levels[levelIndex];
    const nextLevel = config.levels[levelIndex + 1];
    const end = nextLevel ? nextLevel.from_hit - 1 : config.max_bills;
    const withinLevel = Math.max(0, state.hits - level.from_hit + 1) / (end - level.from_hit + 1);
    const duration = level.duration_seconds * (1 - .22 * withinLevel);
    const changed = state.level !== null && state.level !== level.id;
    state.level = level.id;
    stage.dataset.expression = level.key;
    stage.dataset.level = String(level.id);
    stage.style.setProperty("--idle-duration", `${duration}s`);
    stage.style.setProperty("--body-duration", `${duration}s`);
    stage.style.setProperty("--head-duration", `${duration * .75}s`);
    stage.style.setProperty("--left-duration", `${duration * 1.25}s`);
    stage.style.setProperty("--nod-angle", `${2 + withinLevel * 2}deg`);
    document.querySelector(".status span:last-child").textContent = level.status;
    if (changed) document.getElementById("expression-status").textContent = `Level ${level.id}: ${level.label}`;
    return changed;
  }

  function resetRound() {
    // Invalidate pending promise callbacks before cancelling their animations.
    state.round += 1;
    finale.cancel();
    clearTimeout(reactionTimer);
    hideQuote();
    hitAnimation?.cancel();
    for (const animation of state.flights.values()) animation.cancel();
    state.flights.clear();
    state.queue.length = 0;
    flightLayer.replaceChildren();
    state.hits = 0;
    state.accepted = 0;
    state.level = null;
    state.decks = new Map(config.levels.map((level) => [level.id, shuffled(quotes.filter((quote) => quote.level === level.id))]));
    delete bubble.dataset.quoteId;
    bubble.querySelector(".quote-text").textContent = "";
    bubble.querySelector(".quote-author").textContent = "";
    throwButton.hidden = false;
    document.getElementById("money-limit").textContent = String(config.max_bills);
    setPhase("idle");
    updateMotivation();
    updateReceipt();
    document.getElementById("expression-status").textContent = "New round. Level 1: Believer.";
  }
  restartButton.addEventListener("click", () => {
    if (state.phase !== 'game_over') return;
    resetRound();
    throwButton.focus();
  });

  function hideQuote() {
    clearTimeout(bubbleTimer);
    bubble.hidden = true;
  }

  function showQuote() {
    // Decks are never replenished inside a round. Python validates capacity.
    const quote = state.decks.get(state.level).pop();
    // Keep hyphenated words together without changing the source text in JSON.
    bubble.querySelector(".quote-text").textContent = quote.text.replace(/(?<=\w)-(?=\w)/g, '\u2011');
    bubble.querySelector(".quote-author").textContent = `— ${quote.author}`;
    bubble.dataset.quoteId = quote.id;
    bubble.hidden = false;
    clearTimeout(bubbleTimer);
    // Longer real quotations need more reading time than a short slogan.
    const readingTime = Math.max(3500, quote.text.split(/\s+/).length * 220);
    bubbleTimer = setTimeout(hideQuote, readingTime);
  }

  function hit(point) {
    state.hits += 1;
    const levelChanged = updateMotivation();
    setPhase(levelChanged ? "escalating" : "reacting");
    updateReceipt();
    showQuote();
    hitAnimation?.cancel();
    if (!paused) {
      hitAnimation = character.querySelector("svg").animate([
        { transform: "translate(0,0)" },
        { transform: "translate(5px,-7px) rotate(2deg)", offset: .28 },
        { transform: "translate(-3px,1px) rotate(-1deg)", offset: .6 },
        { transform: "translate(0,0)" },
      ], { duration: 260, easing: "steps(1,end)" });
      const impact = document.createElement("span");
      impact.className = "impact";
      impact.textContent = "+1";
      impact.style.left = `${point.x}px`;
      impact.style.top = `${point.y}px`;
      flightLayer.append(impact);
      const animation = impact.animate([
        { transform: "translate(-50%,-50%) scale(.7)", opacity: 1 },
        { transform: "translate(-50%,-140%) scale(1.15)", opacity: 0 },
      ], { duration: 360, easing: "ease-out" });
      animation.finished.then(() => impact.remove(), () => impact.remove());
    }
    clearTimeout(reactionTimer);
    if (state.hits === config.max_bills) {
      setPhase("finale");
      throwButton.hidden = true;
      hitAnimation?.cancel();
      hideQuote();
      const round = state.round;
      finale.play({ characterSvg: svgSource, earthSvg,
        quote: bubble.querySelector('.quote-text').textContent,
        author: bubble.querySelector('.quote-author').textContent.replace(/^—\s*/, ''),
        reducedMotion: paused,
        onOver: () => {
          if (round !== state.round) return;
          setPhase('game_over');
          restartButton.focus();
        },
      });
    } else {
      reactionTimer = setTimeout(() => setPhase("idle"), levelChanged ? 450 : 270);
    }
  }

  function launch(origin) {
    const round = state.round;
    const svg = character.querySelector("svg");
    // SVG coordinates account for mobile letterboxing and resized viewports.
    const screenPoint = new DOMPoint(350, 500).matrixTransform(svg.getScreenCTM());
    const stageRect = stage.getBoundingClientRect();
    const target = { x: screenPoint.x - stageRect.x, y: screenPoint.y - stageRect.y };
    const bill = document.createElement("div");
    bill.className = "flying-bill";
    bill.innerHTML = moneySvg;
    flightLayer.append(bill);
    const at = (x, y, angle, scale = 1) => `translate(${x}px,${y}px) translate(-50%,-50%) rotate(${angle}deg) scale(${scale})`;
    const animation = bill.animate(paused ? [
      { transform: at(target.x, target.y, 0, .7), opacity: 0 },
      { transform: at(target.x, target.y, 0, .7), opacity: 1 },
    ] : [
      { transform: at(origin.x, origin.y, -12), opacity: 1, easing: "ease-out" },
      { transform: at((origin.x + target.x) / 2, Math.min(origin.y, target.y) - 125, 12), opacity: 1, offset: .52, easing: "ease-in" },
      { transform: at(target.x, target.y, 190, .58), opacity: 1 },
    ], { duration: paused ? 100 : 560, fill: "forwards" });
    state.flights.set(bill, animation);
    animation.finished.then(() => {
      if (round === state.round) hit(target);
    }, () => {}).finally(() => {
      if (round !== state.round) return;
      state.flights.delete(bill);
      bill.remove();
      pumpQueue();
    });
  }

  function pumpQueue() {
    while (state.queue.length && state.flights.size < config.max_visible_flights) {
      launch(state.queue.shift());
    }
    updateReceipt();
  }

  throwButton.addEventListener("click", () => {
    if (throwButton.disabled || state.accepted >= config.max_bills || !["idle", "reacting", "escalating"].includes(state.phase)) return;
    state.accepted += 1;
    const rect = throwButton.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    state.queue.push({ x: rect.x + rect.width / 2 - stageRect.x, y: rect.y + rect.height / 2 - stageRect.y });
    pumpQueue();
  });

  function updateMotion() {
    stage.classList.toggle("motion-paused", paused);
    finale.setReducedMotion(paused);
    motionButton.setAttribute("aria-pressed", String(paused));
    motionButton.innerHTML = paused ? 'Resume motion <span aria-hidden="true">▶</span>' : 'Pause motion <span aria-hidden="true">Ⅱ</span>';
    if (paused) {
      hitAnimation?.cancel();
      for (const animation of state.flights.values()) animation.finish();
      flightLayer.querySelectorAll(".impact").forEach((impact) => impact.remove());
    }
  }
  motionButton.addEventListener("click", () => { paused = !paused; updateMotion(); });
  reducedMotion.addEventListener("change", (event) => { paused = event.matches; updateMotion(); });
  updateMotion();

  // The standard v1 component handshake, without a JS package/build dependency.
  // No setComponentValue messages: previews never cause a Python rerun.
  function send(type, payload = {}) {
    window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, "*");
  }
  window.addEventListener("message", (event) => {
    if (event.source !== window.parent || event.data?.type !== "streamlit:render") return;
    const incoming = event.data.args?.character_svg;
    if (typeof incoming === "string" && incoming !== svgSource) {
      // Trusted local asset supplied by app.py, never user-generated markup.
      character.innerHTML = incoming;
      svgSource = incoming;
      character.setAttribute("aria-busy", "false");
    }
    if (!state.initialized && Array.isArray(event.data.args?.quotes)) quotes = event.data.args.quotes;
    if (!state.initialized && event.data.args?.config) config = event.data.args.config;
    if (typeof event.data.args?.money_svg === "string" && event.data.args.money_svg !== moneySvg) {
      moneySvg = event.data.args.money_svg;
      document.getElementById("money-icon").innerHTML = moneySvg;
    }
    if (typeof event.data.args?.earth_svg === 'string') earthSvg = event.data.args.earth_svg;
    if (!state.initialized && svgSource && moneySvg && earthSvg && quotes.length && config) {
      state.initialized = true;
      resetRound();
    }
    updateReceipt();
    send("streamlit:setFrameHeight", { height: window.innerHeight });
  });
  setPhase("idle");
  window.addEventListener("resize", () => send("streamlit:setFrameHeight", { height: window.innerHeight }));
  send("streamlit:componentReady", { apiVersion: 1 });
})();
