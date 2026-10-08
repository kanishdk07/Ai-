import React, { useState } from 'react';
import { Hospital } from '../../types';
import { hospitalApi } from '../../api/hospitalApi';
import { X, Building2, Phone, MapPin } from 'lucide-react';

interface AddHospitalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onHospitalAdded: (hosp: Hospital) => void;
}

export const AddHospitalModal: React.FC<AddHospitalModalProps> = ({
  isOpen,
  onClose,
  onHospitalAdded,
}) => {
  const [name, setName] = useState<string>('');
  const [phone, setPhone] = useState<string>('+91');
  const [email, setEmail] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [city, setCity] = useState<string>('Delhi NCR');
  const [latitude, setLatitude] = useState<number>(28.6139);
  const [longitude, setLongitude] = useState<number>(77.2090);
  const [hasTraumaCenter, setHasTraumaCenter] = useState<boolean>(true);
  const [hasAmbulance, setHasAmbulance] = useState<boolean>(true);
  const [bedCapacity, setBedCapacity] = useState<number>(250);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const created = await hospitalApi.createHospital({
        name,
        phone_numbers: [phone],
        email,
        address,
        city,
        latitude,
        longitude,
        has_trauma_center: hasTraumaCenter,
        has_ambulance: hasAmbulance,
        bed_capacity: bedCapacity,
        available_beds: Math.floor(bedCapacity * 0.15),
      });
      onHospitalAdded(created);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to register hospital');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 bg-gray-950 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-600/20 text-emerald-400 rounded-lg">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Register Emergency Hospital</h3>
              <p className="text-xs text-gray-400 font-mono">Healthcare Provider Directory</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Hospital Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Apex Trauma & Multi-Specialty Hospital"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Emergency Phone (+91...) *
              </label>
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Emergency Email
              </label>
              <input
                type="email"
                placeholder="casualty@hospital.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Full Address *
            </label>
            <input
              type="text"
              required
              placeholder="Street, Highway Intersection, City"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Latitude (WGS84)
              </label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(e) => setLatitude(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Longitude (WGS84)
              </label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(e) => setLongitude(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <label className="flex items-center gap-2 p-3 rounded-xl bg-gray-950 border border-gray-800 cursor-pointer">
              <input
                type="checkbox"
                checked={hasTraumaCenter}
                onChange={(e) => setHasTraumaCenter(e.target.checked)}
                className="rounded border-gray-700 text-emerald-500 focus:ring-0"
              />
              <span className="text-xs text-gray-300 font-semibold">Trauma Center (Level 1)</span>
            </label>

            <label className="flex items-center gap-2 p-3 rounded-xl bg-gray-950 border border-gray-800 cursor-pointer">
              <input
                type="checkbox"
                checked={hasAmbulance}
                onChange={(e) => setHasAmbulance(e.target.checked)}
                className="rounded border-gray-700 text-emerald-500 focus:ring-0"
              />
              <span className="text-xs text-gray-300 font-semibold">ALS Ambulance Fleet</span>
            </label>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-emerald-600/30 transition disabled:opacity-50"
            >
              {isSubmitting ? 'Registering...' : 'Register Hospital'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
