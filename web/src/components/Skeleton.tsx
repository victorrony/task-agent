'use client';

export function SkeletonCard() {
  return (
    <div className="p-6 rounded-xl border border-slate-700 bg-slate-800/50 animate-pulse">
      <div className="flex justify-between items-center mb-4">
        <div className="h-3 bg-slate-700 rounded w-1/3" />
        <div className="h-8 w-8 bg-slate-700 rounded-lg" />
      </div>
      <div className="h-7 bg-slate-700 rounded w-2/3" />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 animate-pulse">
      <div className="h-4 bg-slate-700 rounded w-1/4 mb-6" />
      <div className="h-[250px] bg-slate-800/50 rounded-xl" />
    </div>
  );
}

export function SkeletonChat() {
  return (
    <div className="h-[600px] bg-slate-900/50 rounded-xl border border-slate-800 animate-pulse">
      <div className="p-4 border-b border-slate-800">
        <div className="h-5 bg-slate-700 rounded w-1/3" />
      </div>
      <div className="p-4 space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="flex gap-3">
            <div className="h-8 w-8 bg-slate-700 rounded-full shrink-0" />
            <div className="h-12 bg-slate-800 rounded-lg flex-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonTransactions() {
  return (
    <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 animate-pulse">
      <div className="h-5 bg-slate-700 rounded w-1/3 mb-4" />
      <div className="space-y-3">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="flex justify-between items-center p-3">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 bg-slate-700 rounded-full" />
              <div className="space-y-2">
                <div className="h-3 bg-slate-700 rounded w-24" />
                <div className="h-2 bg-slate-700/60 rounded w-16" />
              </div>
            </div>
            <div className="h-4 bg-slate-700 rounded w-20" />
          </div>
        ))}
      </div>
    </div>
  );
}
