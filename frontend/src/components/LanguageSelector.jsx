import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown } from 'lucide-react';
import { languages } from '@/i18n';

const LanguageSelector = ({ className = '' }) => {
  const { i18n } = useTranslation();
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Get language code - keep full code if it exists in languages list, otherwise get base
  const getLanguageCode = (code) => {
    if (!code) return 'en';
    const fullCode = code;
    if (languages.find(l => l.code === fullCode)) {
      return fullCode;
    }
    return code.split('-')[0];
  };

  const currentLanguage = languages.find(l => l.code === getLanguageCode(i18n.language)) || languages[0];

  const changeLanguage = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem('metro-taxi-language', code);
    setLanguageMenuOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setLanguageMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setLanguageMenuOpen(!languageMenuOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-zinc-800/50 hover:bg-zinc-700/50 transition-colors text-sm"
        data-testid="language-selector-btn"
      >
        <span className="text-lg">{currentLanguage.flag}</span>
        <span className="text-white hidden sm:inline">{currentLanguage.name}</span>
        <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform ${languageMenuOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {languageMenuOpen && (
        <div className="absolute right-0 top-full mt-2 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto min-w-[180px]">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-zinc-800 transition-colors text-sm ${
                i18n.language === lang.code ? 'bg-[#FFD60A]/10 text-[#FFD60A]' : 'text-white'
              }`}
              data-testid={`language-option-${lang.code}`}
            >
              <span className="text-lg">{lang.flag}</span>
              <span>{lang.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
