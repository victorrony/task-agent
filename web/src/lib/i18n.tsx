'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import pt from '@/locales/pt.json';
import en from '@/locales/en.json';

type Locale = 'pt' | 'en';
type Translations = typeof pt;

const translations: Record<Locale, Translations> = {
  pt,
  en,
};

interface LocaleContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

interface LocaleProviderProps {
  children: ReactNode;
}

export function LocaleProvider({ children }: LocaleProviderProps) {
  const [locale, setLocaleState] = useState<Locale>('pt');
  const [mounted, setMounted] = useState(false);

  // Load locale from localStorage on mount
  useEffect(() => {
    const savedLocale = localStorage.getItem('locale') as Locale | null;
    if (savedLocale && (savedLocale === 'pt' || savedLocale === 'en')) {
      setLocaleState(savedLocale);
    }
    setMounted(true);
  }, []);

  // Save locale to localStorage when it changes
  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem('locale', newLocale);

    // Update html lang attribute
    if (typeof document !== 'undefined') {
      document.documentElement.lang = newLocale;
    }
  };

  // Translation function
  const t = (key: string): string => {
    const dict = translations[locale] as Record<string, string>;

    // Flat key lookup (keys like "app.title" stored as-is)
    if (key in dict) {
      return dict[key];
    }

    console.warn(`Translation key not found: ${key} (locale: ${locale})`);
    return key;
  };

  // Don't render until mounted to avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within a LocaleProvider');
  }
  return context;
}
