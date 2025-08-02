import pluggy
import json
import os
import threading

hookimpl = pluggy.HookimplMarker("speech_ai_system")

CONFIG_FILE = "config.json"

class ConfigPlugin:
    def __init__(self):
        self.config_path = CONFIG_FILE
        self.config = {}
        self.lock = threading.Lock() # To prevent race conditions when reading/writing
        self.load_config()

    def load_config(self):
        with self.lock:
            try:
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                        print("ConfigPlugin: Configuration loaded successfully.")
                else:
                    print(f"ConfigPlugin: Warning - {self.config_path} not found. Using empty config.")
                    self.config = {}
            except (json.JSONDecodeError, IOError) as e:
                print(f"ConfigPlugin: Error loading configuration file: {e}")
                self.config = {}

    @hookimpl(tryfirst=True)
    def get_config(self) -> dict:
        """Returns the entire configuration dictionary."""
        with self.lock:
            # Return a deep copy to prevent modification of the internal config
            return json.loads(json.dumps(self.config))

    @hookimpl
    def save_config(self, config_data: dict):
        """Saves the provided dictionary to the configuration file."""
        with self.lock:
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                # After saving, update the internal config
                self.config = config_data
                print("ConfigPlugin: Configuration saved successfully.")
            except IOError as e:
                print(f"ConfigPlugin: Error saving configuration file: {e}")
