import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import fr from './locales/fr.json';
import en from './locales/en.json';
import enGB from './locales/en-GB.json';
import de from './locales/de.json';
import nl from './locales/nl.json';
import es from './locales/es.json';
import pt from './locales/pt.json';
import it from './locales/it.json';
import no from './locales/no.json';
import sv from './locales/sv.json';
import da from './locales/da.json';
import zh from './locales/zh.json';
import hi from './locales/hi.json';
import pa from './locales/pa.json';
import ar from './locales/ar.json';
import ru from './locales/ru.json';

const resources = {
  fr: { translation: fr },
  en: { translation: en },
  'en-GB': { translation: enGB },
  de: { translation: de },
  nl: { translation: nl },
  es: { translation: es },
  pt: { translation: pt },
  it: { translation: it },
  no: { translation: no },
  sv: { translation: sv },
  da: { translation: da },
  zh: { translation: zh },
  hi: { translation: hi },
  pa: { translation: pa },
  ar: { translation: ar },
  ru: { translation: ru }
};

// Supported language codes — must match keys in resources
const supportedLngs = Object.keys(resources);

// Read persisted language (i18next default key)
const storedLng = typeof window !== 'undefined'
  ? localStorage.getItem('i18nextLng')
  : null;

// Determine initial language: stored > querystring > navigator > 'fr'
function getInitialLng() {
  if (storedLng && supportedLngs.includes(storedLng)) return storedLng;
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const qs = params.get('lng');
    if (qs && supportedLngs.includes(qs)) return qs;
    // Try navigator languages
    const navLangs = navigator.languages || [navigator.language];
    for (const nl of navLangs) {
      if (supportedLngs.includes(nl)) return nl;
      const base = nl.split('-')[0];
      if (supportedLngs.includes(base)) return base;
    }
  }
  return 'fr';
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: getInitialLng(),
    supportedLngs,
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false
    },
    load: 'currentOnly'
  });

// Keep document lang attribute in sync
if (typeof document !== 'undefined') {
  document.documentElement.lang = i18n.language;
  i18n.on('languageChanged', (lng) => {
    document.documentElement.lang = lng;
    localStorage.setItem('i18nextLng', lng);
  });
}

export default i18n;

// Languages sorted alphabetically by name
export const languages = [
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'en', name: 'English (US)', flag: '🇺🇸' },
  { code: 'en-GB', name: 'English (UK)', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'no', name: 'Norsk', flag: '🇳🇴' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇵🇰' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
  { code: 'zh', name: '中文', flag: '🇨🇳' }
];
