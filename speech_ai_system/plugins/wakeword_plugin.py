import pluggy
import vosk
import sounddevice as sd
import json
import os
import requests
import zipfile
import threading
import time

hookimpl = pluggy.HookimplMarker("speech_ai_system")

# --- Model Download and Management ---
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
MODELS_DIR = "models"
MODEL_NAME = "vosk-model-small-cn-0.22"
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_NAME)
ZIP_PATH = os.path.join(MODELS_DIR, f"{MODEL_NAME}.zip")

def download_and_unzip_model():
    """Checks for the model, downloads and unzips if not present."""
    if os.path.exists(MODEL_PATH):
        print(f"WakeWordPlugin: Model already exists at {MODEL_PATH}")
        return True

    print(f"WakeWordPlugin: Model not found. Downloading from {MODEL_URL}...")
    os.makedirs(MODELS_DIR, exist_ok=True)

    try:
        with requests.get(MODEL_URL, stream=True) as r:
            r.raise_for_status()
            with open(ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"WakeWordPlugin: Download complete. Unzipping model...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(MODELS_DIR)

        print(f"WakeWordPlugin: Model unzipped successfully.")
        os.remove(ZIP_PATH) # Clean up the zip file
        return True

    except requests.exceptions.RequestException as e:
        print(f"WakeWordPlugin: Error downloading model: {e}")
        return False
    except zipfile.BadZipFile:
        print(f"WakeWordPlugin: Error, downloaded file is not a valid zip file.")
        return False
    except Exception as e:
        print(f"WakeWordPlugin: An unexpected error occurred: {e}")
        return False

# --- Wake Word Plugin ---
class WakeWordPlugin:
    def __init__(self, pm):
        self.pm = pm
        self.wake_words = ["小车", "机器人"] # The wake words to listen for
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.thread = None

        if download_and_unzip_model():
            try:
                self.model = vosk.Model(MODEL_PATH)
                # The keywords list is passed to the recognizer.
                self.recognizer = vosk.KaldiRecognizer(self.model, 16000, json.dumps(self.wake_words, ensure_ascii=False))
                print("WakeWordPlugin: Recognizer initialized successfully.")
            except Exception as e:
                print(f"WakeWordPlugin: Failed to initialize Vosk recognizer: {e}")
        else:
            print("WakeWordPlugin: Could not load model, plugin will be inactive.")

    def _listen_loop(self):
        """The main loop for listening to the microphone."""
        try:
            with sd.RawInputStream(samplerate=16000, blocksize=800, dtype='int16', channels=1) as stream:
                print("\nWakeWordPlugin: Listening for wake words...")
                while self.is_listening:
                    data, overflowed = stream.read(800)
                    if self.recognizer.AcceptWaveform(bytes(data)):
                        result = json.loads(self.recognizer.Result())
                        # Check if the recognized text contains any of our wake words
                        if any(word in result.get("text", "") for word in self.wake_words):
                            detected_word = result["text"].strip()
                            print(f"WakeWordPlugin: Wake word detected: '{detected_word}'")
                            self.pm.hook.on_wake_word_detected(word=detected_word)
                            # Pause listening briefly to avoid immediate re-triggering
                            time.sleep(2)
                            print("WakeWordPlugin: Resuming listening...")
        except Exception as e:
            print(f"WakeWordPlugin: Error in listening loop: {e}")
            self.is_listening = False

    def start(self):
        """Starts the listening thread."""
        if not self.recognizer:
            print("WakeWordPlugin: Cannot start, recognizer not initialized.")
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
                self.thread.join() # Wait for the thread to finish
            print("WakeWordPlugin: Stopped listening.")

    @hookimpl
    def start_listening(self):
        """Starts the listening thread when the hook is called."""
        self.start()

    @hookimpl
    def on_shutdown(self):
        """Stops the listening thread when the hook is called."""
        self.stop()

    @hookimpl
    def pause_listening(self):
        if self.is_listening:
            self.is_listening = False
            print("WakeWordPlugin: Listening paused.")

    @hookimpl
    def resume_listening(self):
        if not self.is_listening:
            # To resume, we need to restart the thread.
            # This assumes the previous thread has already exited.
            self.start()

    @hookimpl(trylast=True) # Run this after other wake word handlers
    def on_wake_word_detected(self, word: str):
        """When a wake word is detected, pause self."""
        print("WakeWordPlugin: Pausing myself after wake word detection.")
        self.pause_listening()
