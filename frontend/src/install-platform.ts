export type InstallPlatform = 'ios' | 'android' | 'desktop';
export function installPlatform(userAgent: string, platform: string, maxTouchPoints: number): InstallPlatform {
  if (/iPhone|iPad|iPod/i.test(userAgent) || (platform === 'MacIntel' && maxTouchPoints > 1)) return 'ios';
  if (/Android/i.test(userAgent)) return 'android';
  return 'desktop';
}

export function isMacSafari(userAgent:string,platform:string){return /Mac/i.test(platform)&&/Safari\//i.test(userAgent)&&!/(Chrome|Chromium|Edg|OPR|Firefox)\//i.test(userAgent)}
