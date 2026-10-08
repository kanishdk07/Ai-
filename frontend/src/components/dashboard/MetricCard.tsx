import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  variant?: 'default' | 'danger' | 'warning' | 'success' | 'info';
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = 'default',
  onClick,
}) => {
  const variantStyles = {
    default: {
      border: 'border-gray-800',
      bg: 'bg-gray-900/80',
      iconBg: 'bg-gray-800 text-gray-300',
      valueColor: 'text-white',
    },
    danger: {
      border: 'border-red-600/50 hover:border-red-500',
      bg: 'bg-gradient-to-br from-red-950/40 to-gray-900/90',
      iconBg: 'bg-red-600/20 text-red-400',
      valueColor: 'text-red-400',
    },
    warning: {
      border: 'border-amber-600/50 hover:border-amber-500',
      bg: 'bg-gradient-to-br from-amber-950/40 to-gray-900/90',
      iconBg: 'bg-amber-600/20 text-amber-400',
      valueColor: 'text-amber-400',
    },
    success: {
      border: 'border-emerald-600/50 hover:border-emerald-500',
      bg: 'bg-gradient-to-br from-emerald-950/40 to-gray-900/90',
      iconBg: 'bg-emerald-600/20 text-emerald-400',
      valueColor: 'text-emerald-400',
    },
    info: {
      border: 'border-blue-600/50 hover:border-blue-500',
      bg: 'bg-gradient-to-br from-blue-950/40 to-gray-900/90',
      iconBg: 'bg-blue-600/20 text-blue-400',
      valueColor: 'text-blue-400',
    },
  };

  const style = variantStyles[variant];

  return (
    <div
      onClick={onClick}
      className={`p-5 rounded-2xl border ${style.border} ${style.bg} backdrop-blur-md shadow-xl transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:-translate-y-1 hover:shadow-2xl' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-gray-400">{title}</p>
          <p className={`text-3xl font-extrabold mt-1 tracking-tight ${style.valueColor}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-xl ${style.iconBg} shadow-inner`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {(subtitle || trend) && (
        <div className="mt-3 flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-800/60">
          {subtitle && <span>{subtitle}</span>}
          {trend && (
            <span className={`font-semibold ${trend.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
