import pluggy
from pyModbusTCP.client import ModbusClient
import threading
import time

hookimpl = pluggy.HookimplMarker("speech_ai_system")

# --- Configuration ---
MODBUS_HOST = "localhost"
MODBUS_PORT = 502
STATUS_REGISTER = 2000
POLL_INTERVAL = 2 # seconds

class StateManagerPlugin:
    def __init__(self, pm):
        self.pm = pm
        self.client = ModbusClient(host=MODBUS_HOST, port=MODBUS_PORT, auto_open=True)
        self.is_running = False
        self.thread = None
        self.last_status = None

    def _poll_loop(self):
        """The main loop for polling the robot's status."""
        while self.is_running:
            try:
                if not self.client.is_open():
                    print("StateManagerPlugin: Modbus connection lost. Attempting to reconnect...")
                    self.client.open()
                    # Wait a bit before retrying after a failed open
                    if not self.client.is_open():
                        time.sleep(POLL_INTERVAL)
                        continue

                # Read the status register
                regs = self.client.read_holding_registers(STATUS_REGISTER, 1)

                if regs:
                    current_status = regs[0]
                    if self.last_status is None:
                        self.last_status = current_status
                        print(f"StateManagerPlugin: Initial status read: {current_status}")
                    elif current_status != self.last_status:
                        print(f"StateManagerPlugin: Status changed from {self.last_status} to {current_status}")
                        self.last_status = current_status
                        # Trigger the hook with the new status
                        self.pm.hook.on_status_changed(status={"register": STATUS_REGISTER, "value": current_status})
                else:
                    print("StateManagerPlugin: Failed to read status register.")

            except Exception as e:
                print(f"StateManagerPlugin: Error in poll loop: {e}")

            time.sleep(POLL_INTERVAL)

    @hookimpl
    def start_listening(self): # Piggyback on the existing start hook
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
            if self.client.is_open():
                self.client.close()
            print("StateManagerPlugin: Stopped polling.")
