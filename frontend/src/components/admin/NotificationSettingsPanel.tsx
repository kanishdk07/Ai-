import React, { useState, useEffect } from 'react';
import {
  Bell,
  BellOff,
  Phone,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Send,
  Save,
  Hospital,
  Loader2,
} from 'lucide-react';
import { adminApi } from '../../api/adminApi';
import { NotificationSettings, TestNotificationResult } from '../../types';

// Phone number validator — accepts E.164 format: +[countrycode][number]
function isValidPhone(value: string): boolean {
  return /^\+[1-9]\d{6,14}$/.test(value.trim());
}

export const NotificationSettingsPanel: React.FC = () => {
  const [notifSettings, setNotifSettings] = useState<NotificationSettings>({
    emergency_contact_number: null,
    emergency_notifications_enabled: false,
    hospital_notifications_enabled: false,
  });

  const [phoneInput, setPhoneInput] = useState<string>('');
  const [phoneError, setPhoneError] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveResult, setSaveResult] = useState<'success' | 'error' | null>(null);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<TestNotificationResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    adminApi.getNotificationSettings().then((s) => {
      setNotifSettings(s);
      setPhoneInput(s.emergency_contact_number ?? '');
      setIsLoading(false);
    });
  }, []);

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPhoneInput(e.target.value);
    setPhoneError('');
    setSaveResult(null);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setPhoneError('');
    setSaveResult(null);
    setTestResult(null);

    const trimmed = phoneInput.trim();
    if (trimmed && !isValidPhone(trimmed)) {
      setPhoneError(
        'Invalid phone number. Use international format: +91XXXXXXXXXX (E.164, digits after +)'
      );
      return;
    }

    setIsSaving(true);
    try {
      const updated = await adminApi.updateNotificationSettings({
        emergency_contact_number: trimmed || null,
        emergency_notifications_enabled: notifSettings.emergency_notifications_enabled,
        hospital_notifications_enabled: notifSettings.hospital_notifications_enabled,
      });
      setNotifSettings(updated);
      setPhoneInput(updated.emergency_contact_number ?? '');
      setSaveResult('success');
      setTimeout(() => setSaveResult(null), 4000);
    } catch {
      setSaveResult('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleEmergency = () => {
    setNotifSettings((prev) => ({
      ...prev,
      emergency_notifications_enabled: !prev.emergency_notifications_enabled,
    }));
    setSaveResult(null);
    setTestResult(null);
  };

  const handleToggleHospital = () => {
    setNotifSettings((prev) => ({
      ...prev,
      hospital_notifications_enabled: !prev.hospital_notifications_enabled,
    }));
    setSaveResult(null);
  };

  const handleTestNotification = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await adminApi.sendTestNotification();
      setTestResult(result);
    } catch {
      setTestResult({
        sent: false,
        message: 'Failed to reach the server. Check your connection.',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsTesting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 flex items-center gap-3 text-gray-400">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span className="text-sm">Loading notification settings…</span>
      </div>
    );
  }

  const hasValidNumber =
    !!notifSettings.emergency_contact_number &&
    isValidPhone(notifSettings.emergency_contact_number);
  const emergencyOn = notifSettings.emergency_notifications_enabled;
  const hospitalOn = notifSettings.hospital_notifications_enabled;

  return (
    <div
      id="notification-settings-panel"
      className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md space-y-6"
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-orange-600/20 text-orange-400 rounded-xl">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">
              Notification Settings
            </h3>
            <p className="text-xs text-gray-400">
              Configure the emergency contact number and SMS notification toggles
            </p>
          </div>
        </div>

        {saveResult === 'success' && (
          <span className="px-3 py-1 bg-emerald-950 border border-emerald-500 text-emerald-400 text-xs font-bold rounded-lg flex items-center gap-1.5 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4" />
            Settings Saved
          </span>
        )}
        {saveResult === 'error' && (
          <span className="px-3 py-1 bg-red-950 border border-red-500 text-red-400 text-xs font-bold rounded-lg flex items-center gap-1.5">
            <XCircle className="w-4 h-4" />
            Save Failed
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Emergency Contact Number */}
        <div>
          <label
            htmlFor="emergency-contact-number"
            className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-2"
          >
            Emergency Contact Number
          </label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                id="emergency-contact-number"
                type="tel"
                value={phoneInput}
                onChange={handlePhoneChange}
                placeholder="+919876543210"
                autoComplete="tel"
                className={`w-full pl-10 pr-4 py-2.5 bg-gray-800 border ${
                  phoneError ? 'border-red-500' : 'border-gray-700'
                } rounded-xl text-white text-sm font-mono focus:outline-none focus:border-orange-500 transition`}
              />
            </div>
            {notifSettings.emergency_contact_number && hasValidNumber && (
              <span className="flex items-center gap-1 text-emerald-400 text-xs font-mono bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-2 rounded-lg whitespace-nowrap">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Configured
              </span>
            )}
          </div>
          {phoneError && (
            <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              {phoneError}
            </p>
          )}
          <p className="mt-1 text-[10px] text-gray-400">
            Use international E.164 format (e.g. +919876543210). Leave empty to remove.
            Number is stored in the database — never hard-coded.
          </p>
        </div>

        {/* Emergency Notifications Toggle */}
        <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              {emergencyOn ? (
                <Bell className="w-4 h-4 text-orange-400" />
              ) : (
                <BellOff className="w-4 h-4 text-gray-500" />
              )}
              <span className="text-sm font-bold text-white">Emergency Notifications</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  emergencyOn
                    ? 'bg-orange-950 text-orange-400 border border-orange-800'
                    : 'bg-gray-800 text-gray-400 border border-gray-700'
                }`}
              >
                {emergencyOn ? 'ON' : 'OFF'}
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed max-w-xl">
              When <strong>ON</strong>, an SMS is sent to the configured number on every
              AI-detected accident. When <strong>OFF</strong>, no SMS is sent — the existing
              accident detection and hospital workflow continues normally.
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
            <input
              type="checkbox"
              id="emergency-notif-toggle"
              checked={emergencyOn}
              onChange={handleToggleEmergency}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600" />
          </label>
        </div>

        {/* Hospital Notifications Toggle */}
        <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Hospital className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-bold text-white">Hospital Notifications</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  hospitalOn
                    ? 'bg-blue-950 text-blue-400 border border-blue-800'
                    : 'bg-gray-800 text-gray-400 border border-gray-700'
                }`}
              >
                {hospitalOn ? 'ON' : 'OFF'}
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed max-w-xl">
              Controls the hospital SMS/Call channel (managed by the Automated Hospital
              Alert Workflow). The hospital list in the Hospitals tab is{' '}
              <strong>informational only</strong> — no messages are sent to hospitals
              just because they appear in the list.
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
            <input
              type="checkbox"
              id="hospital-notif-toggle"
              checked={hospitalOn}
              onChange={handleToggleHospital}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
          </label>
        </div>

        {/* Save & Test buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-800 gap-3 flex-wrap">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2.5 bg-orange-600 hover:bg-orange-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-orange-600/30 transition disabled:opacity-50 flex items-center gap-2"
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isSaving ? 'Saving…' : 'Save Settings'}
          </button>

          <button
            type="button"
            id="send-test-notification-btn"
            onClick={handleTestNotification}
            disabled={isTesting}
            className="px-5 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-xl text-sm font-bold transition disabled:opacity-50 flex items-center gap-2 border border-gray-600"
          >
            {isTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {isTesting ? 'Sending…' : 'Send Test Notification'}
          </button>
        </div>
      </form>

      {/* Test result banner */}
      {testResult && (
        <div
          className={`p-4 rounded-xl border text-sm animate-fadeIn ${
            testResult.sent
              ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300'
              : 'bg-red-950/80 border-red-700 text-red-300'
          }`}
        >
          <div className="flex items-start gap-2">
            {testResult.sent ? (
              <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" />
            )}
            <div>
              <p className="font-semibold">{testResult.sent ? 'Test Sent' : 'Not Sent'}</p>
              <p className="text-xs mt-0.5 opacity-80">{testResult.message}</p>
              {testResult.recipient && (
                <p className="text-xs mt-0.5 font-mono opacity-70">
                  Recipient: {testResult.recipient}
                  {testResult.provider ? ` · Provider: ${testResult.provider}` : ''}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Status Summary */}
      <div className="pt-4 border-t border-gray-800 space-y-1.5">
        <p className="text-[11px] font-bold uppercase tracking-widest text-gray-500 mb-2">
          Status
        </p>
        <StatusRow
          ok={emergencyOn}
          okText="Emergency notifications enabled"
          offText="Emergency notifications disabled"
        />
        <StatusRow
          ok={hasValidNumber}
          okText={`Contact number configured: ${notifSettings.emergency_contact_number}`}
          offText="No emergency contact number configured"
        />
        <StatusRow
          ok={hospitalOn}
          okText="Hospital notifications enabled"
          offText="Hospital notifications disabled"
          neutralOff
        />
      </div>
    </div>
  );
};

interface StatusRowProps {
  ok: boolean;
  okText: string;
  offText: string;
  neutralOff?: boolean;
}

const StatusRow: React.FC<StatusRowProps> = ({ ok, okText, offText, neutralOff }) => (
  <div className="flex items-center gap-2 text-xs">
    {ok ? (
      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
    ) : (
      <XCircle
        className={`w-3.5 h-3.5 flex-shrink-0 ${neutralOff ? 'text-gray-500' : 'text-red-400'}`}
      />
    )}
    <span className={ok ? 'text-emerald-300' : neutralOff ? 'text-gray-400' : 'text-red-300'}>
      {ok ? okText : offText}
    </span>
  </div>
);
