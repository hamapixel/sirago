import { useEffect, useState } from 'react';
import { ArrowDownToLine, Share, Smartphone, X } from 'lucide-react';
import { installPlatform, isMacSafari } from './install-platform';

interface InstallPromptEvent extends Event {
  prompt(): Promise<unknown>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

// Capture the event as soon as the module loads, even if the home view
// is temporarily unmounted. Each native prompt can only be used once.
let pendingPrompt: InstallPromptEvent | null = null;
const subscribers = new Set<() => void>();
const notify = () => subscribers.forEach(fn => fn());
const displayMode = window.matchMedia('(display-mode: standalone)');
let installedThisSession = false;
function isStandalone() {
  return installedThisSession || displayMode.matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true;
}
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  pendingPrompt = event as InstallPromptEvent;
  notify();
});
window.addEventListener('appinstalled', () => {
  pendingPrompt = null;
  installedThisSession = true;
  notify();
});
displayMode.addEventListener('change', notify);

export default function InstallApp() {
  const [available, setAvailable] = useState(Boolean(pendingPrompt));
  const [installed, setInstalled] = useState(isStandalone);
  const [help, setHelp] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const platform = installPlatform(navigator.userAgent, navigator.platform, navigator.maxTouchPoints);
  const macSafari = platform === 'desktop' && isMacSafari(navigator.userAgent, navigator.platform);

  useEffect(() => {
    const sync = () => {
      setAvailable(Boolean(pendingPrompt));
      setInstalled(isStandalone());
    };
    subscribers.add(sync);
    sync();
    return () => { subscribers.delete(sync); };
  }, []);

  async function install() {
    if (busy || installed) return;
    const event = pendingPrompt;
    if (!event) {
      setHelp(value => !value);
      return;
    }
    pendingPrompt = null;
    notify();
    setBusy(true);
    setHelp(false);
    setMessage('');
    try {
      await event.prompt();
      const choice = await event.userChoice;
      if (choice.outcome === 'accepted') {
        setMessage('Installation acceptée. Suivez les indications de votre navigateur.');
      } else {
        setMessage('Installation annulée. Vous pouvez réessayer depuis le menu du navigateur.');
        setHelp(true);
      }
    } catch {
      setMessage('Installation directe indisponible. Consultez les étapes ci-dessous.');
      setHelp(true);
    } finally {
      setBusy(false);
    }
  }

  if (installed) return null;

  return (
    <section className="install-card" aria-label="Installer SiraGo">
      <div className="install-content">
        <div className="install-logo"><img src="/logo.svg" alt="" width="48" height="48"/></div>
        <div className="install-copy">
          <h2>SiraGo, toujours avec vous</h2>
          <p>Sur téléphone, tablette ou ordinateur compatible.</p>
        </div>
        <button type="button" className="install-button" disabled={busy}
          aria-expanded={!available ? help : undefined} aria-controls={!available ? 'sirago-install-help' : undefined}
          onClick={install}>
          <ArrowDownToLine size={19} aria-hidden="true"/>
          <span>{busy ? 'Installation…' : 'Installer SiraGo'}</span>

        </button>
      </div>
      {message && <p className="install-status" role="status">{message}</p>}
      {help && <div className="install-help" id="sirago-install-help">
        <div className="install-help-title"><strong>Comment installer SiraGo ?</strong><button type="button" className="icon-button" aria-label="Fermer les instructions" onClick={()=>setHelp(false)}><X size={19}/></button></div>
        {platform === 'ios' ? <ol>
          <li>Ouvrez cette page dans Safari.</li>
          <li>Appuyez sur Partager <Share size={16} aria-hidden="true"/>.</li>
          <li>Choisissez « Sur l’écran d’accueil », puis « Ajouter ».</li>
        </ol> : platform === 'android' ? <ol>
          <li>Ouvrez SiraGo dans Chrome.</li>
          <li>Dans le menu ⋮, choisissez « Installer l’application » ou « Ajouter à l’écran d’accueil ».</li>
          <li>Confirmez l’installation si proposée.</li>
        </ol> : macSafari ? <ol><li>Dans Safari sur Mac (macOS Sonoma ou ultérieur), ouvrez le menu Fichier.</li><li>Choisissez « Ajouter au Dock », puis confirmez.</li><li>Si cette option est absente, essayez Chrome ou Edge.</li></ol> : <ol>
          <li>Ouvrez SiraGo dans Chrome ou Edge.</li>
          <li>Utilisez l’icône d’installation dans la barre d’adresse ou le menu du navigateur.</li>
          <li>Confirmez l’installation si proposée.</li>
        </ol>}
        <p><Smartphone size={16} aria-hidden="true"/> Utilisez l’adresse HTTPS de SiraGo sur votre appareil. Si le menu d’installation est absent, ouvrez la page dans un navigateur compatible plutôt que dans une application de messagerie. Vous pouvez toujours utiliser SiraGo dans le navigateur. Sur ce PC, localhost sert uniquement aux tests.</p>
      </div>}
    </section>
  );
}
