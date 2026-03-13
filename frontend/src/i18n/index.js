import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import fr from './locales/fr.json';
import en from './locales/en.json';
import es from './locales/es.json';
import pt from './locales/pt.json';
import no from './locales/no.json';
import sv from './locales/sv.json';
import da from './locales/da.json';
import zh from './locales/zh.json';
import ur from './locales/ur.json';

const resources = {
  fr: { translation: fr },
  en: { translation: en },
  es: { translation: es },
  pt: { translation: pt },
  no: { translation: no },
  sv: { translation: sv },
  da: { translation: da },
  zh: { translation: zh },
  ur: { translation: ur }
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
    }
  });

export default i18n;

export const languages = [
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'no', name: 'Norsk', flag: '🇳🇴' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ur', name: 'اردو', flag: '🇵🇰' }
];
