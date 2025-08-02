import pluggy
import pyttsx3

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class TTSPlugin:
    """A plugin for text-to-speech using pyttsx3."""
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            print("TTSPlugin: pyttsx3 engine initialized successfully.")
        except Exception as e:
            print(f"TTSPlugin: Failed to initialize pyttsx3 engine: {e}")
            self.engine = None

    @hookimpl
    def speak_text(self, text: str):
        """Speaks the given text out loud."""
        if not self.engine:
            print("TTSPlugin: Cannot speak, engine not available.")
            return

        print(f"TTSPlugin: Speaking text: '{text}'")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            print("TTSPlugin: Finished speaking.")
        except Exception as e:
            print(f"TTSPlugin: Error while speaking: {e}")
