import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en/translation.json';
import es from './locales/es/translation.json';

const resources = {
  en: { translation: en },
  es: { translation: es }
};

// determine language from browser or fallback to english
let lng = 'en';
if (navigator.language && navigator.language.startsWith('es')) {
  lng = 'es';
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
