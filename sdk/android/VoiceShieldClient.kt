package ai.voiceshield.sdk

import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * TrustCall / VoiceShield Android Kotlin SDK
 * Provides real-time call interception and voice clone detection
 * for mobile banking applications and telecom dialers.
 */
class VoiceShieldClient(
    private val baseUrl: String = "https://api.voiceshield.internal",
    private val apiKey: String? = null
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var webSocket: WebSocket? = null
    var listener: ScoreListener? = null

    interface ScoreListener {
        fun onScoreUpdate(riskScore: Int, verdict: String, explanation: String)
        fun onAlertTriggered(alertTier: String, actionRecommendation: String)
        fun onError(error: Throwable)
    }

    /**
     * Connects to live audio stream WebSocket.
     */
    fun startStreamingSession(sessionId: String = java.util.UUID.randomUUID().toString()) {
        val wsUrl = baseUrl.replace("http", "ws") + "/v1/stream"
        val request = Request.Builder()
            .url(wsUrl)
            .apply { if (apiKey != null) addHeader("Authorization", "Bearer $apiKey") }
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(ws: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    if (json.optString("event") == "score_update") {
                        val risk = json.getInt("risk_score")
                        val verdict = json.getString("verdict")
                        val explanation = json.getString("explanation")
                        val action = json.optString("action_recommendation")

                        listener?.onScoreUpdate(risk, verdict, explanation)
                        if (verdict in listOf("Medium", "High", "Critical")) {
                            listener?.onAlertTriggered(verdict, action)
                        }
                    }
                } catch (e: Exception) {
                    listener?.onError(e)
                }
            }

            override fun onFailure(ws: WebSocket, t: Throwable, response: Response?) {
                listener?.onError(t)
            }
        })
    }

    /**
     * Streams a raw 16kHz PCM audio chunk (e.g. from AudioRecord).
     */
    fun sendAudioChunk(pcmChunk: ByteArray) {
        webSocket?.send(okio.ByteString.of(*pcmChunk))
    }

    /**
     * Closes the active stream.
     */
    fun stopStreamingSession() {
        webSocket?.close(1000, "Session completed")
        webSocket = null
    }
}
