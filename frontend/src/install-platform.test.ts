import { describe, it, expect } from 'vitest';
import { installPlatform, isMacSafari } from './install-platform';
describe('Installation PWA', () => {
  it('détecte iPhone', () => expect(installPlatform('iPhone', 'iPhone', 5)).toBe('ios'));
  it('détecte iPad en mode bureau', () => expect(installPlatform('Macintosh Safari', 'MacIntel', 5)).toBe('ios'));
  it('détecte Android', () => expect(installPlatform('Linux Android', 'Linux', 5)).toBe('android'));
  it('distingue un Mac sans écran tactile', () => expect(installPlatform('Macintosh', 'MacIntel', 0)).toBe('desktop'));
  it('détecte Windows', () => expect(installPlatform('Windows Chrome', 'Win32', 0)).toBe('desktop'));
});

it('distingue Safari Mac de Chrome et Edge',()=>{expect(isMacSafari('Version/17.0 Safari/605.1','MacIntel')).toBe(true);expect(isMacSafari('Chrome/140.0 Safari/537.36','MacIntel')).toBe(false);expect(isMacSafari('Edg/140.0 Safari/537.36','Win32')).toBe(false)});
