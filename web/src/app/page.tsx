'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { fetchDashboard, fetchTransactions, fetchExpenseCategories, DashboardResponse, Transaction, ExpenseCategory } from '@/lib/api';
import { useLocale } from '@/lib/i18n';
import ChatWidget, { ChatWidgetHandle } from '@/components/ChatWidget';
import UserSelector from '@/components/UserSelector';
import GoalsProgress from '@/components/GoalsProgress';
import TransactionsList from '@/components/TransactionsList';
import ExpenseCategories from '@/components/ExpenseCategories';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { StatCard, LineChart } from '@/components/Dashboard';
import { SkeletonCard, SkeletonChart, SkeletonChat, SkeletonTransactions } from '@/components/Skeleton';
import { Wallet, TrendingUp, AlertTriangle, Layers, RefreshCw, Shield, Eye, EyeOff } from 'lucide-react';
import { Toaster } from 'react-hot-toast';

interface PageData extends DashboardResponse {
  transactions: Transaction[];
  expenseCategories: ExpenseCategory[];
}

export default function Home() {
  const { t } = useLocale();
  const [data, setData] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState(1);
  const [showValues, setShowValues] = useState(true);
  const chatRef = useRef<ChatWidgetHandle>(null);

  // FIX 1 (HIGH): Wrap loadData in useCallback so it is a stable reference for useEffect.
  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    setError(null);
    try {
      const [dashboard, tx, categories] = await Promise.all([
        fetchDashboard(userId),
        fetchTransactions(userId),
        fetchExpenseCategories(userId)
      ]);
      setData({ ...dashboard, transactions: tx, expenseCategories: categories });
    } catch (err) {
      if (!silent) setError(err instanceof Error ? err.message : t('error.message'));
    } finally {
      if (!silent) setLoading(false);
      setRefreshing(false);
    }
  }, [userId, t]);

  useEffect(() => { loadData(); }, [loadData]);

  // Memoize chartData - must be before early returns to respect Rules of Hooks
  const chartData = useMemo(() => {
    if (!data) return [];
    return data.transactions.map((tx) => ({
      date: tx.Data,
      balance: Number(tx.Valor)
    }));
  }, [data]);

  // Skeleton loading
  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 p-4 lg:p-8 grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 font-sans antialiased">
        <div className="space-y-6">
          <div className="h-16" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2"><SkeletonChart /></div>
            <div><SkeletonTransactions /></div>
          </div>
        </div>
        <div><SkeletonChat /></div>
      </main>
    );
  }

  // Error state
  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-8">
        <div className="bg-red-900/20 border border-red-500/30 p-8 rounded-2xl max-w-md text-center">
          <AlertTriangle size={40} className="mx-auto mb-4 text-red-400" />
          <h2 className="text-lg font-semibold mb-2">{t('error.title')}</h2>
          <p className="text-sm text-slate-400 mb-6">{error}</p>
          <button
            onClick={() => loadData()}
            className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-2 rounded-lg transition-colors text-sm font-medium"
          >
            {t('error.retry')}
          </button>
        </div>
      </main>
    );
  }

  if (!data) return null;

  // FIX 2 (HIGH): Parse the profit string numerically instead of checking for '-' in the
  // formatted string, which is fragile (e.g. currency symbols could contain a dash).
  const profitValue = Number.parseFloat(data.stats.profit.replaceAll(/[^0-9.-]/g, ''));
  const profitTrend = profitValue < 0 ? t('stats.trend.negative') : t('stats.trend.positive');

  // FIX 3 (HIGH): Use locale-agnostic regex to detect warning/danger health status so the
  // component works correctly in both Portuguese and English (and with emoji variants).
  const statusStr = data.stats.status;
  const isWarning = /reserva|reserve|⚠️/i.test(statusStr);
  const isDanger = /divida|debt|🚨/i.test(statusStr);
  // Extract health card color to avoid a nested ternary in JSX (S3358).
  let healthColor = 'border-slate-700 bg-slate-800/50';
  if (isDanger) healthColor = 'border-red-500/30 bg-red-900/10';
  else if (isWarning) healthColor = 'border-yellow-500/30 bg-yellow-900/10';

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-4 lg:p-8 grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 font-sans antialiased">

      {/* Esquerda: Dashboard */}
      <div className="space-y-6">
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent">
              {t('app.title')}
            </h1>
            <p className="text-slate-500 text-sm mt-1">{t('app.subtitle')}</p>
          </div>
          <div className="flex items-center gap-3">
            <UserSelector currentUserId={userId} onUserChange={setUserId} />
            <LanguageSwitcher />

            {/* FIX 4 (HIGH): Replace hardcoded Portuguese tooltip strings with t() calls.
                FIX 6 (LOW): Add aria-pressed and aria-label for accessibility. */}
            <button
              onClick={() => setShowValues(!showValues)}
              className="p-2 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-emerald-500/50 transition-colors text-slate-400 hover:text-emerald-400"
              title={showValues ? t('header.hideValues') : t('header.showValues')}
              aria-pressed={showValues}
              aria-label={showValues ? t('header.hideValues') : t('header.showValues')}
            >
              {showValues ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>

            {/* FIX 6 (LOW): Add aria-label to the refresh button. */}
            <button
              onClick={() => loadData()}
              className="p-2 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-emerald-500/50 transition-colors text-slate-400 hover:text-emerald-400"
              title={t('header.refresh.title')}
              aria-label={t('header.refresh.title')}
            >
              <RefreshCw size={16} />
            </button>
            <span className="bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-medium border border-emerald-500/20">
              {t('app.status.online')}
            </span>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <StatCard
            title={t('stats.balance.title')}
            value={data.stats.balance}
            icon={<Wallet size={20} />}
            color="border-emerald-500/30 bg-emerald-900/10"
            hideValue={!showValues}
          />
          <StatCard
            title={t('stats.reserve.title')}
            value={data.stats.reserve}
            icon={<Shield size={20} />}
            color="border-cyan-500/30 bg-cyan-900/10"
            hideValue={!showValues}
          />
          <StatCard
            title={t('stats.profit.title')}
            value={data.stats.profit}
            icon={<TrendingUp size={20} />}
            trend={profitTrend}
            color={profitTrend === t('stats.trend.negative') ? 'border-red-500/30 bg-red-900/10' : 'border-blue-500/30 bg-blue-900/10'}
            hideValue={!showValues}
          />
          {/* FIX 3 (HIGH): Use regex-based isWarning / isDanger flags instead of fragile
              Portuguese-only string includes. Order: danger > warning > neutral. */}
          <StatCard
            title={t('stats.health.title')}
            value={data.stats.status}
            icon={<AlertTriangle size={20} />}
            color={healthColor}
            hideValue={!showValues}
          />
          <StatCard
            title={t('stats.goals.title')}
            value={data.stats.goals}
            icon={<Layers size={20} />}
            hideValue={!showValues}
          />
        </div>

        {/* Chart + Transactions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 bg-slate-900/50 p-5 rounded-2xl border border-slate-800">
            <h3 className="text-base font-semibold mb-4 text-slate-300">{t('chart.title')}</h3>
            <LineChart data={chartData} />
          </div>
          <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800">
            <h3 className="text-base font-semibold mb-4 text-slate-300">{t('transactions.title')}</h3>
            <TransactionsList transactions={data.recent_transactions} limit={5} />
          </div>
        </div>

        {/* Categories + Goals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ExpenseCategories data={data.expenseCategories} />
          <GoalsProgress goals={data.goals} />
        </div>
      </div>

      {/* Direita: Chat + Quick Commands fixos */}
      <div className="relative">
        <div className="sticky top-4 flex flex-col h-[calc(100vh-3.2rem)] gap-3">
          <ChatWidget ref={chatRef} userId={userId} onAgentResponse={() => loadData(true)} />

          {/* Quick Commands - fixo no bottom */}
          <div className="shrink-0 p-3 bg-slate-900/50 rounded-xl border border-slate-800">
            <h4 className="font-semibold text-emerald-400 text-xs mb-2">{t('quickCommands.title')}</h4>
            <div className="flex flex-wrap gap-2">
              {[
                t('quickCommands.analyze'),
                t('quickCommands.simulate'),
                t('quickCommands.viewGoals'),
                t('quickCommands.addExpense')
              ].map(cmd => (
                <button
                  key={cmd}
                  onClick={() => chatRef.current?.sendMessage(cmd)}
                  className="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-md text-xs transition-colors border border-slate-700 hover:border-emerald-500/50 hover:text-emerald-400"
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f8fafc',
            border: '1px solid #334155',
            borderRadius: '12px',
            fontSize: '13px',
          },
          success: {
            iconTheme: { primary: '#10b981', secondary: '#f8fafc' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#f8fafc' },
          },
        }}
      />
    </main>
  );
}
