/**
 * TrustCall / VoiceShield JavaScript SDK
 * Lightweight client for integrating real-time voice clone and impersonation detection
 * into Web applications, browser softphones, and Node.js telephony gateways.
 */

class VoiceShieldClient {
  /**
   * @param {Object} options
   * @param {string} options.baseUrl - REST API base URL (e.g., "http://localhost:8000")
   * @param {string} [options.wsUrl] - WebSocket URL (e.g., "ws://localhost:8000/v1/stream")
   * @param {string} [options.apiKey] - Optional enterprise authentication key
   */
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || "http://localhost:8000";
    this.wsUrl = options.wsUrl || (this.baseUrl.replace(/^http/, "ws") + "/v1/stream");
    this.apiKey = options.apiKey || null;
    this.ws = null;
    this.sessionId = null;
    this.callbacks = {};
  }

  /**
   * Establishes a real-time WebSocket connection for live streaming call audio.
   * @param {Object} handlers
   * @param {Function} handlers.onScore - Fired when a new risk score is calculated
   * @param {Function} handlers.onAlert - Fired when risk tier exceeds threshold
   * @param {Function} handlers.onConnect - Fired on successful handshake
   * @param {Function} handlers.onError - Fired on connection error
   */
  connectStream(handlers = {}) {
    this.callbacks = handlers;

    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      if (this.callbacks.onConnect) {
        this.callbacks.onConnect();
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        if (payload.event === "connected") {
          this.sessionId = payload.session_id;
        } else if (payload.event === "score_update") {
          if (this.callbacks.onScore) {
            this.callbacks.onScore(payload);
          }
          if (["Medium", "High", "Critical"].includes(payload.verdict) && this.callbacks.onAlert) {
            this.callbacks.onAlert(payload);
          }
        }
      } catch (err) {
        if (this.callbacks.onError) this.callbacks.onError(err);
      }
    };

    this.ws.onerror = (err) => {
      if (this.callbacks.onError) this.callbacks.onError(err);
    };

    this.ws.onclose = () => {
      this.ws = null;
    };
  }

  /**
   * Sends an audio frame (200-500ms) over the WebSocket stream.
   * Accepts ArrayBuffer (raw 16kHz PCM), Blob, or Base64 string.
   */
  sendAudioChunk(chunkData, transcript = null) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("VoiceShield WebSocket is not connected. Call connectStream() first.");
    }

    if (chunkData instanceof ArrayBuffer || chunkData instanceof Uint8Array) {
      this.ws.send(chunkData);
    } else if (typeof chunkData === "string") {
      this.ws.send(JSON.stringify({
        event: "audio_chunk",
        audio_base64: chunkData,
        transcript: transcript
      }));
    }
  }

  /**
   * Analyzes an uploaded audio clip via REST POST /v1/score.
   * @param {string} audioBase64 - Base64 encoded audio string
   * @param {Object} options - Metadata and hints
   * @returns {Promise<Object>}
   */
  async scoreClip(audioBase64, options = {}) {
    const response = await fetch(`${this.baseUrl}/v1/score`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey ? { "Authorization": `Bearer ${this.apiKey}` } : {})
      },
      body: JSON.stringify({
        audio_base64: audioBase64,
        sample_rate: options.sampleRate || 16000,
        text_transcript: options.transcript || null,
        caller_metadata: options.callerMetadata || null,
        session_id: options.sessionId || this.sessionId
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "VoiceShield scoring failed");
    }

    return await response.json();
  }

  /**
   * Retrieves non-biometric alert telemetry for a session.
   * @param {string} sessionId
   * @returns {Promise<Object>}
   */
  async getAlerts(sessionId = this.sessionId) {
    if (!sessionId) throw new Error("Session ID is required to fetch alerts");
    const response = await fetch(`${this.baseUrl}/v1/alerts?session_id=${encodeURIComponent(sessionId)}`);
    return await response.json();
  }

  /**
   * Disconnects the active WebSocket stream.
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = VoiceShieldClient;
} else if (typeof window !== "undefined") {
  window.VoiceShieldClient = VoiceShieldClient;
}
