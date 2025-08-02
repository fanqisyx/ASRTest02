import pluggy
from pyModbusTCP.client import ModbusClient
import threading
import time

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class StateManagerPlugin:
    def __init__(self, pm):
        self.pm = pm
        self.client = None
        self.is_running = False
        self.thread = None
        self.last_status = None
        self.config = {} # Lazy loaded

    def _load_config_and_init_client(self):
        """Load config and initialize client if needed."""
        if not self.config:
            full_config = self.pm.hook.get_config()
            self.config = full_config.get("state_manager", {})
            server_config = full_config.get("servers", {})
            self.config.update(server_config) # Merge server settings

        host = self.config.get("modbus_host", "localhost")
        port = self.config.get("modbus_port", 502)

        if self.client is None or self.client.host != host or self.client.port != port:
            self.client = ModbusClient(host=host, port=port, auto_open=True)
            print(f"StateManagerPlugin: Initialized Modbus client for {host}:{port}")

    def _poll_loop(self):
        """The main loop for polling the robot's status."""
        self._load_config_and_init_client()

        status_register = self.config.get("status_register", 2000)
        poll_interval = self.config.get("poll_interval_seconds", 2)

        while self.is_running:
            try:
                if not self.client.is_open():
                    print("StateManagerPlugin: Modbus connection lost. Attempting to reconnect...")
                    self.client.open()
                    if not self.client.is_open():
                        time.sleep(poll_interval)
                        continue

                regs = self.client.read_holding_registers(status_register, 1)

                if regs:
                    current_status = regs[0]
                    if self.last_status is None:
                        self.last_status = current_status
                        print(f"StateManagerPlugin: Initial status read: {current_status}")
                    elif current_status != self.last_status:
                        print(f"StateManagerPlugin: Status changed from {self.last_status} to {current_status}")
                        self.last_status = current_status
                        self.pm.hook.on_status_changed(status={"register": status_register, "value": current_status})
                else:
                    print(f"StateManagerPlugin: Failed to read status register {status_register}.")

            except Exception as e:
                print(f"StateManagerPlugin: Error in poll loop: {e}")

            time.sleep(poll_interval)

    @hookimpl
    def start_listening(self):
        """Starts the polling thread."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._poll_loop)
            self.thread.daemon = True
            self.thread.start()
            print("StateManagerPlugin: Started polling for status updates.")

    @hookimpl
    def on_shutdown(self):
        """Stops the polling thread."""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            if self.client and self.client.is_open():
                self.client.close()
            print("StateManagerPlugin: Stopped polling.")
