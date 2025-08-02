import pluggy
import time
import sys
from .hooks import SpeechAIHooks
from .gui import run_gui, QueueIO, log_queue
from .plugins.nlp_plugin import NLPPlugin
from .plugins.executor_plugin import ExecutorPlugin
from .plugins.command_router_plugin import CommandRouterPlugin
from .plugins.script_executor_plugin import ScriptExecutorPlugin
from .plugins.tts_plugin import TTSPlugin
from .plugins.wakeword_plugin import WakeWordPlugin
from .plugins.asr_plugin import ASRPlugin
from .plugins.state_manager_plugin import StateManagerPlugin
from .plugins.status_handler_plugin import StatusHandlerPlugin

def get_plugin_manager():
    """Initializes and returns the plugin manager."""
    pm = pluggy.PluginManager("speech_ai_system")
    pm.add_hookspecs(SpeechAIHooks)
    return pm

def register_plugins(pm):
    """Registers all the system plugins."""
    # Register functional plugins
    pm.register(NLPPlugin())
    pm.register(ExecutorPlugin())
    pm.register(ScriptExecutorPlugin())
    pm.register(TTSPlugin())

    # Register background service plugins
    pm.register(WakeWordPlugin(pm=pm))
    pm.register(ASRPlugin(pm=pm))
    pm.register(StateManagerPlugin(pm=pm))
    pm.register(StatusHandlerPlugin(pm=pm))

    # The CommandRouterPlugin should be last to wrap other hooks
    pm.register(CommandRouterPlugin(pm=pm))

    return pm

def main():
    """Main application loop."""
    # This print statement goes to the actual console before stdout is redirected
    print("Starting Speech AI System...")
    print("A web-based GUI will be available at http://localhost:5001")

    # Redirect stdout to our log queue
    sys.stdout = QueueIO(log_queue)

    print("--- Initializing Speech AI System ---")
    pm = get_plugin_manager()
    register_plugins(pm)

    # Start the GUI in a background thread
    run_gui()

    # Call the hook to start all listening plugins
    pm.hook.start_listening()

    print("\n--- System Initialized. Listening for wake word... (Press Ctrl+C to exit) ---")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Shutting down ---")
    finally:
        # Call the shutdown hook for all plugins
        pm.hook.on_shutdown()
        print("--- System Shutdown Complete ---")

if __name__ == "__main__":
    main()
