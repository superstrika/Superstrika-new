import json
import os
import queue
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Console</title>
  <style>
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      background: #111;
      color: #ddd;
      font: 14px/1.4 monospace;
    }
    .shell {
      height: 100vh;
      padding: 12px;
    }
    .panel {
      display: flex;
      flex-direction: column;
      height: 100%;
      border: 1px solid #2c2c2c;
      border-radius: 8px;
      overflow: hidden;
      background: #161616;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid #2c2c2c;
      background: #1b1b1b;
      position: sticky;
      top: 0;
    }
    .title {
      font-weight: bold;
      color: #fff;
      margin-right: auto;
    }
    button {
      border: 1px solid #3f3f3f;
      background: #242424;
      color: #ddd;
      padding: 6px 10px;
      border-radius: 6px;
      cursor: pointer;
      font: inherit;
    }
    button:hover { background: #2f2f2f; }
    button:disabled {
      opacity: 0.6;
      cursor: wait;
    }
    .status {
      padding: 8px 12px;
      border-bottom: 1px solid #2c2c2c;
      color: #9ad;
      min-height: 38px;
    }
    .console {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      background: #111;
    }
    #log {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="panel">
      <div class="toolbar">
        <div class="title">Console</div>
        <button id="toggleButton" type="button">Stop</button>
        <button id="restartButton" type="button">Restart</button>
        <button id="clearButton" type="button">Clear Log</button>
      </div>
      <div id="status" class="status">Loading...</div>
      <div id="consoleBox" class="console">
        <pre id="log"></pre>
      </div>
    </div>
  </div>
  <script>
    const statusElement = document.getElementById("status");
    const logElement = document.getElementById("log");
    const consoleBox = document.getElementById("consoleBox");
    const toggleButton = document.getElementById("toggleButton");
    const restartButton = document.getElementById("restartButton");
    const clearButton = document.getElementById("clearButton");

    function scrollToBottom() {
      consoleBox.scrollTop = consoleBox.scrollHeight;
    }

    function setLog(lines) {
      logElement.textContent = lines.join("");
      scrollToBottom();
    }

    function appendLine(line) {
      logElement.textContent += line;
      scrollToBottom();
    }

    function clearLog() {
      logElement.textContent = "";
    }

    function renderStatus(data) {
      const exitText = data.returncode === null ? "n/a" : data.returncode;
      const pidText = data.pid === null ? "n/a" : data.pid;
      const errorText = data.error ? " | error: " + data.error : "";
      statusElement.textContent = "state: " + data.state + " | pid: " + pidText + " | exit: " + exitText + " | lines: " + data.line_count + errorText;
      const busy = data.state === "stopping" || data.state === "starting";
      toggleButton.textContent = data.state === "running" ? "Stop" : "Start";
      toggleButton.disabled = busy;
      restartButton.disabled = busy;
      clearButton.disabled = false;
    }

    async function postAction(path, button) {
      button.disabled = true;
      try {
        const response = await fetch(path, { method: "POST" });
        const data = await response.json();
        renderStatus(data);
      } catch (error) {
        statusElement.textContent = "request failed: " + error;
      } finally {
        button.disabled = false;
      }
    }

    toggleButton.addEventListener("click", () => {
      const path = toggleButton.textContent === "Stop" ? "/api/stop" : "/api/start";
      postAction(path, toggleButton);
    });
    restartButton.addEventListener("click", () => postAction("/api/restart", restartButton));
    clearButton.addEventListener("click", () => postAction("/api/clear", clearButton));

    fetch("/api/status")
      .then(response => response.json())
      .then(data => {
        renderStatus(data);
        setLog(data.lines || []);

        const events = new EventSource("/events");

        events.addEventListener("line", event => {
          appendLine(JSON.parse(event.data));
        });

        events.addEventListener("status", event => {
          renderStatus(JSON.parse(event.data));
        });

        events.addEventListener("clear", () => {
          clearLog();
        });

        events.onerror = () => {
          statusElement.textContent = "connection lost, reconnecting...";
        };
      })
      .catch(error => {
        statusElement.textContent = "failed to load: " + error;
      });
  </script>
</body>
</html>
"""


class ProcessManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
        self.log_path = (BASE_DIR / self.config.get("log_file", "console.log")).resolve()
        self.lines = []
        self.state = "idle"
        self.pid = None
        self.returncode = None
        self.error = None
        self.process = None
        self.subscribers = []
        self.run_id = 0
        self.lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.action_lock = threading.Lock()
        self._load_existing_log()

    def _load_config(self):
        with self.config_path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    def _load_existing_log(self):
        if not self.log_path.exists():
            return
        with self.log_path.open("r", encoding="utf-8", errors="replace") as log_file:
            self.lines = log_file.readlines()

    def start(self):
        with self.action_lock:
            return self._start_locked()

    def restart(self):
        with self.action_lock:
            self._stop_locked()
            return self._start_locked()

    def stop(self):
        with self.action_lock:
            self._stop_locked()
            with self.lock:
                self.returncode = None
                self.error = None
                if self.state != "failed":
                    self.state = "stopped"
                self.pid = None
                self.process = None
            self._broadcast_status()
            return self.get_status(include_lines=False)

    def clear(self):
        with self.lock:
            self.lines = []
        with self.log_lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.write_text("", encoding="utf-8")
        self._broadcast("clear", "")
        self._broadcast_status()
        return self.get_status(include_lines=False)

    def _start_locked(self):
        already_running = False
        with self.lock:
            already_running = self.process is not None and self.process.poll() is None
        if already_running:
            return self.get_status(include_lines=False)
        command = self._build_command()
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        with self.lock:
            self.state = "starting"
            self.error = None
            self.returncode = None
            self.pid = None
            self.run_id += 1
            run_id = self.run_id
        self._broadcast_status()

        try:
            process = subprocess.Popen(
                command,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
        except Exception as exc:
            with self.lock:
                self.process = None
                self.state = "failed"
                self.error = str(exc)
            self._broadcast_status()
            return self.get_status(include_lines=False)

        with self.lock:
            self.process = process
            self.pid = process.pid
            self.state = "running"
            self.error = None
        self._broadcast_status()

        threading.Thread(target=self._read_output, args=(process, run_id), name=f"console-reader-{run_id}", daemon=True).start()
        threading.Thread(target=self._watch_process, args=(process, run_id), name=f"console-watcher-{run_id}", daemon=True).start()
        return self.get_status(include_lines=False)

    def _stop_locked(self):
        with self.lock:
            process = self.process
            if process is None or process.poll() is not None:
                self.process = None
                if self.state in {"running", "starting", "stopping"}:
                    self.state = "stopped"
                self.pid = None
                return
            self.state = "stopping"
        self._broadcast_status()

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def _build_command(self):
        python_executable = self.config.get("python_executable") or sys.executable
        script_path = (BASE_DIR / self.config["script"]).resolve()
        args = self.config.get("args", [])
        return [python_executable, "-u", str(script_path), *args]

    def _append_line(self, line: str, run_id: int):
        with self.lock:
            if run_id != self.run_id:
                return
            self.lines.append(line)

        with self.log_lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(line)

        self._broadcast("line", line)
        self._broadcast_status()

    def _read_output(self, process: subprocess.Popen, run_id: int):
        if not process.stdout:
            return

        for line in process.stdout:
            self._append_line(line, run_id)

        process.stdout.close()

    def _watch_process(self, process: subprocess.Popen, run_id: int):
        returncode = process.wait()
        should_broadcast = False
        with self.lock:
            if process is self.process and run_id == self.run_id:
                self.returncode = returncode
                self.state = "exited"
                self.pid = None
                self.process = None
                self.error = None if returncode == 0 else self.error
                should_broadcast = True
        if should_broadcast:
            self._broadcast_status()

    def subscribe(self):
        subscriber = queue.Queue(maxsize=512)
        with self.lock:
            self.subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber):
        with self.lock:
            if subscriber in self.subscribers:
                self.subscribers.remove(subscriber)

    def _broadcast(self, event_type, payload):
        with self.lock:
            subscribers = list(self.subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait((event_type, payload))
            except queue.Full:
                continue

    def _broadcast_status(self):
        self._broadcast("status", json.dumps(self.get_status(include_lines=False)))

    def get_status(self, include_lines=True):
        with self.lock:
            lines = list(self.lines) if include_lines else None
            return {
                "state": self.state,
                "pid": self.pid,
                "returncode": self.returncode,
                "error": self.error,
                "lines": lines,
                "line_count": len(self.lines),
            }


manager = ProcessManager(CONFIG_PATH)


class ConsoleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html()
            return
        if parsed.path == "/api/status":
            self._send_json(manager.get_status(include_lines=True))
            return
        if parsed.path == "/events":
            self._stream_events()
            return
        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/start":
            self._send_json(manager.start())
            return
        if parsed.path == "/api/stop":
            self._send_json(manager.stop())
            return
        if parsed.path == "/api/restart":
            self._send_json(manager.restart())
            return
        if parsed.path == "/api/clear":
            self._send_json(manager.clear())
            return
        self.send_error(404)

    def _send_html(self):
        body = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _stream_events(self):
        subscriber = manager.subscribe()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            status_payload = json.dumps(manager.get_status(include_lines=False))
            self.wfile.write(f"event: status\ndata: {status_payload}\n\n".encode("utf-8"))
            self.wfile.flush()

            while True:
                try:
                    event_type, payload = subscriber.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue

                if event_type == "line":
                    safe_payload = json.dumps(payload)
                    self.wfile.write(f"event: line\ndata: {safe_payload}\n\n".encode("utf-8"))
                elif event_type == "clear":
                    self.wfile.write(b"event: clear\ndata: {}\n\n")
                else:
                    self.wfile.write(f"event: status\ndata: {payload}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            manager.unsubscribe(subscriber)

    def log_message(self, format, *args):
        return


def main():
    host = manager.config.get("host", "0.0.0.0")
    port = int(manager.config.get("port", 8080))
    manager.start()
    server = ThreadingHTTPServer((host, port), ConsoleHandler)
    print(f"Console server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
