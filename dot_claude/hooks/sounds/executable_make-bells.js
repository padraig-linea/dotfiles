// Synthesise small bell sounds as 16-bit mono WAV files.
// Usage: node make-bells.js <output-dir>
const fs = require('fs');
const path = require('path');

const SR = 44100;
const outDir = process.argv[2];
fs.mkdirSync(outDir, { recursive: true });

// [frequency ratio, amplitude, decay multiplier]; the slightly detuned partial gives a shimmering ring.
const BRIGHT = [[1, 1, 1], [1.003, 0.5, 1], [2.0, 0.5, 1.6], [2.76, 0.35, 2.2], [5.4, 0.2, 3.5], [8.93, 0.1, 5]];
const MELLOW = [[1, 1, 1], [1.002, 0.6, 1], [2.0, 0.3, 1.8], [3.0, 0.12, 2.5]];

function strike(buf, t0, f0, amp, tau, partials) {
  const start = Math.floor(t0 * SR);
  for (let i = start; i < buf.length; i++) {
    const t = (i - start) / SR;
    const attack = Math.min(1, t / 0.003);
    let s = 0;
    for (const [ratio, a, decay] of partials) {
      if (f0 * ratio > 18000) continue;
      s += a * Math.exp((-t * decay) / tau) * Math.sin(2 * Math.PI * f0 * ratio * t);
    }
    buf[i] += amp * attack * s;
  }
}

function writeWav(name, seconds, render) {
  const buf = new Float64Array(Math.floor(seconds * SR));
  render(buf);
  const fade = Math.floor(0.05 * SR);
  for (let i = 0; i < fade; i++) buf[buf.length - 1 - i] *= i / fade;
  const peak = buf.reduce((m, v) => Math.max(m, Math.abs(v)), 0);
  const data = Buffer.alloc(buf.length * 2);
  buf.forEach((v, i) => data.writeInt16LE(Math.round((v / peak) * 0.7 * 32767), i * 2));
  const header = Buffer.alloc(44);
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + data.length, 4);
  header.write('WAVEfmt ', 8);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(SR, 24);
  header.writeUInt32LE(SR * 2, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write('data', 36);
  header.writeUInt32LE(data.length, 40);
  fs.writeFileSync(path.join(outDir, name), Buffer.concat([header, data]));
  console.log(name);
}

// Single bright strike, like a desk bell.
writeWav('bell-single.wav', 1.5, (b) => strike(b, 0, 1760, 1, 0.6, BRIGHT));

// A little bell being shaken: quick alternating strikes.
writeWav('bell-tinkle.wav', 1.4, (b) => {
  [0, 0.09, 0.18, 0.27, 0.36].forEach((t, i) => strike(b, t, i % 2 ? 2793 : 2637, 1 - i * 0.12, 0.35, BRIGHT));
});

// Two-note ding-dong.
writeWav('bell-dingdong.wav', 1.8, (b) => {
  strike(b, 0, 1318.5, 1, 0.8, BRIGHT);
  strike(b, 0.35, 1046.5, 1, 0.8, BRIGHT);
});

// Soft, lower single bell.
writeWav('bell-soft-low.wav', 2.0, (b) => strike(b, 0, 659.3, 1, 1.0, MELLOW));

// Rising three-note glockenspiel arpeggio.
writeWav('bell-triple.wav', 1.6, (b) => {
  [[0, 1046.5], [0.12, 1318.5], [0.24, 1568]].forEach(([t, f]) => strike(b, t, f, 1, 0.5, BRIGHT));
});
