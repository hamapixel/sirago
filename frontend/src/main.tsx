import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './style.css';
import 'swiper/css';
import 'swiper/css/pagination';
import './responsive.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
