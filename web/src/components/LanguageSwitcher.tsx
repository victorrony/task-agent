'use client';

import { useLocale } from '@/lib/i18n';

const Flag = ({ locale }: { locale: 'pt' | 'en' }) => (
  <span className="text-base leading-none" role="img" aria-label={locale === 'pt' ? 'Português' : 'English'}>
    {locale === 'pt' ? '🇵🇹' : '🇬🇧'}
  </span>
);

export default function LanguageSwitcher() {
  const { locale, setLocale } = useLocale();

  const toggleLocale = () => {
    setLocale(locale === 'pt' ? 'en' : 'pt');
  };

  return (
    <button
      onClick={toggleLocale}
      className="p-2 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-emerald-500/50 transition-colors group flex items-center gap-2"
      title={locale === 'pt' ? 'Switch to English' : 'Mudar para Português'}
    >
      <Flag locale={locale} />
      <span className="text-xs font-medium text-slate-400 group-hover:text-emerald-400 transition-colors uppercase">
        {locale}
      </span>
    </button>
  );
}
