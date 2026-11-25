import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
const proxy = { '/api': {target: process.env.API_PROXY_TARGET || 'http://localhost:8000'}, '/admin': {target: process.env.API_PROXY_TARGET || 'http://localhost:8000'}, '/static': {target: process.env.API_PROXY_TARGET || 'http://localhost:8000'} };
export default defineConfig({
  plugins: [react(), VitePWA({registerType:'autoUpdate', includeAssets:['logo.svg','coach.svg'], manifest:{name:'SiraGo — Voyagez autrement',short_name:'SiraGo',lang:'fr',theme_color:'#103B38',background_color:'#F7F8FA',display:'standalone',start_url:'/',icons:[{src:'/logo.svg',sizes:'any',type:'image/svg+xml',purpose:'any'}]},workbox:{navigateFallbackDenylist:[/^\/api\//,/^\/admin\//,/^\/static\//]}})],
  server: {host:'0.0.0.0',port:5173,strictPort:true,proxy},
  preview: {port:5173,strictPort:true,proxy}
});
