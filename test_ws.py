"""
WebSocket smoke test for OmniPulse.

Connects to the local Channels endpoint and prints the first three
batched metric frames received. Used to verify that the consumer is
producing and flushing data correctly before building the frontend.
"""

import asyncio
import json

import websockets


async def test_connection() -> None:
    uri = "ws://127.0.0.1:8000/ws/metrics/"
    print(f"Connecting to {uri} ...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected. Waiting for batches...\n")

            # We only need to inspect the first three frames to confirm
            # batching is working (one frame per second, 4 samples each).
            for frame_index in range(1, 4):
                message = await websocket.recv()
                payload = json.loads(message)

                timestamp = payload.get("timestamp")
                samples = payload.get("samples", [])

                print(f"--- Batch #{frame_index} | ts={timestamp:.2f} ---")
                print(f"Samples in batch: {len(samples)}")

                for sample in samples:
                    print(
                        f"  {sample['server']:<18} "
                        f"CPU={sample['cpu']:>5.2f}%  "
                        f"MEM={sample['memory']:>5.2f}%  "
                        f"NET_IN={sample['network_in_kbps']:>8.2f}kb/s"
                    )
                print()

            print("Test complete. Closing connection.")

    except ConnectionRefusedError:
        print(
            "ERROR: Could not connect. Is the Django server running "
            "on http://127.0.0.1:8000 ?"
        )
    except Exception as exc:
        print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    asyncio.run(test_connection())
    