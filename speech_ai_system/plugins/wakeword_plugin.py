import pluggy
import vosk
import json
import os
import requests
import zipfile
import threading
import time

hookimpl = pluggy.HookimplMarker("speech_ai_system")

MODELS_DIR = "models"

def download_and_unzip_model(model_url, model_name):
    """Checks for the model, downloads and unzips if not present."""
    model_path = os.path.join(MODELS_DIR, model_name)
    zip_path = os.path.join(MODELS_DIR, f"{model_name}.zip")

    if os.path.exists(model_path):
        print(f"WakeWordPlugin: Model '{model_name}' already exists at {model_path}")
        return True

    print(f"WakeWordPlugin: Model not found. Downloading from {model_url}...")
    os.makedirs(MODELS_DIR, exist_ok=True)

    try:
        with requests.get(model_url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"WakeWordPlugin: Download complete. Unzipping model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(MODELS_DIR)

        print(f"WakeWordPlugin: Model unzipped successfully.")
        os.remove(zip_path)
        return True

    except Exception as e:
        print(f"WakeWordPlugin: An error occurred during model download/unzip: {e}")
        return False

class WakeWordPlugin:
    def __init__(self, pm):
        self.pm = pm
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.thread = None
        self.config = {} # Lazy loaded

    def _initialize_from_config(self):
        """Loads config and initializes the Vosk model and recognizer."""
        if not self.config:
            full_config = self.pm.hook.get_config()
            self.config = full_config

        model_config = self.config.get("models", {})
        model_url = model_config.get("vosk_model_url")
        model_name = model_config.get("vosk_model_name")

        if not model_url or not model_name:
            print("WakeWordPlugin: Error - Vosk model URL or name not found in config.")
            return False

        if not download_and_unzip_model(model_url, model_name):
            print("WakeWordPlugin: Could not prepare model, plugin will be inactive.")
            return False

        try:
            model_path = os.path.join(MODELS_DIR, model_name)
            self.model = vosk.Model(model_path)

            general_config = self.config.get("general", {})
            wake_words = general_config.get("wake_words", ["小车", "机器人"])

            self.recognizer = vosk.KaldiRecognizer(self.model, 16000, json.dumps(wake_words, ensure_ascii=False))
            print(f"WakeWordPlugin: Recognizer initialized for wake words: {wake_words}")
            return True
        except Exception as e:
            print(f"WakeWordPlugin: Failed to initialize Vosk recognizer: {e}")
            return False

    def _listen_loop(self):
        """The main loop for listening to the microphone."""
        try:
            import sounddevice as sd
            with sd.RawInputStream(samplerate=16000, blocksize=800, dtype='int16', channels=1) as stream:
                print("\nWakeWordPlugin: Listening for wake words...")
                while self.is_listening:
                    data, overflowed = stream.read(800)
                    if self.recognizer and self.recognizer.AcceptWaveform(bytes(data)):
                        result = json.loads(self.recognizer.Result())

                        wake_words = self.config.get("general", {}).get("wake_words", [])
                        if any(word in result.get("text", "") for word in wake_words):
                            detected_word = result["text"].strip()
                            print(f"WakeWordPlugin: Wake word detected: '{detected_word}'")
                            self.pm.hook.on_wake_word_detected(word=detected_word)
        except Exception as e:
            print(f"WakeWordPlugin: Error in listening loop: {e}")
            self.is_listening = False

    def start(self):
        """Starts the listening thread."""
        if not self._initialize_from_config():
             print("WakeWordPlugin: Initialization from config failed. Cannot start.")
             return

        if not self.is_listening:
            self.is_listening = True
            self.thread = threading.Thread(target=self._listen_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """Stops the listening thread."""
        if self.is_listening:
            self.is_listening = False
            if self.thread:
                self.thread.join()
            print("WakeWordPlugin: Stopped listening.")

    @hookimpl
    def start_listening(self):
        self.start()

    @hookimpl
    def on_shutdown(self):
        self.stop()

    @hookimpl
    def pause_listening(self):
        if self.is_listening:
            self.is_listening = False
            print("WakeWordPlugin: Listening paused.")

    @hookimpl
    def resume_listening(self):
        if not self.is_listening:
            self.start()

    @hookimpl(trylast=True)
    def on_wake_word_detected(self, word: str):
        self.pause_listening()
