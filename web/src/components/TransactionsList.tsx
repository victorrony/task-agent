'use client';

import { ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { Transaction } from '@/lib/api';
import { useLocale } from '@/lib/i18n';

interface TransactionsListProps {
  transactions: Transaction[];
  limit?: number;
}

export default function TransactionsList({ transactions, limit }: TransactionsListProps) {
  const { t } = useLocale();
  const items = limit ? transactions.slice(0, limit) : transactions;

  if (items.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8">
        <ArrowDownCircle size={32} className="mx-auto mb-2 opacity-30" />
        <p>{t('transactions.empty')}</p>
        <p className="text-xs mt-1">{t('transactions.empty.cta')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((tx, i) => (
        <div key={i} className="flex items-center gap-3 p-3 hover:bg-slate-800/50 rounded-lg transition-colors">
          <div className={`p-2 rounded-full ${
            tx.Tipo === 'entrada'
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-red-500/10 text-red-400'
          }`}>
            {tx.Tipo === 'entrada' ? <ArrowUpCircle size={18} /> : <ArrowDownCircle size={18} />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm text-slate-200 truncate">{tx['Descrição']}</p>
            <div className="flex gap-2 text-xs text-slate-500">
              <span>{tx.Data}</span>
              <span className="px-1.5 py-0.5 bg-slate-700/50 rounded text-slate-400">{tx.Categoria}</span>
            </div>
          </div>
          <span className={`font-mono text-sm font-medium whitespace-nowrap ${
            tx.Tipo === 'entrada' ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {tx.Tipo === 'entrada' ? '+' : '-'}{Number(tx.Valor).toLocaleString('pt-PT')} CVE
          </span>
        </div>
      ))}
    </div>
  );
}
