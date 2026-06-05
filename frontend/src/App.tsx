import { useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import './App.css';

function App() {
  useEffect(() => {
    const apiKey = (import.meta.env.VITE_ADREV_API_KEY || '').trim();
    if (!apiKey) {
      return;
    }

    const startedFlag = 'solarware:adrev:layer:started';
    if (sessionStorage.getItem(startedFlag) === '1') {
      return;
    }

    const baseUrl = (
      import.meta.env.VITE_ADREV_BASE_URL || 'https://www.adrevtechnologies.com'
    ).replace(/\/$/, '');

    const scriptSrc = `${baseUrl}/sdk/adrev-runtime-layer.js`;
    const scriptId = 'adrev-runtime-layer-sdk';

    const startLayer = () => {
      const layer = (window as any).AdRevLayer;
      if (!layer || typeof layer.start !== 'function') {
        return;
      }

      const storedUserId =
        localStorage.getItem('solarware_user_id') ||
        localStorage.getItem('solarware:user_id') ||
        '';

      const externalUserId =
        storedUserId ||
        `solarware_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;

      void layer
        .start({
          apiKey,
          baseUrl,
          orgId: (import.meta.env.VITE_ADREV_ORG_ID || '').trim() || undefined,
          campaignId:
            (import.meta.env.VITE_ADREV_CAMPAIGN_ID || '').trim() || undefined,
          externalUserId,
          placement: 'solarware-dashboard',
        })
        .then(() => {
          sessionStorage.setItem(startedFlag, '1');
        })
        .catch((error: unknown) => {
          console.error('[Solarware] adrev-layer:start_failed', error);
        });
    };

    const existing = document.getElementById(scriptId) as HTMLScriptElement | null;
    if (existing) {
      if ((window as any).AdRevLayer) {
        startLayer();
      } else {
        existing.addEventListener('load', startLayer, { once: true });
      }
      return;
    }

    const script = document.createElement('script');
    script.id = scriptId;
    script.src = scriptSrc;
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.addEventListener('load', startLayer, { once: true });
    script.addEventListener('error', () => {
      console.error('[Solarware] adrev-layer:script_load_failed', { scriptSrc });
    });

    document.head.appendChild(script);
  }, []);

  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;
