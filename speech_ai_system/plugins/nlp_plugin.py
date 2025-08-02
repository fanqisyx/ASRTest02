import pluggy
import json

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class NLPPlugin:
    """A plugin for natural language processing."""

    @hookimpl
    def process_asr_result(self, text: str) -> dict:
        """Parses text into a command using a local LLM (mocked)."""
        print(f"NLPPlugin: Received text '{text}', parsing...")
        if "去A点" in text:
            result = {
                "command": "move_to",
                "params": {"target": "A", "speed": "high"},
                "say": "好的，正在前往 A 点"
            }
            return result
        if "运输" in text:
            result = {
                "command": "transport_item",
                "params": {"item": "box", "destination": "B"},
                "say": "收到，开始运输物品"
            }
            return result
        return None # Return None if the plugin cannot handle the text.
