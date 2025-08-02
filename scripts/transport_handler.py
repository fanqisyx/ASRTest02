import sys
import json

def handle_transport(params):
    """
    A simple handler for a transport task.
    It receives parameters, performs a mock action, and returns a result.
    """
    item = params.get("item", "nothing")
    destination = params.get("destination", "nowhere")

    print(f"Transport Handler Script: Received task to transport '{item}' to '{destination}'.", file=sys.stderr)

    # Mocking some work
    print("Transport Handler Script: Work complete.", file=sys.stderr)

    # Return a result as a JSON string to stdout
    result = {
        "status": "success",
        "message": f"Successfully transported {item} to {destination}."
    }
    return result

if __name__ == "__main__":
    # The ScriptExecutorPlugin captures stdout for its return value,
    # so we use stderr for logging within the script itself.
    if len(sys.argv) > 1:
        try:
            input_params = json.loads(sys.argv[1])
            output = handle_transport(input_params)
            print(json.dumps(output)) # This goes to stdout for the plugin to capture
        except json.JSONDecodeError:
            error_msg = {"status": "error", "message": "Invalid JSON parameters provided."}
            print(json.dumps(error_msg))
            sys.exit(1)
    else:
        error_msg = {"status": "error", "message": "No parameters provided to script."}
        print(json.dumps(error_msg))
        sys.exit(1)
