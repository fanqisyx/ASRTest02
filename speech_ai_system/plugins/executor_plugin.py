import pluggy
from pyModbusTCP.client import ModbusClient

hookimpl = pluggy.HookimplMarker("speech_ai_system")

# --- Configuration ---
MODBUS_HOST = "localhost"
MODBUS_PORT = 502

# A simple mapping from location names to register values
LOCATION_TO_REGISTER_VALUE = {
    "A": 1,
    "B": 2,
    "C": 3,
    "充电站": 99,
}

class ExecutorPlugin:
    """A plugin for command execution via ModbusTCP."""

    def __init__(self):
        self.client = ModbusClient(host=MODBUS_HOST, port=MODBUS_PORT, auto_open=True, auto_close=True)

    @hookimpl
    def execute_command(self, command_config: dict, command_data: dict):
        """Executes a specific robot action based on the command config."""
        action = command_config.get("action")

        print(f"ExecutorPlugin: Received action '{action}' with data {command_data}")

        if not self.client.is_open():
            print(f"ExecutorPlugin: Error - could not connect to Modbus server at {MODBUS_HOST}:{MODBUS_PORT}")
            # Optionally, we could speak an error message
            # self.pm.hook.speak_text(text="无法连接到机器人控制器")
            return

        try:
            if action == "write_register":
                self._handle_write_register(command_config, command_data)
            # Add other actions here, e.g.:
            # elif action == "read_register":
            #     self._handle_read_register(command_config, command_data)
            else:
                print(f"ExecutorPlugin: Error - Unknown action '{action}'")

        except Exception as e:
            print(f"ExecutorPlugin: An error occurred during Modbus communication: {e}")

    def _handle_write_register(self, command_config: dict, command_data: dict):
        """Handles the 'write_register' action."""
        params = command_config.get("params", {})
        register_addr = params.get("register")

        # Get the value to write. It could be a static value or a placeholder.
        value_template = params.get("value")

        if register_addr is None or value_template is None:
            print("ExecutorPlugin: Error - 'register' and 'value' must be defined in config for write_register.")
            return

        # Substitute placeholder values from the command data
        # Example: if value_template is "{target}" and command_data has params["target"] = "A"
        try:
            # This is a simple substitution. A more complex system might use a template engine.
            final_value_str = value_template.format(**command_data.get("params", {}))

            # Now, we need to convert the final value to an integer.
            # It might be a direct integer string, or a location name like "A".
            if final_value_str in LOCATION_TO_REGISTER_VALUE:
                final_value = LOCATION_TO_REGISTER_VALUE[final_value_str]
            else:
                final_value = int(final_value_str)

        except (KeyError, ValueError) as e:
            print(f"ExecutorPlugin: Error - Could not resolve value for writing. Template: '{value_template}', Data: {command_data.get('params')}. Details: {e}")
            return

        print(f"ExecutorPlugin: Writing value {final_value} to register {register_addr}...")

        is_ok = self.client.write_single_register(register_addr, final_value)

        if is_ok:
            print("ExecutorPlugin: Write successful.")
        else:
            print("ExecutorPlugin: Error - Write failed.")
            # self.pm.hook.speak_text(text="指令执行失败")
