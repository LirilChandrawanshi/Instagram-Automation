"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

interface AnalyticsChartsProps {
  tasksByType: Record<string, number>;
  tasksByStatus: Record<string, number>;
}

const COLORS = ["#c026d3", "#a21caf", "#86198f", "#e879f9", "#f5d0fe"];

export default function AnalyticsCharts({ tasksByType, tasksByStatus }: AnalyticsChartsProps) {
  const typeData = Object.entries(tasksByType).map(([name, value]) => ({ name, value }));
  const statusData = Object.entries(tasksByStatus).map(([name, value]) => ({ name, value }));

  return (
    <div className="mt-8 grid gap-8 lg:grid-cols-2">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-medium text-slate-900">Tasks by type</h3>
        <div className="mt-4 h-80">
          {typeData.length === 0 ? (
            <p className="flex h-full items-center justify-center text-slate-500">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#c026d3" radius={[4, 4, 0, 0]} name="Count" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-medium text-slate-900">Tasks by status</h3>
        <div className="mt-4 h-80">
          {statusData.length === 0 ? (
            <p className="flex h-full items-center justify-center text-slate-500">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
