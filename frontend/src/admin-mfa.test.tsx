import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import AdminMfaChallenge,{validMfaCode} from './AdminMfaChallenge';
import {isMfaChallenge,type Account} from './auth-api';

describe('Superadmin MFA',()=>{
 it('distinguishes a pending challenge from an authenticated profile',()=>{
  expect(isMfaChallenge({mfa_required:true,stage:'enroll'})).toBe(true);
  expect(isMfaChallenge({mfa_required:true,stage:'verify'})).toBe(true);
  expect(isMfaChallenge({role:'ADMIN'} as Account)).toBe(false);
 });
 it('validates six ASCII digits including leading zero',()=>{
  expect(validMfaCode('012345','totp')).toBe(true);
  for(const code of ['12345','1234567','abcdef','１２３４５６'])expect(validMfaCode(code,'totp')).toBe(false);
 });
 it('accepts only the expected activation and recovery formats',()=>{
  expect(validMfaCode('a'.repeat(48),'activation')).toBe(true);
  expect(validMfaCode('A'.repeat(32),'recovery')).toBe(true);
  expect(validMfaCode('0'.repeat(48),'recovery')).toBe(false);
  expect(validMfaCode('z'.repeat(48),'activation')).toBe(false);
 });
 it('renders enrollment without a secret or QR before operator validation',()=>{
  const html=renderToStaticMarkup(<AdminMfaChallenge challenge={{mfa_required:true,stage:'enroll'}}/>);
  expect(html).toContain('Code privé');
  expect(html).toContain('Afficher le QR code');
  expect(html).not.toContain('data:image/png');
  expect(html).toContain('disabled=""');
 });
 it('renders verification and recovery option without revealing enrollment secret',()=>{
  const html=renderToStaticMarkup(<AdminMfaChallenge challenge={{mfa_required:true,stage:'verify'}}/>);
  expect(html).toContain('Code à six chiffres');
  expect(html).toContain('Utiliser un code de récupération');
  expect(html).toContain('Annuler et se reconnecter');
  expect(html).not.toContain('Afficher le QR code');
 });
});
