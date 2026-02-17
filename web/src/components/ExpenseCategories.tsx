'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useLocale } from '@/lib/i18n';
import type { ExpenseCategory } from '@/lib/api';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#6b7280'];

interface Props {
  data: ExpenseCategory[];
}

export default function ExpenseCategories({ data }: Props) {
  const { t } = useLocale();

  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800">
        <h3 className="text-base font-semibold mb-4 text-slate-300">{t('categories.title')}</h3>
        <div className="h-[240px] flex items-center justify-center text-slate-500 text-sm">
          {t('categories.empty')}
        </div>
      </div>
    );
  }

  const total = data.reduce((sum, c) => sum + c.value, 0);

  return (
    <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800">
      <h3 className="text-base font-semibold mb-4 text-slate-300">{t('categories.title')}</h3>
      <div className="flex items-center gap-4">
        {/* Donut Chart */}
        <div className="w-[160px] h-[160px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={3}
                dataKey="value"
                nameKey="name"
                strokeWidth={0}
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '12px'
                }}
                formatter={(value: number | undefined) => [`CVE ${Number(value ?? 0).toLocaleString()}`, '']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2 overflow-y-auto max-h-[160px]">
          {data.map((cat, index) => {
            const pct = total > 0 ? ((cat.value / total) * 100).toFixed(1) : '0';
            return (
              <div key={cat.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-slate-300 truncate max-w-[100px]">{cat.name}</span>
                </div>
                <span className="text-slate-400 font-mono">{pct}%</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
