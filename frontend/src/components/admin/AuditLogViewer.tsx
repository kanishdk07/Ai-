import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/adminApi';
import { AuditLog } from '../../types';
import { FileText, Search, CheckCircle2, XCircle, Shield } from 'lucide-react';

export const AuditLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [search, setSearch] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchLogs = async () => {
      setIsLoading(true);
      try {
        const res = await adminApi.getAuditLogs();
        setLogs(res.logs);
      } finally {
        setIsLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter(
    (l) =>
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.description?.toLowerCase().includes(search.toLowerCase()) ||
      l.username?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">Security & Administrative Audit Logs</h3>
            <p className="text-xs text-gray-400">Chronological ledger of overrides, settings updates, and dispatches</p>
          </div>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search action, user, log..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {filteredLogs.length === 0 ? (
        <p className="text-xs text-gray-500 py-6 text-center">No audit logs found matching query.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-gray-950 text-gray-400 uppercase text-[10px] font-bold border-b border-gray-800">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Endpoint / Resource</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-800/40 transition">
                  <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-bold text-white whitespace-nowrap">
                    {log.username || 'system'}
                  </td>
                  <td className="px-4 py-3 font-bold text-blue-400 whitespace-nowrap">{log.action}</td>
                  <td className="px-4 py-3 text-gray-300 truncate max-w-xs">{log.endpoint || log.resource_type || '-'}</td>
                  <td className="px-4 py-3 text-gray-300 font-sans">{log.description || '-'}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {log.success ? (
                      <span className="text-emerald-400 flex items-center gap-1 font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5" /> OK
                      </span>
                    ) : (
                      <span className="text-red-400 flex items-center gap-1 font-bold">
                        <XCircle className="w-3.5 h-3.5" /> FAIL
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
