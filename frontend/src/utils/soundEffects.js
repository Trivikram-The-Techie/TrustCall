// Web Audio API Synthesizer for Real-Time Security Alerts
// Operates 100% offline without external audio assets.

let audioCtx = null;
let sirenOsc1 = null;
let sirenGain = null;
let sirenInterval = null;
let isMutedState = false;

function getAudioContext() {
  if (typeof window === 'undefined') return null;
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return null;

  if (!audioCtx) {
    audioCtx = new AudioContextClass();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

export function isAudioMuted() {
  return isMutedState;
}

export function setAudioMuted(muted) {
  isMutedState = muted;
  if (muted) {
    stopCriticalSiren();
  }
  return isMutedState;
}

export function toggleAudioMute() {
  return setAudioMuted(!isMutedState);
}

/**
 * Play a two-tone caution chime (e.g., when risk moves to Medium/Elevated)
 */
export function playCautionChime() {
  if (isMutedState) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(520, now);
    osc.frequency.setValueAtTime(660, now + 0.12);

    gain.gain.setValueAtTime(0.15, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.36);
  } catch (err) {
    console.warn('Could not play caution chime', err);
  }
}

/**
 * Play a rising 3-tone success chime (e.g., when challenge is passed / human verified)
 */
export function playSuccessChime() {
  if (isMutedState) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const tones = [523.25, 659.25, 783.99]; // C5, E5, G5

    tones.forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const startTime = now + i * 0.1;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, startTime);

      gain.gain.setValueAtTime(0.18, startTime);
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(startTime);
      osc.stop(startTime + 0.32);
    });
  } catch (err) {
    console.warn('Could not play success chime', err);
  }
}

/**
 * Play an alternating cyber alarm warble siren (for High / Critical spoof threats)
 */
export function playCriticalSiren() {
  if (isMutedState) return;
  stopCriticalSiren();

  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sawtooth';
    gain.gain.setValueAtTime(0.10, ctx.currentTime);

    let high = true;
    osc.frequency.setValueAtTime(820, ctx.currentTime);

    sirenInterval = setInterval(() => {
      if (!audioCtx || isMutedState) {
        stopCriticalSiren();
        return;
      }
      try {
        const t = audioCtx.currentTime;
        osc.frequency.cancelScheduledValues(t);
        osc.frequency.setValueAtTime(high ? 620 : 820, t);
        high = !high;
      } catch (e) {}
    }, 220);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();

    sirenOsc1 = osc;
    sirenGain = gain;

    // Auto-timeout siren after 8 seconds so it doesn't ring endlessly
    setTimeout(() => {
      stopCriticalSiren();
    }, 8000);
  } catch (err) {
    console.warn('Could not play critical siren', err);
  }
}

/**
 * Stop any currently sounding siren
 */
export function stopCriticalSiren() {
  if (sirenInterval) {
    clearInterval(sirenInterval);
    sirenInterval = null;
  }
  if (sirenOsc1) {
    try {
      sirenOsc1.stop();
      sirenOsc1.disconnect();
    } catch (e) {}
    sirenOsc1 = null;
  }
  if (sirenGain) {
    try {
      sirenGain.disconnect();
    } catch (e) {}
    sirenGain = null;
  }
}

/**
 * Short acoustic UI tap feedback
 */
export function playFeedbackTap() {
  if (isMutedState) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(900, now);
    osc.frequency.exponentialRampToValueAtTime(300, now + 0.05);

    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.06);
  } catch (e) {}
}
