import {it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {renderToStaticMarkup} from 'react-dom/server';
import AuthPage from './AuthPage';
import {LanguageSelect,LanguageFlag,translateText} from './i18n';
it('conserve un sélecteur natif accessible avec les trois langues et un drapeau SVG',()=>{
 const html=renderToStaticMarkup(<LanguageSelect/>);
 expect(html).toContain('language-pill');expect(html).toContain('language-flag');expect(html).toContain('<select');expect(html).toContain('Français');expect(html).toContain('English');expect(html).toContain('Bamanankan');
 expect(renderToStaticMarkup(<LanguageFlag lang="bm"/>)).toContain('#14a653');
 expect(renderToStaticMarkup(<LanguageFlag lang="en"/>)).toContain('#17376b');
});
it('conserve les champs de connexion sans préremplir de données personnelles',()=>{
 const html=renderToStaticMarkup(<AuthPage register={false}/>);
 expect(html).toContain('auth-login');expect(html).toContain('/brand-mark.svg');expect(html).toContain('name="username"');expect(html).toContain('autoComplete="username"');expect(html).toContain('name="password"');expect(html).toContain('current-password');expect(html).toContain('disabled=""');expect(html).toContain('Retour à l’accueil');
});
it('traduit les libellés de connexion',()=>{expect(translateText('Bienvenue sur SiraGo','en')).toBe('Welcome to SiraGo');expect(translateText('Bienvenue sur SiraGo','bm')).not.toBe('Bienvenue sur SiraGo')});

it('garde le préfixe malien sur une ligne sans comprimer le champ téléphone',()=>{
 const html=renderToStaticMarkup(<AuthPage register selection={{out:1,count:1}}/>);
 expect(html).toContain('class="auth-phone"><span>+223</span>');
 expect(html).toContain('autoComplete="tel-national"');
 const css=readFileSync('src/auth.css','utf8');
 expect(css).toMatch(/\.auth-fields \.auth-phone>span\{[^}]*flex:0 0 64px[^}]*white-space:nowrap/);
 expect(css).toMatch(/\.auth-fields \.auth-phone>input\[type=tel\]\{[^}]*flex:1 1 0;width:0;min-width:0/);
});
