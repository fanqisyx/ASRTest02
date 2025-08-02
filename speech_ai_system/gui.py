import queue
import threading
from flask import Flask, render_template, jsonify, request

# A thread-safe queue to hold log messages
log_queue = queue.Queue()

app = Flask(__name__)
pm = None # Will be set by the main application

@app.route('/')
def index():
    """Serve the main GUI page."""
    return render_template('index.html')

@app.route('/logs')
def get_logs():
    """API endpoint to get logs from the queue."""
    logs = []
    while not log_queue.empty():
        try:
            logs.append(log_queue.get_nowait())
        except queue.Empty:
            break
    return jsonify(logs)

@app.route('/api/config', methods=['GET'])
def get_config_api():
    """API endpoint to get the current configuration."""
    if not pm:
        return jsonify({"error": "Plugin manager not available"}), 500
    config = pm.hook.get_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def save_config_api():
    """API endpoint to save the configuration."""
    if not pm:
        return jsonify({"error": "Plugin manager not available"}), 500

    new_config = request.json
    if not new_config:
        return jsonify({"error": "No JSON data provided"}), 400

    pm.hook.save_config(config_data=new_config)
    return jsonify({"status": "success", "message": "Configuration saved."})

def run_gui(plugin_manager):
    """Runs the Flask app in a separate thread."""
    global pm
    pm = plugin_manager

    def run_app():
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()
    print("GUI: Flask server is running in a background thread on http://localhost:5001")

class QueueIO:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s.strip():
            self.q.put(s)

    def flush(self):
        pass
