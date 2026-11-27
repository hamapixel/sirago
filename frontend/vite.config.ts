import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
const proxy = { '/api': {target: process.env.API_PROXY_TARGET || 'http://localhost:8000'}, '/admin': {target: process.env.API_PROXY_TARGET || 'http://localhost:8000'}, '/static': {target: process.env.API_PROXY_TARGET || 'http://localhost:8000'} };
export default defineConfig({
  plugins: [react(), VitePWA({registerType:'autoUpdate', includeAssets:['logo.svg','coach.svg','icons/*.png','images/slides/*.webp','images/partners/*.{webp,png,jpg,jpeg}'], manifest:{name:'SiraGo — Voyagez autrement',short_name:'SiraGo',lang:'fr',theme_color:'#103B38',background_color:'#103B38',display:'standalone',start_url:'/',icons:[{src:'/icons/icon-192.png',sizes:'192x192',type:'image/png',purpose:'any'},{src:'/icons/icon-512.png',sizes:'512x512',type:'image/png',purpose:'any'},{src:'/logo.svg',sizes:'any',type:'image/svg+xml',purpose:'any'}]},workbox:{importScripts:['/push-events.js'],navigateFallbackDenylist:[/^\/api\//,/^\/admin\//,/^\/static\//]}})],
  server: {host:'0.0.0.0',port:5173,strictPort:true,proxy},
  preview: {port:5173,strictPort:true,proxy}
});
