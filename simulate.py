import time
import random
import requests

# URL do teu backend (Render ou local)
API_URL = "https://omnipulse-1ds1.onrender.com/api/metrics/"
API_KEY = "omnipulse-secret-key-change-me"

servers = ["linux-server-01", "mac-server-02"]

def simulate():
    print("Iniciando simulação de telemetria...")
    while True:
        for server in servers:
            # Gera valores aleatórios
            cpu = round(random.uniform(10.0, 90.0), 1)
            memory = round(random.uniform(20.0, 95.0), 1)
            network_in = round(random.uniform(10.0, 500.0), 1)
            network_out = round(random.uniform(10.0, 500.0), 1)

            payload = {
                "server": server,
                "cpu": cpu,
                "memory": memory,
                "network_in_kbps": network_in,
                "network_out_kbps": network_out
            }

            headers = {
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(API_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    print(f"[{server}] Enviado com sucesso: CPU {cpu}% | MEM {memory}%")
                else:
                    print(f"[{server}] Erro: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"[{server}] Falha na conexão: {e}")

        # Espera 2 segundos antes do próximo envio
        time.sleep(2)

if __name__ == "__main__":
    simulate()
    