import pluggy
from .hooks import SpeechAIHooks
from .plugins.nlp_plugin import NLPPlugin
from .plugins.executor_plugin import ExecutorPlugin
from .plugins.command_router_plugin import CommandRouterPlugin
from .plugins.script_executor_plugin import ScriptExecutorPlugin

def get_plugin_manager():
    """Initializes and returns the plugin manager."""
    pm = pluggy.PluginManager("speech_ai_system")
    pm.add_hookspecs(SpeechAIHooks)
    return pm

def register_plugins(pm):
    """Registers all the system plugins."""
    pm.register(NLPPlugin())
    pm.register(ExecutorPlugin())
    pm.register(ScriptExecutorPlugin())
    # The CommandRouterPlugin needs the plugin manager instance to call other hooks.
    # We use a hookwrapper, so its registration order relative to the wrapped hook is important.
    # Pluggy ensures wrappers execute around the non-wrapper implementations.
    pm.register(CommandRouterPlugin(pm=pm))
    return pm

def main():
    """Main application loop."""
    print("--- Initializing Speech AI System ---")
    pm = get_plugin_manager()
    register_plugins(pm)

    print("\n--- System Initialized. Starting Simulation ---")

    # --- Test Case 1: Route to ModbusExecutor ---
    print("\n--- Test Case 1: ASR Result '小车小车，去A点' ---")
    asr_text_1 = "小车小车，去A点"
    # Calling the hook will trigger the entire chain:
    # CommandRouterPlugin(wrapper start) -> NLPPlugin -> CommandRouterPlugin(wrapper end) -> ExecutorPlugin
    pm.hook.process_asr_result(text=asr_text_1)

    print("\n" + "="*40 + "\n")

    # --- Test Case 2: Route to ScriptExecutor ---
    print("--- Test Case 2: ASR Result '机器人，开始运输' ---")
    asr_text_2 = "机器人，开始运输"
    # Calling the hook for the second case
    pm.hook.process_asr_result(text=asr_text_2)

    print("\n--- Simulation Finished ---")

if __name__ == "__main__":
    main()
