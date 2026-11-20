import time
import socket
import requests
import psutil

# O URL do teu backend no Render
API_URL = "https://omnipulse-1ds1.onrender.com/api/metrics/"
API_KEY = "omnipulse-secret-key-change-me"
HOSTNAME = socket.gethostname()

print(f"[Agent] Starting. Reporting as: {HOSTNAME}")

while True:
    payload = {
        "server": HOSTNAME,
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent,
        "network_in_kbps": round(psutil.net_io_counters().bytes_recv / 1024, 2),
        "network_out_kbps": round(psutil.net_io_counters().bytes_sent / 1024, 2),
        "timestamp": time.time(),
    }

    try:
        r = requests.post(API_URL, json=payload, headers={"X-API-Key": API_KEY}, timeout=10)
        print(f"[Agent] {payload['server']} | CPU={payload['cpu']}% | MEM={payload['memory']}% | Status={r.status_code}")
    except Exception as e:
        print(f"[Agent] Error: {e}")

    time.sleep(2)
    