import React from 'react';
import { NotificationQueue } from '../components/notifications/NotificationQueue';
import { BellRing } from 'lucide-react';

export const NotificationControlPage: React.FC = () => {
  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <BellRing className="w-5 h-5 text-purple-400" />
            <h1 className="text-xl font-extrabold text-white tracking-wide">
              Emergency Notification Procedures & Live Queue
            </h1>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Monitor active SMS/Call retry cycles, countdown schedules, and hospital acknowledgment responses
          </p>
        </div>
      </div>

      <NotificationQueue />
    </div>
  );
};
