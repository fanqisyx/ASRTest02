import pluggy
from pyModbusTCP.client import ModbusClient

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class ExecutorPlugin:
    """A plugin for command execution via ModbusTCP."""

    def __init__(self, pm):
        self.pm = pm
        self.client = None
        self.config = {} # Will be loaded lazily

    def _initialize_client(self):
        """Initializes the Modbus client using config."""
        # Load config only when needed
        if not self.config:
            full_config = self.pm.hook.get_config()
            self.config = full_config.get("servers", {})

        host = self.config.get("modbus_host", "localhost")
        port = self.config.get("modbus_port", 502)

        # Initialize client if not already done
        if self.client is None or self.client.host != host or self.client.port != port:
            self.client = ModbusClient(host=host, port=port, auto_open=True, auto_close=True)
            print(f"ExecutorPlugin: Initialized Modbus client for {host}:{port}")

    @hookimpl
    def execute_command(self, command_config: dict, command_data: dict):
        """Executes a specific robot action based on the command config."""
        self._initialize_client()

        action = command_config.get("action")
        print(f"ExecutorPlugin: Received action '{action}' with data {command_data}")

        if not self.client.is_open():
            print(f"ExecutorPlugin: Error - could not connect to Modbus server.")
            return

        try:
            if action == "write_register":
                self._handle_write_register(command_config, command_data)
            else:
                print(f"ExecutorPlugin: Error - Unknown action '{action}'")

        except Exception as e:
            print(f"ExecutorPlugin: An error occurred during Modbus communication: {e}")

    def _handle_write_register(self, command_config: dict, command_data: dict):
        """Handles the 'write_register' action."""
        params = command_config.get("params", {})
        register_addr = params.get("register")
        value_template = params.get("value")

        if register_addr is None or value_template is None:
            print("ExecutorPlugin: Error - 'register' and 'value' must be defined in config for write_register.")
            return

        try:
            full_config = self.pm.hook.get_config()
            location_map = full_config.get("executor", {}).get("location_to_register_value", {})

            final_value_str = value_template.format(**command_data.get("params", {}))

            if final_value_str in location_map:
                final_value = location_map[final_value_str]
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
