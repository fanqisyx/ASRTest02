import pluggy

hookimpl = pluggy.HookimplMarker("speech_ai_system")

# A simple mapping from status codes to human-readable text
STATUS_CODE_TO_TEXT = {
    0: "待机中",
    1: "任务执行成功",
    2: "正在前往目的地",
    98: "电量不足，请充电",
    99: "正在充电",
}

class StatusHandlerPlugin:
    def __init__(self, pm):
        self.pm = pm

    @hookimpl
    def on_status_changed(self, status: dict):
        """Handles the status change event by speaking it."""
        status_value = status.get("value")

        message = STATUS_CODE_TO_TEXT.get(status_value)

        if message:
            print(f"StatusHandlerPlugin: Received status {status_value}, speaking message: '{message}'")
            self.pm.hook.speak_text(text=message)
        else:
            print(f"StatusHandlerPlugin: Received unknown status code: {status_value}")
