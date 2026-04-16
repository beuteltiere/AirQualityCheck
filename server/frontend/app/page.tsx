"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

const API_BASE =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") + "/api";

type SensorActivity = {
  id: number;
  recorded_at: string;
  temperature: number;
  humidity: number;
};

type MotorActivity = {
  id: number;
  occurred_at: string;
  event_type: "OPEN" | "CLOSE";
};

type ExternalWeatherActivity = {
  id: number;
  fetched_at: string;
  temperature: number;
  humidity: number;
};

function fmt(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function fmtDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
  });
}

export default function ActivityPage() {
  const [sensorData, setSensorData] = useState<SensorActivity[]>([]);
  const [motorData, setMotorData] = useState<MotorActivity[]>([]);
  const [weatherData, setWeatherData] = useState<ExternalWeatherActivity[]>([]);

  const [loading, setLoading] = useState(false);
  const [lastFetched, setLastFetched] = useState<string | null>(null);

  const isFetchingRef = useRef(false);

  const fetchAll = useCallback(async () => {
    if (isFetchingRef.current) return;

    isFetchingRef.current = true;
    setLoading(true);

    const now = new Date();
    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);

    const params = `start=${encodeURIComponent(
      todayStart.toISOString()
    )}&end=${encodeURIComponent(now.toISOString())}`;

    try {
      const [s, m, w] = await Promise.all([
        fetch(`${API_BASE}/sensor_activity/?${params}`).then((r) => r.json()),
        fetch(`${API_BASE}/motor_activity/?${params}`).then((r) => r.json()),
        fetch(`${API_BASE}/external_weather_activity/?${params}`).then((r) =>
          r.json()
        ),
      ]);

      const sortDesc = (arr: any[], key: string) =>
        (arr ?? []).sort(
          (a, b) =>
            new Date(b[key]).getTime() - new Date(a[key]).getTime()
        );

      setSensorData(sortDesc(s, "recorded_at"));
      setMotorData(sortDesc(m, "occurred_at"));
      setWeatherData(sortDesc(w, "fetched_at"));

      setLastFetched(new Date().toLocaleTimeString());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, []);

  const sendCommand = async (value: 360 | -360) => {
    try {
      await fetch(`${API_BASE}/motor/command/${value}`, {
        method: "POST",
      });
      setTimeout(fetchAll, 500);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    const interval = setInterval(async () => {
      if (isFetchingRef.current) return;
      await fetchAll();
    }, 15000);

    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Activity Monitor
          </h1>
          <p className="text-xs text-muted-foreground uppercase tracking-widest">
            Today · Sensor · Motor · External Weather
          </p>
        </div>

        <div className="flex gap-2">
          <Button type="button" onClick={() => sendCommand(360)}>
            Open
          </Button>
          <Button
            type="button"
            onClick={() => sendCommand(-360)}
            variant="secondary"
          >
            Close
          </Button>
          <Button type="button" onClick={fetchAll} disabled={loading}>
            {loading ? "Loading…" : "Refresh"}
          </Button>
        </div>
      </div>

      <div className="flex gap-6 text-xs text-muted-foreground border-b pb-2">
        <span>Sensor <b>{sensorData.length}</b></span>
        <span>Motor <b>{motorData.length}</b></span>
        <span>Weather <b>{weatherData.length}</b></span>

        {lastFetched && (
          <span className="ml-auto">
            Last fetched <b>{lastFetched}</b>
          </span>
        )}
      </div>

      <div className="grid md:grid-cols-3 gap-4 h-[70vh]">
        <ActivityColumn
          title="Sensor Activity"
          data={sensorData}
          loading={loading}
          getDate={(r) => r.recorded_at}
          renderRow={(row) => (
            <div className="grid grid-cols-3 text-sm">
              <span className="text-muted-foreground">
                {fmt(row.recorded_at)}
              </span>
              <span>{row.temperature.toFixed(1)}°C</span>
              <span>{row.humidity.toFixed(1)}%</span>
            </div>
          )}
        />

        <ActivityColumn
          title="Motor Activity"
          data={motorData}
          loading={loading}
          getDate={(r) => r.occurred_at}
          renderRow={(row) => (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                {fmt(row.occurred_at)}
              </span>
              <span className="font-medium">{row.event_type}</span>
            </div>
          )}
        />

        <ActivityColumn
          title="External Weather"
          data={weatherData}
          loading={loading}
          getDate={(r) => r.fetched_at}
          renderRow={(row) => (
            <div className="grid grid-cols-3 text-sm">
              <span className="text-muted-foreground">
                {fmt(row.fetched_at)}
              </span>
              <span>{row.temperature.toFixed(1)}°C</span>
              <span>{row.humidity.toFixed(1)}%</span>
            </div>
          )}
        />
      </div>
    </div>
  );
}

function ActivityColumn({
  title,
  data,
  loading,
  renderRow,
  getDate,
}: {
  title: string;
  data: Array<{ id: number }>;
  loading: boolean;
  renderRow: (row: any) => React.ReactNode;
  getDate: (row: any) => string;
}) {
  return (
    <Card className="flex flex-col h-full">
      <CardHeader>
        <div className="flex justify-between text-sm font-medium">
          <span>{title}</span>
          <span className="text-muted-foreground">{data.length} rows</span>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-4">
          {loading && (
            <div className="text-center py-6 text-sm text-muted-foreground">
              Fetching…
            </div>
          )}

          {!loading && data.length === 0 && (
            <div className="text-center py-6 text-sm text-muted-foreground">
              No data
            </div>
          )}

          {!loading &&
            data.map((row: any, i: number) => {
              const showDate =
                i === 0 ||
                fmtDate(getDate(row)) !== fmtDate(getDate(data[i - 1]));

              return (
                <div key={row.id}>
                  {showDate && (
                    <div className="text-xs text-muted-foreground py-2 sticky top-0 bg-background">
                      {fmtDate(getDate(row))}
                    </div>
                  )}
                  <div className="py-2 border-b">{renderRow(row)}</div>
                </div>
              );
            })}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}