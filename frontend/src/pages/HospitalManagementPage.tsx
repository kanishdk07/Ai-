import React, { useState } from 'react';
import { HospitalList } from '../components/hospitals/HospitalList';
import { ManualContactForm } from '../components/hospitals/ManualContactForm';
import { Building2, Phone } from 'lucide-react';

export const HospitalManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'directory' | 'manual'>('directory');

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Tab Switcher */}
      <div className="flex items-center gap-2 p-1.5 bg-gray-900 border border-gray-800 rounded-2xl w-fit">
        <button
          onClick={() => setActiveTab('directory')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'directory'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Hospital Directory & Providers
        </button>

        <button
          onClick={() => setActiveTab('manual')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'manual'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Phone className="w-4 h-4" />
          Manual Emergency Dispatch Form
        </button>
      </div>

      {activeTab === 'directory' ? <HospitalList /> : <ManualContactForm />}
    </div>
  );
};
