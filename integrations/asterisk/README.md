# TrustCall Asterisk ARI / FreePBX Telephony Bridge 📞

This integration connects **TrustCall / VoiceShield** directly to telecom carrier trunks, Asterisk PBX, and FreePBX gateways for automated real-time scam interception.

## How It Works
1. **Call Leg Sniffing**: Asterisk ARI forwards incoming call audio to `ari_bridge.py`.
2. **WebSocket Mirroring**: `ari_bridge.py` mirrors the live 16kHz audio stream into TrustCall's `/v1/stream` WebSocket.
3. **Active Intervention**:
   - If risk score reaches **High (≥60)**: Injects an in-band caution tone / whisper warning into the recipient's ear.
   - If risk score reaches **Critical (≥85)**: Instantly sends a `DELETE /ari/channels/{channel_id}` command to terminate the call and prevent monetary theft.

## Usage
```bash
python integrations/asterisk/ari_bridge.py
```
