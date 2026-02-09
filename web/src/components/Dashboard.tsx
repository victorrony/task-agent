'use client';

import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer 
} from 'recharts';

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: string;
  color?: string;
}

export const StatCard = ({ title, value, icon, trend, color = "bg-slate-800" }: StatCardProps) => (
  <div className={`p-6 rounded-xl border border-slate-700 ${color} shadow-lg transition-all hover:scale-[1.02]`}>
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">{title}</h3>
      <div className="p-2 bg-slate-700/50 rounded-lg text-emerald-400">
        {icon}
      </div>
    </div>
    <div className="flex items-baseline gap-2">
      <span className="text-3xl font-bold text-white">{value}</span>
      {trend && (
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full 
          ${trend.startsWith('+') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
          {trend}
        </span>
      )}
    </div>
  </div>
);

export const LineChart = ({ data }: { data: any[] }) => (
  <div className="h-[300px] w-full bg-slate-800/50 rounded-xl p-4 border border-slate-700">
    <h3 className="text-lg font-semibold mb-4 text-slate-200">Evolução do Saldo</h3>
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <XAxis dataKey="date" stroke="#64748b" tick={{fontSize: 12}} />
        <YAxis stroke="#64748b" tick={{fontSize: 12}} />
        <Tooltip 
          contentStyle={{backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc'}}
          itemStyle={{color: '#10b981'}}
        />
        <Area 
          type="monotone" 
          dataKey="balance" 
          stroke="#10b981" 
          strokeWidth={3}
          fillOpacity={1} 
          fill="url(#colorBalance)" 
        />
      </AreaChart>
    </ResponsiveContainer>
  </div>
);
