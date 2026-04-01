import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, X, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

const UpdateNotification = () => {
  const { t } = useTranslation();
  const [showUpdate, setShowUpdate] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    // Listen for custom update event from service worker registration
    const handleUpdateAvailable = () => {
      console.log('Update notification received');
      setShowUpdate(true);
    };

    window.addEventListener('sw-update-available', handleUpdateAvailable);

    return () => {
      window.removeEventListener('sw-update-available', handleUpdateAvailable);
    };
  }, []);

  const handleUpdate = () => {
    setUpdating(true);
    // Dispatch event to trigger the update
    window.dispatchEvent(new CustomEvent('sw-do-update'));
    
    // Reload after a short delay to ensure SW has activated
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  const handleDismiss = () => {
    setShowUpdate(false);
  };

  return (
    <AnimatePresence>
      {showUpdate && (
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 100 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-[9999]"
        >
          <div className="bg-gradient-to-r from-[#18181B] to-[#27272A] border border-[#FFD60A]/30 rounded-xl shadow-2xl overflow-hidden">
            {/* Accent line */}
            <div className="h-1 bg-gradient-to-r from-[#FFD60A] to-[#E6C209]" />
            
            <div className="p-4">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#FFD60A]/10 rounded-full flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-[#FFD60A]" />
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-sm">
                      {t('update.title', 'Nouvelle version disponible')}
                    </h3>
                    <p className="text-zinc-400 text-xs">
                      {t('update.subtitle', 'Métro-Taxi a été mis à jour')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleDismiss}
                  className="text-zinc-500 hover:text-white transition-colors p-1"
                  aria-label="Fermer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Description */}
              <p className="text-zinc-300 text-sm mb-4">
                {t('update.description', 'Rechargez pour profiter des dernières améliorations et corrections.')}
              </p>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  onClick={handleUpdate}
                  disabled={updating}
                  className="flex-1 bg-[#FFD60A] text-black font-bold hover:bg-[#E6C209] disabled:opacity-50"
                  data-testid="update-now-btn"
                >
                  {updating ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      {t('update.updating', 'Mise à jour...')}
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      {t('update.updateNow', 'Mettre à jour')}
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleDismiss}
                  variant="outline"
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  data-testid="update-later-btn"
                >
                  {t('update.later', 'Plus tard')}
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default UpdateNotification;
