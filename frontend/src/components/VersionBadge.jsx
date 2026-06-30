import React from 'react';

// IMPORTANT : à incrémenter à chaque déploiement majeur.
// Permet à Capitaine de vérifier visuellement quelle version est active sur son appareil.
// Si la version affichée diffère de celle annoncée par Charly, c'est qu'un déploiement n'a pas pris ou que le cache PWA tient.
export const APP_VERSION = 'v32.broadcast-mode-2026.06.30';

const VersionBadge = () => (
  <span
    className="text-[10px] text-zinc-600 hover:text-zinc-400 font-mono select-text"
    title={`Version actuelle : ${APP_VERSION}. Si tu vois une autre version, clique sur Deploy.`}
    data-testid="app-version-badge"
  >
    {APP_VERSION}
  </span>
);

export default VersionBadge;
