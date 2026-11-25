import { describe, it, expect } from 'vitest';
import { installPlatform } from './install-platform';
describe('Installation PWA', () => {
  it('détecte iPhone', () => expect(installPlatform('iPhone', 'iPhone', 5)).toBe('ios'));
  it('détecte iPad en mode bureau', () => expect(installPlatform('Macintosh Safari', 'MacIntel', 5)).toBe('ios'));
  it('détecte Android', () => expect(installPlatform('Linux Android', 'Linux', 5)).toBe('android'));
  it('distingue un Mac sans écran tactile', () => expect(installPlatform('Macintosh', 'MacIntel', 0)).toBe('desktop'));
  it('détecte Windows', () => expect(installPlatform('Windows Chrome', 'Win32', 0)).toBe('desktop'));
});
