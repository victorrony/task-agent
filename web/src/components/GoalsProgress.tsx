'use client';

import { Target } from 'lucide-react';
import { Goal } from '@/lib/api';
import { useLocale } from '@/lib/i18n';

interface GoalsProgressProps {
  goals: Goal[];
}

export default function GoalsProgress({ goals }: GoalsProgressProps) {
  const { t } = useLocale();

  if (goals.length === 0) {
    return (
      <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <Target size={20} className="text-emerald-400" /> {t('goals.title')}
        </h3>
        <div className="text-center text-slate-500 py-6">
          <Target size={32} className="mx-auto mb-2 opacity-30" />
          <p>{t('goals.empty')}</p>
          <p className="text-xs mt-1">{t('goals.empty.cta')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800">
      <h3 className="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
        <Target size={20} className="text-emerald-400" /> {t('goals.title')}
      </h3>
      <div className="space-y-4">
        {goals.map((goal, idx) => {
          const pct = Math.min(100, goal.percent);
          const color = pct >= 80 ? 'bg-emerald-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-blue-500';
          return (
            <div key={idx} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-slate-200">{goal.name}</span>
                <span className="text-xs font-mono text-slate-400">{pct.toFixed(0)}%</span>
              </div>
              <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`absolute top-0 left-0 h-full ${color} rounded-full transition-all duration-700`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>CVE {goal.current.toLocaleString()}</span>
                <span>CVE {goal.target.toLocaleString()}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
