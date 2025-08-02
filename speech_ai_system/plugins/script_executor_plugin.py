import pluggy
import subprocess
import json

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class ScriptExecutorPlugin:
    """A plugin for executing external scripts."""

    @hookimpl
    def run_script(self, script_path: str, params: dict) -> dict:
        """Executes a script at the given path and passes parameters."""
        print(f"ScriptExecutorPlugin: Executing script {script_path} with params {params}")
        try:
            # Use subprocess to call the external script, passing params as a JSON string.
            result = subprocess.run(
                ["python", script_path, json.dumps(params)],
                capture_output=True,
                text=True,
                check=True
            )
            # Assume the script prints its result as a JSON string to stdout.
            print(f"ScriptExecutorPlugin: Script output: {result.stdout}")
            return json.loads(result.stdout)
        except FileNotFoundError:
            print(f"ScriptExecutorPlugin: Error - Script not found at {script_path}")
            return {"status": "error", "message": "Script not found."}
        except subprocess.CalledProcessError as e:
            print(f"ScriptExecutorPlugin: Script execution failed: {e.stderr}")
            return {"status": "error", "message": e.stderr}
        except json.JSONDecodeError:
            print(f"ScriptExecutorPlugin: Error - Could not decode JSON from script output.")
            return {"status": "error", "message": "Invalid JSON output from script."}
