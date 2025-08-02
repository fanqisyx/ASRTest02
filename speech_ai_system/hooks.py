import pluggy

hookspec = pluggy.HookspecMarker("speech_ai_system")

class SpeechAIHooks:
    """Defines all the hook specifications in our system."""

    @hookspec
    def on_wake_word_detected(self, word: str):
        """Called when a wake word is detected, passing the detected word."""

    @hookspec(firstresult=True)
    def process_asr_result(self, text: str) -> dict:
        """
        Receives ASR result text and returns a standardized command JSON.
        firstresult=True means only the first non-null result is returned.
        """

    @hookspec
    def execute_command(self, command_data: dict):
        """Receives a command JSON and performs a specific action."""

    @hookspec
    def on_status_changed(self, status: dict):
        """Called when the robot's status changes."""

    @hookspec
    def run_script(self, script_path: str, params: dict) -> dict:
        """Calls and runs an external script, passing parameters."""
