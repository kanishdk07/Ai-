import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

const mockTimelineData = [
  { time: '00:00', detected: 1, resolved: 1 },
  { time: '03:00', detected: 0, resolved: 0 },
  { time: '06:00', detected: 2, resolved: 1 },
  { time: '09:00', detected: 4, resolved: 3 },
  { time: '12:00', detected: 3, resolved: 2 },
  { time: '15:00', detected: 5, resolved: 4 },
  { time: '18:00', detected: 6, resolved: 5 },
  { time: '21:00', detected: 2, resolved: 2 },
];

export const IncidentTimelineChart: React.FC = () => {
  return (
    <div className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 backdrop-blur-md shadow-xl flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300">Incident Detection Velocity</h3>
          <p className="text-xs text-gray-400">24-hour crash event timeline and resolution rate</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={mockTimelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorDetected" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
            <XAxis dataKey="time" stroke="#6B7280" fontSize={11} tickLine={false} />
            <YAxis stroke="#6B7280" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                borderColor: '#374151',
                borderRadius: '0.75rem',
                color: '#F9FAFB',
                fontSize: '12px',
              }}
            />
            <Area
              type="monotone"
              dataKey="detected"
              name="Detected Crashes"
              stroke="#EF4444"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorDetected)"
            />
            <Area
              type="monotone"
              dataKey="resolved"
              name="Resolved Incidents"
              stroke="#10B981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorResolved)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
