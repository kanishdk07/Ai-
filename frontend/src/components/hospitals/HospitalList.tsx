import React, { useState, useEffect } from 'react';
import { Hospital } from '../../types';
import { hospitalApi } from '../../api/hospitalApi';
import { AddHospitalModal } from './AddHospitalModal';
import { useAuth } from '../../context/AuthContext';
import {
  Building2,
  Plus,
  Search,
  Phone,
  Mail,
  MapPin,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Ambulance,
} from 'lucide-react';

export const HospitalList: React.FC = () => {
  const { isAdmin } = useAuth();
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [search, setSearch] = useState<string>('');
  const [filterTrauma, setFilterTrauma] = useState<boolean>(false);
  const [filterAmbulance, setFilterAmbulance] = useState<boolean>(false);
  const [isAddOpen, setIsAddOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchHospitals = async () => {
      setIsLoading(true);
      try {
        const res = await hospitalApi.getHospitals();
        setHospitals(res.hospitals);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHospitals();
  }, []);

  const filteredHospitals = hospitals.filter((h) => {
    const matchSearch =
      h.name.toLowerCase().includes(search.toLowerCase()) ||
      h.address.toLowerCase().includes(search.toLowerCase()) ||
      h.phone_numbers.some((p) => p.includes(search));

    if (!matchSearch) return false;
    if (filterTrauma && !h.has_trauma_center) return false;
    if (filterAmbulance && !h.has_ambulance) return false;
    return true;
  });

  return (
    <div className="space-y-5">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Emergency Hospital Registry</h2>
          <p className="text-xs text-gray-400">
            Registered regional trauma centers and rapid-response emergency clinics
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => setIsAddOpen(true)}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition flex-shrink-0"
          >
            <Plus className="w-4 h-4" />
            Add Hospital
          </button>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search hospitals by name, area, phone number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900/90 border border-gray-800 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilterTrauma(!filterTrauma)}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border ${
              filterTrauma
                ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                : 'bg-gray-900 border-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Level 1 Trauma Center
          </button>

          <button
            onClick={() => setFilterAmbulance(!filterAmbulance)}
            className={`px-3 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border ${
              filterAmbulance
                ? 'bg-blue-950 border-blue-500 text-blue-400'
                : 'bg-gray-900 border-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <Ambulance className="w-3.5 h-3.5" />
            ALS Ambulances Only
          </button>
        </div>
      </div>

      {/* Hospital Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredHospitals.map((hosp) => (
          <div
            key={hosp.id}
            className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 hover:border-gray-700 backdrop-blur-md shadow-xl flex flex-col justify-between transition space-y-4"
          >
            <div>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-emerald-600/20 text-emerald-400 rounded-xl">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-wide">{hosp.name}</h3>
                    <p className="text-[11px] text-gray-400 font-mono">{hosp.hospital_code || 'REG-HOSP'}</p>
                  </div>
                </div>

                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800">
                  Active Provider
                </span>
              </div>

              <div className="mt-3 space-y-2 text-xs text-gray-300">
                <div className="flex items-center gap-2 text-gray-400">
                  <MapPin className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                  <span className="truncate">{hosp.address}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-400 font-mono">
                  <Phone className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  <span>{hosp.phone_numbers.join(', ')}</span>
                </div>
                {hosp.description && (
                  <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed pt-1">
                    {hosp.description}
                  </p>
                )}
              </div>
            </div>

            {/* Badges & Stats */}
            <div className="pt-3 border-t border-gray-800/80 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 flex-wrap">
                {hosp.has_trauma_center && (
                  <span className="px-2 py-0.5 rounded-md bg-amber-950/80 text-amber-400 border border-amber-800/60 text-[10px] font-bold">
                    Trauma Center
                  </span>
                )}
                {hosp.has_ambulance && (
                  <span className="px-2 py-0.5 rounded-md bg-blue-950/80 text-blue-400 border border-blue-800/60 text-[10px] font-bold">
                    ALS Ambulance
                  </span>
                )}
              </div>

              <span className="font-mono text-[11px] text-gray-400">
                Avg Response: <strong className="text-white">{hosp.average_response_time_minutes || 3.5}m</strong>
              </span>
            </div>
          </div>
        ))}
      </div>

      {isAddOpen && (
        <AddHospitalModal
          isOpen={isAddOpen}
          onClose={() => setIsAddOpen(false)}
          onHospitalAdded={(newHosp) => setHospitals((prev) => [newHosp, ...prev])}
        />
      )}
    </div>
  );
};
