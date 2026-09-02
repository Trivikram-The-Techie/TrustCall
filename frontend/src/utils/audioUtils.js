/**
 * Audio helper utilities for capturing microphone input,
 * resampling to 16kHz mono, and encoding to PCM / base64 chunks.
 */

export class AudioStreamRecorder {
  constructor(onAudioChunk, sampleRate = 16000) {
    this.onAudioChunk = onAudioChunk;
    this.targetSampleRate = sampleRate;
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.source = null;
    this.isRecording = false;
  }

  async start() {
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const sourceSr = this.audioContext.sampleRate;
    this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

    // Buffer size 4096 gives ~85ms chunks at 48kHz
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (e) => {
      if (!this.isRecording) return;
      const inputData = e.inputBuffer.getChannelData(0);
      
      // Resample to 16000 Hz if needed
      const resampled = this.resampleAudio(inputData, sourceSr, this.targetSampleRate);
      const pcm16 = this.floatTo16BitPCM(resampled);
      
      if (this.onAudioChunk) {
        this.onAudioChunk(pcm16);
      }
    };

    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    this.isRecording = true;
  }

  resampleAudio(audioBuffer, sourceRate, targetRate) {
    if (sourceRate === targetRate) return audioBuffer;
    const ratio = sourceRate / targetRate;
    const newLength = Math.round(audioBuffer.length / ratio);
    const result = new Float32Array(newLength);
    
    for (let i = 0; i < newLength; i++) {
      const origin = i * ratio;
      const index = Math.floor(origin);
      const nextIndex = Math.min(index + 1, audioBuffer.length - 1);
      const frac = origin - index;
      result[i] = audioBuffer[index] * (1 - frac) + audioBuffer[nextIndex] * frac;
    }
    return result;
  }

  floatTo16BitPCM(floatArray) {
    const buffer = new ArrayBuffer(floatArray.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < floatArray.length; i++) {
      const s = Math.max(-1, Math.min(1, floatArray[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return buffer;
  }

  stop() {
    this.isRecording = false;
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
  }
}

export function arrayBufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
