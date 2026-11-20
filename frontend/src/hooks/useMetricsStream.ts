"use client";

import { useEffect, useRef, useState } from "react";

export interface MetricSample {
  server: string;
  cpu: number;
  memory: number;
  network_in_kbps: number;
  network_out_kbps: number;
  timestamp: number;
}

export interface MetricsBatch {
  type: string;
  timestamp: number;
  samples: MetricSample[];
}

const WS_URL = "ws://127.0.0.1:8000/ws/metrics/";
const MAX_POINTS_PER_SERVER = 30;

export function useMetricsStream() {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<Record<string, MetricSample[]>>({});
  
  const bufferRef = useRef<MetricSample[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const batch: MetricsBatch = JSON.parse(event.data);
        if (batch.type === "metrics_batch" && batch.samples) {
          bufferRef.current.push(...batch.samples);
        }
      } catch (err) {
        console.error("[OmniPulse] Failed to parse WebSocket message:", err);
      }
    };

    let animationFrameId: number;

    const updateUI = () => {
      if (bufferRef.current.length > 0) {
        const newSamples = bufferRef.current;
        bufferRef.current = [];

        setMetrics((prev) => {
          const nextState = { ...prev };

          for (const sample of newSamples) {
            const serverHistory = [...(nextState[sample.server] || [])];
            serverHistory.push(sample);

            if (serverHistory.length > MAX_POINTS_PER_SERVER) {
              serverHistory.shift();
            }
            
            nextState[sample.server] = serverHistory;
          }

          return nextState;
        });
      }

      animationFrameId = requestAnimationFrame(updateUI);
    };

    animationFrameId = requestAnimationFrame(updateUI);

    return () => {
      cancelAnimationFrame(animationFrameId);
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, []);

  return { isConnected, metrics };
}
