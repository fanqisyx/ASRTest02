import pluggy
import json
import requests

hookimpl = pluggy.HookimplMarker("speech_ai_system")

# The system prompt is complex and better kept in code for now,
# but could be moved to a separate file later.
SYSTEM_PROMPT = """
You are a helpful AI assistant for a voice-controlled robot. Your task is to understand the user's speech and convert it into a standardized JSON command.

The user's text will be provided to you. Based on the text, you must perform the following two tasks:
1. Determine the user's intent and select the appropriate command and parameters.
2. Generate a brief, natural language confirmation message to be spoken back to the user.

You MUST reply with ONLY a single, valid JSON object. Do not add any explanation or introductory text.

The JSON object must have the following structure:
{
  "command": "the_command_name",
  "params": { "parameter_name": "parameter_value" },
  "say": "the_confirmation_message"
}

Available commands and their parameters:
- "move_to": Moves the robot to a location.
  - "target": The destination (e.g., "A", "B", "充电站").
  - "speed": (Optional) The speed, can be "high", "medium", or "low".
- "transport_item": A complex command to transport an item.
  - "item": The item to transport.
  - "destination": The place to take the item.
- "report_status": Reports the robot's status.
  - "component": The component to report on (e.g., "battery", "location").

Example:
User text: "请用最快的速度把箱子送到A点"
Your response:
{
  "command": "transport_item",
  "params": {
    "item": "箱子",
    "destination": "A点"
  },
  "say": "好的，正在把箱子送到A点"
}
"""

class NLPPlugin:
    """A plugin for natural language processing via LM Studio."""
    def __init__(self, pm):
        self.pm = pm

    @hookimpl
    def process_asr_result(self, text: str) -> dict:
        """Parses text into a command by calling a local LLM."""
        config = self.pm.hook.get_config()
        lm_studio_url = config.get("servers", {}).get("lm_studio_url", "http://localhost:1234/v1/chat/completions")

        print(f"NLPPlugin: Received text '{text}', sending to LM Studio at {lm_studio_url}...")

        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "local-model", # This is often ignored by LM Studio
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7,
        }

        try:
            response = requests.post(lm_studio_url, headers=headers, json=payload, timeout=20)
            response.raise_for_status() # Raise an exception for bad status codes

            # Extract the content from the response
            response_data = response.json()
            content_str = response_data['choices'][0]['message']['content']

            print(f"NLPPlugin: Received raw content from LLM: {content_str}")

            # The content itself is a JSON string, so we parse it
            parsed_command = json.loads(content_str)

            # Basic validation
            if "command" in parsed_command and "say" in parsed_command:
                print(f"NLPPlugin: Successfully parsed command: {parsed_command}")
                return parsed_command
            else:
                print("NLPPlugin: Error - Parsed JSON is missing required 'command' or 'say' fields.")
                return None

        except requests.exceptions.RequestException as e:
            config = self.pm.hook.get_config()
            lm_studio_url = config.get("servers", {}).get("lm_studio_url", "http://localhost:1234/v1/chat/completions")
            print(f"NLPPlugin: Error - Could not connect to LM Studio at {lm_studio_url}. Is it running?")
            print(f"  Details: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"NLPPlugin: Error - Invalid response structure from LLM API.")
            print(f"  Details: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"NLPPlugin: Error - Could not decode JSON from LLM response content.")
            print(f"  Raw content was: {content_str}")
            print(f"  Details: {e}")
            return None
        except Exception as e:
            print(f"NLPPlugin: An unexpected error occurred: {e}")
            return None
