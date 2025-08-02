import pluggy
import vosk
import sounddevice as sd
import json
import os
import threading
import queue

hookimpl = pluggy.HookimplMarker("speech_ai_system")

# Use the same model path as the WakeWord plugin
MODELS_DIR = "models"
MODEL_NAME = "vosk-model-small-cn-0.22"
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_NAME)

class ASRPlugin:
    def __init__(self, pm):
        self.pm = pm
        self.model = None
        self.is_active = False
        self.audio_queue = queue.Queue()

        if not os.path.exists(MODEL_PATH):
            print("ASRPlugin: Model not found. Please run WakeWord plugin first to download.")
            return

        try:
            self.model = vosk.Model(MODEL_PATH)
            print("ASRPlugin: Vosk model loaded successfully.")
        except Exception as e:
            print(f"ASRPlugin: Failed to load Vosk model: {e}")

    def _recording_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status)
        self.audio_queue.put(bytes(indata))

    def _process_audio(self):
        """Processes the recorded audio to get the transcription."""
        if not self.model:
            print("ASRPlugin: Cannot process audio, model not loaded.")
            self.is_active = False
            return

        # Use a general-purpose recognizer (no keywords)
        recognizer = vosk.KaldiRecognizer(self.model, 16000)
        print("ASRPlugin: Listening for command...")

        # Play a sound to indicate listening has started
        self.pm.hook.speak_text(text="在的")

        try:
            with sd.RawInputStream(samplerate=16000, blocksize=800, dtype='int16', channels=1, callback=self._recording_callback):
                # Listen for a few seconds (e.g., 5 seconds)
                for _ in range(int(16000 / 800 * 5)): # 5 seconds of recording
                    data = self.audio_queue.get()
                    if recognizer.AcceptWaveform(data):
                        break # Partial result found, can stop early

                final_result = json.loads(recognizer.FinalResult())
                text = final_result.get("text", "").strip()

                if text:
                    print(f"ASRPlugin: Recognized text: '{text}'")
                    self.pm.hook.process_asr_result(text=text)
                else:
                    print("ASRPlugin: No text recognized.")
                    self.pm.hook.speak_text(text="没有听到指令")

        except Exception as e:
            print(f"ASRPlugin: Error during ASR processing: {e}")
        finally:
            self.is_active = False
            print("ASRPlugin: Session finished.")
            # Tell the wake word listener to resume
            self.pm.hook.resume_listening()


    @hookimpl
    def start_asr_session(self):
        """Starts a new ASR session in a separate thread."""
        if not self.model:
            print("ASRPlugin: Cannot start session, model not loaded.")
            return

        if self.is_active:
            print("ASRPlugin: Session already in progress.")
            return

        # Pause the wake word listener
        self.pm.hook.pause_listening()

        self.is_active = True
        thread = threading.Thread(target=self._process_audio)
        thread.daemon = True
        thread.start()

    @hookimpl
    def on_wake_word_detected(self, word: str):
        """When a wake word is detected, start the ASR session."""
        print(f"ASRPlugin: Wake word '{word}' detected, starting ASR session.")
        self.start_asr_session()
