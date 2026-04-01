// Service Worker Registration for PWA

// Store the waiting service worker for later activation
let waitingServiceWorker = null;

export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration.scope);
          
          // Check for updates every 5 minutes
          setInterval(() => {
            registration.update();
          }, 5 * 60 * 1000);
          
          // Check for updates on page focus
          document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
              registration.update();
            }
          });
          
          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New update available
                console.log('New content available!');
                waitingServiceWorker = newWorker;
                
                // Dispatch custom event to notify React components
                window.dispatchEvent(new CustomEvent('sw-update-available'));
              }
            });
          });
          
          // Listen for user's decision to update
          window.addEventListener('sw-do-update', () => {
            if (waitingServiceWorker) {
              waitingServiceWorker.postMessage({ type: 'SKIP_WAITING' });
            }
          });
          
          // Listen for controller change and refresh
          navigator.serviceWorker.addEventListener('controllerchange', () => {
            window.location.reload();
          });
        })
        .catch((error) => {
          console.log('SW registration failed: ', error);
        });
    });
  }
}

export function unregisterServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}

// Check if app is installed as PWA
export function isPWAInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

// Prompt to install PWA
let deferredPrompt = null;

export function initInstallPrompt() {
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing
    e.preventDefault();
    // Save the event for later
    deferredPrompt = e;
    console.log('Install prompt ready');
  });

  window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    deferredPrompt = null;
  });
}

export function canInstallPWA() {
  return deferredPrompt !== null;
}

export async function installPWA() {
  if (!deferredPrompt) {
    return false;
  }
  
  // Show the install prompt
  deferredPrompt.prompt();
  
  // Wait for the user's response
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`User response to install prompt: ${outcome}`);
  
  // Clear the deferred prompt
  deferredPrompt = null;
  
  return outcome === 'accepted';
}
