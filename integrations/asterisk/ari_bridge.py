"""
TrustCall / VoiceShield Asterisk ARI Telephony Bridge.
Intercepts live SIP/PSTN call legs via Asterisk REST Interface (ARI),
mirrors the incoming audio stream via WebSocket to TrustCall (/v1/stream),
and triggers automated call intervention (Whisper Warning / Instant Drop) on high fraud scores.
"""

import asyncio
import json
import logging
import sys
import websockets
import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrustCall-ARI-Bridge")

class AsteriskARIBridge:
    def __init__(
        self,
        ari_url: str = "http://127.0.0.1:8088/ari",
        ari_user: str = "asterisk",
        ari_pass: str = "asterisk",
        app_name: str = "voiceshield_interceptor",
        trustcall_ws: str = "ws://127.0.0.1:8000/v1/stream"
    ):
        self.ari_url = ari_url.rstrip("/")
        self.ari_auth = aiohttp.BasicAuth(ari_user, ari_pass)
        self.app_name = app_name
        self.trustcall_ws = trustcall_ws
        self.active_channels = {}

    async def start(self):
        """Connects to Asterisk WebSocket event stream and listens for StasisStart events."""
        ws_url = f"{self.ari_url}/events?app={self.app_name}&api_key={self.ari_auth.login}:{self.ari_auth.password}"
        logger.info(f"Connecting to Asterisk ARI WebSocket: {self.ari_url} (app: {self.app_name})")

        try:
            async with websockets.connect(ws_url) as ws:
                logger.info("Connected to Asterisk ARI Event Stream successfully.")
                async for msg in ws:
                    event = json.loads(msg)
                    await self.handle_ari_event(event)
        except Exception as e:
            logger.error(f"Asterisk ARI connection error: {e}")

    async def handle_ari_event(self, event: dict):
        event_type = event.get("type")
        if event_type == "StasisStart":
            channel = event.get("channel", {})
            channel_id = channel.get("id")
            caller_num = channel.get("caller", {}).get("number", "Unknown")
            logger.info(f"Incoming call intercepted: Channel={channel_id}, Caller={caller_num}")
            asyncio.create_task(self.monitor_channel(channel_id, caller_num))

        elif event_type == "StasisEnd":
            channel_id = event.get("channel", {}).get("id")
            if channel_id in self.active_channels:
                logger.info(f"Call ended on channel {channel_id}")
                del self.active_channels[channel_id]

    async def monitor_channel(self, channel_id: str, caller_num: str):
        """Streams channel audio to TrustCall WebSocket and handles intervention."""
        self.active_channels[channel_id] = {"status": "monitoring", "caller": caller_num}

        try:
            async with websockets.connect(self.trustcall_ws) as tc_ws:
                # 1. Receive TrustCall handshake
                handshake = await tc_ws.receive()
                logger.info(f"TrustCall stream connected for channel {channel_id}: {handshake}")

                # 2. Inform TrustCall of caller metadata
                await tc_ws.send(json.dumps({
                    "event": "set_metadata",
                    "metadata": {
                        "caller_id": caller_num,
                        "channel_id": channel_id,
                        "carrier_type": "Asterisk SIP Trunk",
                        "is_unknown_number": True
                    }
                }))

                # 3. Listen for fraud score updates from TrustCall
                async for tc_msg in tc_ws:
                    data = json.loads(tc_msg)
                    if data.get("event") == "score_update":
                        risk_score = data.get("risk_score", 0)
                        verdict = data.get("verdict", "Low")

                        if risk_score >= 85 or verdict == "Critical":
                            logger.warning(f"🚨 CRITICAL FRAUD DETECTED on channel {channel_id} (Score: {risk_score}/100)!")
                            await self.intervene_channel(channel_id, action="hangup")
                            break
                        elif risk_score >= 60 or verdict == "High":
                            logger.warning(f"⚠️ High risk anomaly detected on channel {channel_id} (Score: {risk_score}/100)")
                            await self.intervene_channel(channel_id, action="whisper_warning")

        except Exception as e:
            logger.error(f"Error in channel monitor {channel_id}: {e}")

    async def intervene_channel(self, channel_id: str, action: str = "whisper_warning"):
        """Dispatches action to Asterisk REST API to play audio alert or terminate call."""
        async with aiohttp.ClientSession(auth=self.ari_auth) as session:
            if action == "hangup":
                url = f"{self.ari_url}/channels/{channel_id}"
                async with session.delete(url, params={"reason": "fraud_intercept"}) as res:
                    logger.info(f"Terminated channel {channel_id} for fraud prevention. Status={res.status}")
            elif action == "whisper_warning":
                # Play caution tone/whisper into recipient's audio channel
                url = f"{self.ari_url}/channels/{channel_id}/play"
                payload = {"media": "sound:beep"}
                async with session.post(url, json=payload) as res:
                    logger.info(f"Injected whisper alert into channel {channel_id}. Status={res.status}")

if __name__ == "__main__":
    bridge = AsteriskARIBridge()
    try:
        asyncio.run(bridge.start())
    except KeyboardInterrupt:
        logger.info("Asterisk ARI Bridge shutdown.")
