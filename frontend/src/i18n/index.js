import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import fr from './locales/fr.json';
import en from './locales/en.json';
import enGB from './locales/en-GB.json';
import de from './locales/de.json';
import nl from './locales/nl.json';
import es from './locales/es.json';
import pt from './locales/pt.json';
import no from './locales/no.json';
import sv from './locales/sv.json';
import da from './locales/da.json';
import zh from './locales/zh.json';
import hi from './locales/hi.json';
import pa from './locales/pa.json';

const resources = {
  fr: { translation: fr },
  en: { translation: en },
  'en-GB': { translation: enGB },
  de: { translation: de },
  nl: { translation: nl },
  es: { translation: es },
  pt: { translation: pt },
  no: { translation: no },
  sv: { translation: sv },
  da: { translation: da },
  zh: { translation: zh },
  hi: { translation: hi },
  pa: { translation: pa }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'fr',
    debug: false,
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    },
    // Load all language codes including region variants like en-GB
    load: 'all',
    // Use specific language if available, fall back to base language
    nonExplicitSupportedLngs: true
  });

export default i18n;

export const languages = [
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'en', name: 'English (US)', flag: '🇺🇸' },
  { code: 'en-GB', name: 'English (UK)', flag: '🇬🇧' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'no', name: 'Norsk', flag: '🇳🇴' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇵🇰' }
];
