import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { useIncidents } from '../../context/IncidentContext';

export const SeverityChart: React.FC = () => {
  const { incidents } = useIncidents();

  const highCount = incidents.filter((i) => i.severity === 'high').length;
  const mediumCount = incidents.filter((i) => i.severity === 'medium').length;
  const lowCount = incidents.filter((i) => i.severity === 'low').length;

  const data = [
    { name: 'High Severity', value: highCount || 1, color: '#EF4444' },
    { name: 'Medium Severity', value: mediumCount || 1, color: '#F59E0B' },
    { name: 'Low Severity', value: lowCount || 1, color: '#3B82F6' },
  ];

  return (
    <div className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 backdrop-blur-md shadow-xl flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300">Severity Distribution</h3>
          <p className="text-xs text-gray-400">Classification of detected highway incidents</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#111827" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                borderColor: '#374151',
                borderRadius: '0.75rem',
                color: '#F9FAFB',
                fontSize: '12px',
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => <span className="text-xs text-gray-300 font-medium">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
