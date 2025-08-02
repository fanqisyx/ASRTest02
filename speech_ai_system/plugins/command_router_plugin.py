import pluggy
import json
import os

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class CommandRouterPlugin:
    def __init__(self, pm, config_file="config/project.json"):
        self.pm = pm  # The plugin manager instance
        self.config = self._load_config(config_file)

    def _load_config(self, file_path):
        if not os.path.exists(file_path):
            print(f"CommandRouterPlugin: Error - Config file not found at {file_path}")
            return {"commands": {}}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @hookimpl(hookwrapper=True)
    def process_asr_result(self, text: str):
        """
        A hook wrapper that intercepts the result of the NLP plugin.
        It runs after the NLP plugin and routes the command.
        """
        # This code runs before the NLP plugin's hook implementation
        print("CommandRouterPlugin: Intercepted ASR result, waiting for NLP plugin...")

        outcome = yield

        # This code runs after the NLP plugin's hook implementation
        nlp_result = outcome.get_result()

        if nlp_result:
            print(f"CommandRouterPlugin: NLP returned: {nlp_result}. Routing command...")
            self.route_command(nlp_result)
        else:
            print("CommandRouterPlugin: NLP did not return a result. No command to route.")

    def route_command(self, command_data: dict):
        """The core routing logic."""
        command_name = command_data.get("command")
        if not command_name or command_name not in self.config.get("commands", {}):
            print(f"CommandRouterPlugin: Unknown or unconfigured command '{command_name}'. Cannot route.")
            return

        command_config = self.config["commands"][command_name]
        executor_type = command_config.get("executor")

        if executor_type == "ModbusExecutor":
            print(f"CommandRouterPlugin: Routing to ModbusExecutor...")
            self.pm.hook.execute_command(command_data=command_data)

        elif executor_type == "ScriptExecutor":
            script_path = command_config.get("script_path")
            if script_path:
                print(f"CommandRouterPlugin: Routing to ScriptExecutor to run {script_path}...")
                self.pm.hook.run_script(
                    script_path=script_path,
                    params=command_data.get("params", {})
                )
            else:
                print("CommandRouterPlugin: Error - ScriptExecutor specified but no script_path is configured.")

        else:
            print(f"CommandRouterPlugin: Error - Unknown executor type '{executor_type}' in config.")
