/* Cancellable cinematic. Only this module owns the finale timeline/effects. */
const TIMING = { freeze: 1100, charge: 1600, orbit: 1600, cracks: 1100, explosion: 1400, darkness: 350 };

export class Finale {
  constructor(root) {
    this.root = root;
    this.version = 0;
    this.timers = new Map();
    this.animations = new Set();
    this.reduced = false;
  }

  cancel() {
    this.version += 1;
    for (const [timer, resolve] of this.timers) { clearTimeout(timer); resolve(); }
    this.timers.clear();
    for (const animation of this.animations) animation.cancel();
    this.animations.clear();
    this.root.hidden = true;
    delete this.root.dataset.scene;
    this.root.querySelector('.explosion').replaceChildren();
    this.root.querySelector('.game-over').hidden = true;
    this.root.querySelector('.space-scene').hidden = true;
    this.root.querySelector('.finale-shout').hidden = true;
  }

  wait(duration) {
    return new Promise((resolve) => {
      const timer = setTimeout(() => { this.timers.delete(timer); resolve(); }, duration);
      this.timers.set(timer, resolve);
    });
  }

  animate(element, frames, options) {
    const animation = element.animate(frames, { fill: 'forwards', ...options });
    this.animations.add(animation);
    animation.finished.then(() => {}, () => {});
    return animation;
  }

  setReducedMotion(reduced) {
    this.reduced = reduced;
    this.root.classList.toggle('reduced-finale', reduced);
    if (reduced) {
      // Retain the timeline and story but stop camera movement immediately.
      for (const animation of this.animations) animation.finish();
    }
  }

  async play({ characterSvg, earthSvg, quote, author, reducedMotion, onOver }) {
    this.cancel();
    const version = this.version;
    const alive = () => version === this.version;
    const root = this.root;
    const coach = root.querySelector('.finale-coach');
    const space = root.querySelector('.space-scene');
    const camera = root.querySelector('.earth-camera');
    const earth = root.querySelector('.earth-rig');
    const speck = root.querySelector('.coach-speck');
    const over = root.querySelector('.game-over');
    coach.innerHTML = characterSvg;
    earth.innerHTML = earthSvg;
    speck.innerHTML = characterSvg;
    root.querySelector('.finale-quote span').textContent = quote;
    root.querySelector('.finale-quote cite').textContent = author ? `— ${author}` : '';
    const fit = Math.min(root.parentElement.clientWidth / 700, root.parentElement.clientHeight / 850) * .92;
    coach.style.setProperty('--coach-fit', String(fit));
    root.hidden = false;
    this.setReducedMotion(reducedMotion);
    root.dataset.scene = 'freeze';
    await this.wait(TIMING.freeze);
    if (!alive()) return;

    root.dataset.scene = 'charge';
    root.querySelector('.finale-shout').hidden = false;
    if (!this.reduced) this.animate(coach, [
      { transform: `translate(-50%,-50%) scale(${fit})` },
      { transform: `translate(-50%,-46%) scale(${fit * 1.5})`, offset: .30 },
      { transform: `translate(-50%,-38%) scale(${fit * 3})`, offset: .66 },
      { transform: `translate(-50%,-30%) scale(${fit * 5.5})` },
    ], { duration: TIMING.charge, easing: 'steps(12,end)' });
    await this.wait(TIMING.charge);
    if (!alive()) return;

    root.dataset.scene = 'orbit';
    root.querySelector('.finale-shout').hidden = true;
    space.hidden = false;
    if (!this.reduced) this.animate(camera, [
      { transform: 'translate(-50%,-50%) scale(9)', opacity: .6 },
      { transform: 'translate(-50%,-50%) scale(1)', opacity: 1 },
    ], { duration: TIMING.orbit, easing: 'cubic-bezier(.15,.65,.2,1)' });
    await this.wait(TIMING.orbit);
    if (!alive()) return;

    root.dataset.scene = 'cracks';
    await this.wait(TIMING.cracks);
    if (!alive()) return;

    root.dataset.scene = 'explosion';
    this.explode();
    await this.wait(TIMING.explosion);
    if (!alive()) return;

    root.dataset.scene = 'darkness';
    await this.wait(TIMING.darkness);
    if (!alive()) return;
    root.dataset.scene = 'game_over';
    over.hidden = false;
    onOver();
  }

  explode() {
    const layer = this.root.querySelector('.explosion');
    const blast = document.createElement('div');
    blast.className = 'blast-shape';
    blast.innerHTML = '<span>BOOM.</span>';
    layer.append(blast);
    if (this.reduced) return;
    this.animate(blast, [
      { transform:'translate(-50%,-50%) scale(.12)', opacity:1 },
      { transform:'translate(-50%,-50%) scale(1.3)', opacity:1, offset:.35 },
      { transform:'translate(-50%,-50%) scale(1.8)', opacity:0 },
    ], { duration:1300, easing:'steps(8,end)' });
    for (let index = 0; index < 32; index += 1) {
      const fragment = document.createElement('i');
      fragment.className = index % 3 ? 'planet-fragment' : 'fire-fragment';
      const size = 12 + (index % 5) * 9;
      fragment.style.width = `${size}px`;
      fragment.style.height = `${size * .8}px`;
      layer.append(fragment);
      const angle = index / 32 * Math.PI * 2;
      const distance = Math.max(this.root.clientWidth, this.root.clientHeight) * (.4 + index % 4 * .12);
      this.animate(fragment, [
        { transform:'translate(-50%,-50%) scale(.2)', opacity:1 },
        { transform:`translate(calc(-50% + ${Math.cos(angle) * distance}px),calc(-50% + ${Math.sin(angle) * distance}px)) rotate(${index * 47}deg) scale(1)`, opacity:0 },
      ], { duration:1150 + index % 3 * 100, easing:'cubic-bezier(.1,.5,.5,1)' });
    }
  }
}
