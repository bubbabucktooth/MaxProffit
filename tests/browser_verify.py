"""Isolated local frontend verification using installed Chrome, no user profile."""
import base64
import json
import os
import shutil
from pathlib import Path
import subprocess
import time
import sys
import urllib.request
from websockets.sync.client import connect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / ".verification"
ROOT.mkdir(exist_ok=True)
candidates = [
    os.environ.get("MAXPROFFIT_CHROME"),
    shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chrome"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
chrome = next((Path(candidate) for candidate in candidates if candidate and Path(candidate).is_file()), None)
if chrome is None:
    raise SystemExit("Install Chrome/Chromium or set MAXPROFFIT_CHROME to its executable path")
profile = ROOT / f"chrome-profile-{time.time_ns()}"
process = subprocess.Popen([
    str(chrome), "--headless=new", "--disable-gpu", "--no-first-run",
    "--no-default-browser-check", "--disable-background-networking",
    "--remote-debugging-port=0", f"--user-data-dir={profile}", "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ws = None
try:
    deadline = time.monotonic() + 20
    port_file = profile / "DevToolsActivePort"
    while not port_file.exists():
        if time.monotonic() > deadline:
            raise RuntimeError("Chrome did not start")
        time.sleep(.2)
    port = int(port_file.read_text().splitlines()[0])
    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
    target = next(t for t in targets if t["type"] == "page")
    ws = connect(target["webSocketDebuggerUrl"], max_size=30_000_000, proxy=None, legacy=True)
    seq = 0
    errors = []

    def cdp(method, params=None):
        global seq
        seq += 1
        ws.send(json.dumps({"id": seq, "method": method, "params": params or {}}))
        while True:
            response = json.loads(ws.recv(timeout=20))
            if response.get("method") == "Runtime.exceptionThrown":
                errors.append(response["params"])
            if response.get("id") == seq:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response.get("result", {})

    def evaluate(js):
        result = cdp("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"])
        return result.get("result", {}).get("value")

    cdp("Runtime.enable")
    cdp("Page.enable")
    cdp("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
    cdp("Page.navigate", {"url": "http://127.0.0.1:8501"})
    deadline = time.monotonic() + 30
    ready = """(() => {const f = document.querySelector('iframe'); return !!f?.contentDocument?.querySelector('.coach-svg');})()"""
    while not evaluate(ready):
        if time.monotonic() > deadline:
            raise RuntimeError("Component did not mount: " + str(evaluate("document.body.innerText")))
        time.sleep(.25)
    evaluate("window.reviewDoc = document.querySelector('iframe').contentDocument; window.reviewDoc.reviewToken = 123")

    def check_layout(label):
        data = evaluate("""(() => {
          const f = document.querySelector('iframe'), d = f.contentDocument;
          const r = f.getBoundingClientRect(), s = d.querySelector('.stage').getBoundingClientRect();
          const figure = d.querySelector('.coach-svg').getBoundingClientRect();
          return {frame:{x:r.x,y:r.y,w:r.width,h:r.height}, stage:{w:s.width,h:s.height},
            viewport:{w:innerWidth,h:innerHeight}, figure:{x:figure.x,y:figure.y,w:figure.width,h:figure.height},
            bodyScroll:document.documentElement.scrollHeight, text:d.body.innerText};
        })()""")
        print(label, json.dumps(data))
        assert abs(data["frame"]["h"] - data["viewport"]["h"]) <= 2, data
        assert data["frame"]["y"] <= 2, data
        assert data["bodyScroll"] <= data["viewport"]["h"] + 2, data
        assert data["figure"]["h"] > data["viewport"]["h"] * .5, data
        screenshot = cdp("Page.captureScreenshot", {"format": "png"})
        (ROOT / f"{label}.png").write_bytes(base64.b64decode(screenshot["data"]))

    if '--typography' in sys.argv:
        from typography_checks import run
    elif '--preview' in sys.argv:
        from record_finale import run
    else:
        from finale_checks import run
    run(cdp, evaluate, check_layout, ROOT)
    assert not errors, errors

finally:
    if ws:
        try:
            ws.send(json.dumps({"id":999,"method":"Browser.close"}))
        except Exception:
            pass
        ws.close()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
