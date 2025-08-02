import pluggy

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class StatusHandlerPlugin:
    def __init__(self, pm):
        self.pm = pm

    @hookimpl
    def on_status_changed(self, status: dict):
        """Handles the status change event by speaking it."""
        config = self.pm.hook.get_config()
        status_map = config.get("state_manager", {}).get("status_code_mapping", {})

        status_value = status.get("value")
        # In the config file, keys are strings.
        message = status_map.get(str(status_value))

        if message:
            print(f"StatusHandlerPlugin: Received status {status_value}, speaking message: '{message}'")
            self.pm.hook.speak_text(text=message)
        else:
            print(f"StatusHandlerPlugin: Received unknown status code: {status_value}")
