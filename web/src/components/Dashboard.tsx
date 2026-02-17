'use client';

import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts';
import { useLocale } from '@/lib/i18n';

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: string;
  color?: string;
  hideValue?: boolean;
}

function getTrendStyle(trend: string): string {
  const isPositive = trend.startsWith('+') || trend === 'Positivo' || trend === 'Positive';
  if (isPositive) return 'bg-emerald-500/10 text-emerald-400';

  const isNegative = trend.startsWith('-') || trend === 'Negativo' || trend === 'Negative';
  if (isNegative) return 'bg-red-500/10 text-red-400';

  return 'bg-slate-700/50 text-slate-400';
}

export const StatCard = ({ title, value, icon, trend, color = "border-slate-700 bg-slate-800/50", hideValue }: StatCardProps) => (
  <div className={`p-5 rounded-xl border ${color} shadow-lg transition-all hover:scale-[1.02] hover:shadow-emerald-500/5`}>
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-slate-400 text-xs font-medium uppercase tracking-wider">{title}</h3>
      <div className="p-2 bg-slate-700/50 rounded-lg text-emerald-400">
        {icon}
      </div>
    </div>
    <div>
      <span className="text-2xl font-bold text-white">
        {hideValue ? '••••••' : String(value)}
      </span>
    </div>
    {trend && (
      <span className={`text-xs font-medium mt-2 inline-block px-2 py-0.5 rounded-full ${getTrendStyle(trend)}`}>
        {hideValue ? '***' : trend}
      </span>
    )}
  </div>
);

export const LineChart = ({ data }: { data: { date: string; balance: number }[] }) => {
  const { t } = useLocale();

  if (!data || data.length === 0) {
    return (
      <div className="h-70 flex items-center justify-center text-slate-500 text-sm">
        {t('chart.empty')}
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
        <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
          itemStyle={{ color: '#10b981' }}
          formatter={(value: number | undefined) => [`CVE ${Number(value ?? 0).toLocaleString()}`, t('chart.tooltip.balance')]}
        />
        <Area
          type="monotone"
          dataKey="balance"
          stroke="#10b981"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorBalance)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};
