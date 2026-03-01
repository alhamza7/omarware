// ── Luxury channel icons for Noor Al-Nebras ──────────────
// Each icon uses the platform's recognizable silhouette
// rendered as clean inline SVGs at any size

interface IconProps {
  className?: string;
}

function WhatsAppIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 2C6.48 2 2 6.48 2 12c0 1.77.46 3.43 1.27 4.88L2 22l5.23-1.24A9.96 9.96 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.62 0-3.13-.47-4.41-1.28l-.31-.19-3.24.77.81-3.16-.21-.33A7.96 7.96 0 014 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8zm4.38-5.97c-.24-.12-1.42-.7-1.64-.78-.22-.08-.38-.12-.54.12-.16.24-.62.78-.76.94-.14.16-.28.18-.52.06-.24-.12-1.01-.37-1.93-1.18-.71-.63-1.19-1.41-1.33-1.65-.14-.24-.02-.37.1-.49.11-.11.24-.28.36-.42.12-.14.16-.24.24-.4.08-.16.04-.3-.02-.42-.06-.12-.54-1.3-.74-1.78-.2-.47-.4-.4-.54-.41h-.46c-.16 0-.42.06-.64.3-.22.24-.84.82-.84 2s.86 2.32.98 2.48c.12.16 1.7 2.6 4.12 3.64.58.25 1.03.4 1.38.51.58.18 1.1.16 1.52.1.46-.07 1.42-.58 1.62-1.14.2-.56.2-1.04.14-1.14-.06-.1-.22-.16-.46-.28z" />
    </svg>
  );
}

function InstagramIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 01-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 017.8 2zm-.2 2A3.6 3.6 0 004 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 003.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6zm9.65 1.5a1.25 1.25 0 110 2.5 1.25 1.25 0 010-2.5zM12 7a5 5 0 110 10 5 5 0 010-10zm0 2a3 3 0 100 6 3 3 0 000-6z" />
    </svg>
  );
}

function XTwitterIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function SnapchatIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 2c-3.18 0-5.2 2.14-5.2 5.3 0 .6.05 1.19.14 1.72-.6.08-1.27.22-1.73.42-.4.17-.67.5-.67.86 0 .76.93 1.1 1.88 1.38.18.05.34.1.44.15.12.06.16.12.14.22-.12.62-.52 1.2-1.2 1.74-.62.5-1.36.84-1.9 1.04-.3.11-.5.38-.5.7 0 .47.37.86.82.97.56.14 1.22.2 1.68.5.38.24.58.72.92 1.15.4.5.96 1.15 2.28 1.15.84 0 1.5-.2 2.06-.42a6.7 6.7 0 011.84-.42c.64 0 1.24.16 1.84.42.56.22 1.22.42 2.06.42 1.32 0 1.88-.66 2.28-1.15.34-.43.54-.91.92-1.15.46-.3 1.12-.36 1.68-.5.45-.11.82-.5.82-.97 0-.32-.2-.59-.5-.7-.54-.2-1.28-.54-1.9-1.04-.68-.54-1.08-1.12-1.2-1.74-.02-.1.02-.16.14-.22.1-.05.26-.1.44-.15.95-.28 1.88-.62 1.88-1.38 0-.36-.27-.69-.67-.86-.46-.2-1.13-.34-1.73-.42.09-.53.14-1.12.14-1.72C17.2 4.14 15.18 2 12 2z" />
    </svg>
  );
}

function TikTokIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M16.6 5.82A4.278 4.278 0 0113.25 3h-3.1v12.4a2.592 2.592 0 01-2.593 2.545 2.592 2.592 0 01-2.593-2.593 2.592 2.592 0 012.593-2.593c.265 0 .52.04.76.114V9.702a5.765 5.765 0 00-.76-.051 5.768 5.768 0 00-5.767 5.767 5.768 5.768 0 005.767 5.767 5.768 5.768 0 005.767-5.767V9.34a7.392 7.392 0 004.325 1.392V7.58a4.283 4.283 0 01-2.394-.76z" />
    </svg>
  );
}

function TelegramIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42 10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l.002.001-.314 4.692c.46 0 .663-.211.921-.46l2.211-2.15 4.599 3.397c.848.467 1.457.227 1.668-.785l3.019-14.228c.309-1.239-.473-1.8-1.282-1.434z" />
    </svg>
  );
}

function WebsiteIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm6.918 6h-3.215a15.876 15.876 0 00-1.396-3.704A8.026 8.026 0 0118.918 8zM12 4.04c.782 1.04 1.414 2.2 1.856 3.46h-3.712c.442-1.26 1.074-2.42 1.856-3.46zM4.26 14a7.93 7.93 0 010-4h3.48a16.533 16.533 0 000 4H4.26zm.822 2h3.215a15.876 15.876 0 001.396 3.704A8.026 8.026 0 015.082 16zM8.297 8H5.082a8.026 8.026 0 014.611-3.704A15.876 15.876 0 008.297 8zM12 19.96c-.782-1.04-1.414-2.2-1.856-3.46h3.712c-.442 1.26-1.074 2.42-1.856 3.46zM14.34 14H9.66a14.768 14.768 0 010-4h4.68a14.768 14.768 0 010 4zm.353 5.704A15.876 15.876 0 0016.089 16h3.215a8.026 8.026 0 01-4.611 3.704zM16.26 14a16.533 16.533 0 000-4h3.48a7.93 7.93 0 010 4h-3.48z" />
    </svg>
  );
}

function EmailIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-.4 4.25l-7.07 4.42c-.32.2-.74.2-1.06 0L4.4 8.25a.85.85 0 11.9-1.44L12 11l5.7-4.19a.85.85 0 01.9 1.44z" />
    </svg>
  );
}

function StoreIcon({ className = "w-4 h-4" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M20 4H4v2h16V4zm1 10v-2l-1-5H4l-1 5v2h1v6h10v-6h4v6h2v-6h1zm-9 4H6v-4h6v4z" />
    </svg>
  );
}

// ── Exported map for easy usage ──────────────────────────
export const channelIcons: Record<string, React.ReactNode> = {
  whatsapp: <WhatsAppIcon />,
  instagram: <InstagramIcon />,
  x: <XTwitterIcon />,
  snapchat: <SnapchatIcon />,
  tiktok: <TikTokIcon />,
  telegram: <TelegramIcon />,
  website: <WebsiteIcon />,
  email: <EmailIcon />,
  store: <StoreIcon />,
};

// For cases where you need a specific size
export function getChannelIcon(channel: string, className = "w-4 h-4"): React.ReactNode {
  const icons: Record<string, (props: IconProps) => React.ReactNode> = {
    whatsapp: WhatsAppIcon,
    instagram: InstagramIcon,
    x: XTwitterIcon,
    snapchat: SnapchatIcon,
    tiktok: TikTokIcon,
    telegram: TelegramIcon,
    website: WebsiteIcon,
    email: EmailIcon,
    store: StoreIcon,
  };
  const Icon = icons[channel];
  return Icon ? <Icon className={className} /> : null;
}
