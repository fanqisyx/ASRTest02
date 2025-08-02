import queue
import threading
from flask import Flask, render_template, jsonify

# A thread-safe queue to hold log messages
log_queue = queue.Queue()

app = Flask(__name__)

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
            break # Should not happen, but for safety
    return jsonify(logs)

def run_gui():
    """Runs the Flask app in a separate thread."""
    def run_app():
        # Running with debug=False and without reloader is important for threaded mode
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()
    print("GUI: Flask server is running in a background thread on http://localhost:5001")

# This class can be used to redirect stdout to the queue
class QueueIO:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        # Don't write empty lines to the log
        if s.strip():
            self.q.put(s)

    def flush(self):
        pass # The queue doesn't need flushing
