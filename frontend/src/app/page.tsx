"use client";

import { useState, useEffect, useRef } from "react";
import { useMetricsStream } from "@/hooks/useMetricsStream";
import { 
  Activity, Server, Wifi, WifiOff, Cpu, MemoryStick, 
  ArrowDownToLine, Sun, Moon 
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface HistoryPoint {
  timestamp: number;
  cpu: number;
  memory: number;
}

export default function Dashboard() {
  const { isConnected, metrics } = useMetricsStream();
  const [isDark, setIsDark] = useState(true);
  const [history, setHistory] = useState<Record<string, HistoryPoint[]>>({});
  const [hasFetchedHistory, setHasFetchedHistory] = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark]);

  useEffect(() => {
    const servers = Object.keys(metrics);
    if (servers.length > 0 && !hasFetchedHistory) {
      const server = servers[0];
      fetch(`https://omnipulse-1ds1.onrender.com/api/history/?server=${server}&minutes=60`)
        .then((res) => res.json())
        .then((data) => {
          if (data.data) {
            const formatted = data.data.map((d: any) => ({
              timestamp: d.timestamp,
              cpu: d.cpu,
              memory: d.memory,
            }));
            setHistory({ [server]: formatted });
          }
        })
        .catch((err) => console.error("History fetch failed:", err));
      setHasFetchedHistory(true);
    }
  }, [metrics, hasFetchedHistory]);

  const servers = Object.keys(metrics);
  const totalServers = servers.length;

  const getCombinedData = (server: string) => {
    const historyData = history[server] || [];
    const liveData = metrics[server] || [];
    const combined = [...historyData];
    liveData.forEach((point) => {
      if (!combined.some((p) => p.timestamp === point.timestamp)) {
        combined.push({
          timestamp: point.timestamp,
          cpu: point.cpu,
          memory: point.memory,
        });
      }
    });
    return combined.sort((a, b) => a.timestamp - b.timestamp);
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 p-6 font-sans transition-colors duration-300">
      <header className="flex items-center justify-between mb-8 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-3">
          <Activity className="text-emerald-600 dark:text-emerald-500 w-8 h-8" />
          <h1 className="text-2xl font-bold tracking-tight">OmniPulse</h1>
          <span className="text-xs font-medium bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 px-2 py-1 rounded-full uppercase tracking-wider">
            Infrastructure Monitor
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsDark(!isDark)}
            className="p-2 rounded-lg bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
            aria-label="Toggle theme"
          >
            {isDark ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-zinc-600" />}
          </button>

          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${isConnected ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20"}`}>
            {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            {isConnected ? "Live Connection" : "Disconnected"}
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Active Servers" value={totalServers.toString()} icon={<Server className="w-5 h-5 text-blue-600 dark:text-blue-400" />} />
        <StatCard title="Avg CPU Load" value={`${(metrics[servers[0]]?.slice(-1)[0]?.cpu || 0).toFixed(1)}%`} icon={<Cpu className="w-5 h-5 text-amber-600 dark:text-amber-400" />} />
        <StatCard title="Avg Memory" value={`${(metrics[servers[0]]?.slice(-1)[0]?.memory || 0).toFixed(1)}%`} icon={<MemoryStick className="w-5 h-5 text-purple-600 dark:text-purple-400" />} />
        <StatCard title="Total Network" value={`${(metrics[servers[0]]?.slice(-1)[0]?.network_in_kbps || 0).toFixed(1)} MB/s`} icon={<ArrowDownToLine className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />} />
      </div>

      <div className="grid grid-cols-1 gap-6">
        {servers.length === 0 ? (
          <div className="col-span-full h-64 flex flex-col items-center justify-center text-zinc-500 border border-dashed border-zinc-300 dark:border-zinc-800 rounded-xl bg-zinc-100 dark:bg-zinc-900/50 transition-colors">
            <Activity className="w-10 h-10 mb-4 animate-pulse text-zinc-400 dark:text-zinc-500" />
            <p>Waiting for incoming telemetry...</p>
          </div>
        ) : (
          servers.map((server) => (
            <ServerChart key={server} serverName={server} data={getCombinedData(server)} isDark={isDark} />
          ))
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 flex items-center justify-between shadow-sm dark:shadow-none transition-colors">
      <div>
        <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400 mb-1">{title}</p>
        <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">{value}</p>
      </div>
      <div className="p-3 bg-zinc-100 dark:bg-zinc-800/50 rounded-lg">{icon}</div>
    </div>
  );
}

function ServerChart({ serverName, data, isDark }: { serverName: string; data: any[]; isDark: boolean }) {
  const gridColor = isDark ? "#27272a" : "#e4e4e7";
  const axisColor = isDark ? "#52525b" : "#a1a1aa";
  const tooltipBg = isDark ? "#18181b" : "#ffffff";
  const tooltipBorder = isDark ? "#27272a" : "#e4e4e7";
  const tooltipText = isDark ? "#e4e4e7" : "#18181b";

  const chartRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);

  const chartWidth = Math.max(data.length * 40, 1500);
  const containerWidth = 800; // Largura "visível" base

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!chartRef.current) return;
    setIsDragging(true);
    setStartX(e.pageX - chartRef.current.offsetLeft);
    setScrollLeft(chartRef.current.scrollLeft);
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !chartRef.current) return;
    e.preventDefault();
    const x = e.pageX - chartRef.current.offsetLeft;
    const walk = (x - startX) * 1.5; // Multiplicador de velocidade
    chartRef.current.scrollLeft = scrollLeft - walk;
  };

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 shadow-sm dark:shadow-none transition-colors">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2 text-zinc-800 dark:text-zinc-100">
          <Server className="w-4 h-4 text-zinc-500 dark:text-zinc-400" />
          {serverName}
        </h2>
        <div className="flex gap-4 text-xs font-medium">
          <span className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
            <div className="w-2 h-2 rounded-full bg-blue-500" /> CPU
          </span>
          <span className="flex items-center gap-1.5 text-purple-600 dark:text-purple-400">
            <div className="w-2 h-2 rounded-full bg-purple-500" /> Memory
          </span>
        </div>
      </div>

      <div 
        ref={chartRef}
        className={`w-full overflow-x-hidden overflow-y-hidden relative ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        onMouseDown={handleMouseDown}
        onMouseLeave={handleMouseLeave}
        onMouseUp={handleMouseUp}
        onMouseMove={handleMouseMove}
      >
        <div style={{ width: chartWidth, height: '350px' }}>
          <ResponsiveContainer width={chartWidth} height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(tick) => new Date(tick * 1000).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })} 
                stroke={axisColor} 
                fontSize={12} 
                tickMargin={10}
                minTickGap={40}
              />
              <YAxis 
                stroke={axisColor} 
                fontSize={12} 
                tickFormatter={(val) => `${val}%`} 
                domain={[0, 100]} 
                tickMargin={10}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: '8px', color: tooltipText }}
                itemStyle={{ color: tooltipText }}
                labelFormatter={(label) => {
                  const timestamp = typeof label === 'number' ? label : Number(label);
                  return isNaN(timestamp) ? '' : new Date(timestamp * 1000).toLocaleTimeString();
                }}
                formatter={(value) => {
                  const numValue = typeof value === 'number' ? value : Number(value);
                  return [`${numValue.toFixed(2)}%`];
                }}
                cursor={{ stroke: axisColor, strokeWidth: 1, strokeDasharray: '3 3' }}
              />
              <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="memory" stroke="#a855f7" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <p className="text-xs text-center text-zinc-500 mt-4">Arraste o gráfico para navegar no histórico.</p>
    </div>
  );
}
