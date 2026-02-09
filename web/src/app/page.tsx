'use client';

import { useState, useEffect } from 'react';
import { fetchDashboard, fetchTransactions } from '@/lib/api';
import ChatWidget from '@/components/ChatWidget';
import { StatCard, LineChart } from '@/components/Dashboard';
import { Wallet, TrendingUp, AlertTriangle, Layers, Send } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(1);

  useEffect(() => {
    async function load() {
      try {
        const d = await fetchDashboard(userId);
        const tx = await fetchTransactions(userId);
        setData({ ...d, transactions: tx });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [userId]);

  if (loading) return (
    <div className="flex h-screen items-center justify-center bg-slate-900 text-emerald-500">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-emerald-500"></div>
    </div>
  );

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 grid lg:grid-cols-[1fr_400px] gap-8 font-sans antialiased">
      
      {/* Esquerda: Dashboard */}
      <div className="space-y-8 animate-fade-in-up">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent">
              FinanceAgent Pro <span className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded ml-2 align-middle">BETA</span>
            </h1>
            <p className="text-slate-400 mt-2">Gestão financeira inteligente com IA</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-sm font-medium border border-emerald-500/20">
              ● Online
            </span>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            title="Saldo Total" 
            value={data.stats.balance} 
            icon={<Wallet size={24} />} 
            trend="+2.5% vs mês anterior"
            color="border-emerald-500/30 bg-emerald-900/10"
          />
          <StatCard 
            title="Resultado Mensal" 
            value={data.stats.profit} 
            icon={<TrendingUp size={24} />} 
            trend={data.stats.profit.includes('-') ? 'Negativo' : 'Positivo'}
            color={data.stats.profit.includes('-') ? 'border-red-500/30 bg-red-900/10' : 'border-blue-500/30 bg-blue-900/10'}
          />
          <StatCard 
            title="Saúde Financeira" 
            value={data.stats.status} 
            icon={<AlertTriangle size={24} />} 
            color={data.stats.status.includes('Alerta') ? 'border-yellow-500/30 bg-yellow-900/10' : 'border-slate-700 bg-slate-800/50'}
          />
          <StatCard 
            title="Metas Ativas" 
            value={data.stats.goals} 
            icon={<Layers size={24} />} 
          />
        </div>

        {/* Main Chart Section */}
        <div className="grid grid-cols-3 gap-8">
          <div className="col-span-2 bg-slate-900/50 p-6 rounded-2xl border border-slate-800 shadow-xl">
             <LineChart data={data.transactions.map((t: any) => ({ date: t.Date, balance: t.Amount }))} />
          </div>
          
          <div className="col-span-1 bg-slate-900/50 p-6 rounded-2xl border border-slate-800 shadow-xl">
            <h3 className="text-lg font-semibold mb-4 text-slate-300">Últimas Transações</h3>
            <div className="space-y-3">
              {data.recent_transactions.map((tx: any, i: number) => (
                <div key={i} className="flex justify-between items-center p-3 hover:bg-slate-800/50 rounded-lg transition-colors border-b border-slate-800 last:border-0">
                  <div>
                    <p className="font-medium text-slate-200">{tx['Descrição']}</p>
                    <p className="text-xs text-slate-500">{tx['Categoria']}</p>
                  </div>
                  <span className={`font-mono font-medium ${tx['Tipo'] === 'entrada' ? 'text-emerald-400' : 'text-slate-400'}`}>
                    {tx['Tipo'] === 'entrada' ? '+' : '-'} {tx['Valor'].toLocaleString('pt-PT', { style: 'currency', currency: 'CVE' })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Direita: Chat Fixo */}
      <div className="relative">
        <div className="sticky top-8 space-y-4">
          <ChatWidget userId={userId} />
          
          <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-800 text-sm text-slate-400">
            <h4 className="font-semibold text-emerald-400 mb-2">Comandos Rápidos</h4>
            <div className="flex flex-wrap gap-2">
              {['Analisar gastos', 'Simular investimento', 'Ver metas', 'Adicionar despesa'].map(cmd => (
                <button key={cmd} className="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-md text-xs transition-colors border border-slate-700 hover:border-emerald-500/50">
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

    </main>
  );
}
