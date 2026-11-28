import {Children,useEffect,useState,type ReactNode} from 'react';
import {Swiper,SwiperSlide} from 'swiper/react';
import {A11y,Navigation,Pagination} from 'swiper/modules';
import 'swiper/css/navigation';
import './home-card-carousel.css';

export function HomeCardCarousel({label,children,kind}:{label:string;children:ReactNode;kind:'trips'|'partners'}){
 const slides=Children.toArray(children);
 const [reduced,setReduced]=useState(false);
 useEffect(()=>{
  const media=window.matchMedia('(prefers-reduced-motion: reduce)');
  const update=()=>setReduced(media.matches);
  update();media.addEventListener('change',update);
  return()=>media.removeEventListener('change',update);
 },[]);
 const multiple=slides.length>1;
 if(!slides.length)return null;
 return <div role="region" aria-label={label} aria-roledescription="carrousel" className="home-card-carousel-region">
  <Swiper className={'home-card-carousel home-card-carousel-'+kind+(multiple?' has-multiple':'')}
    modules={[A11y,Navigation,Pagination]} direction="horizontal" simulateTouch={true} allowTouchMove={multiple}
    grabCursor={multiple} threshold={6} touchAngle={40} preventClicks={true} preventClicksPropagation={true}
    speed={reduced?0:320} watchOverflow={true} loop={false}
    spaceBetween={12} slidesPerView={multiple?(kind==='trips'?1.06:1.12):1}
    breakpoints={{640:{slidesPerView:multiple?2:1,spaceBetween:14}}}
    navigation={multiple} pagination={multiple?{clickable:true,dynamicBullets:true}:false}
    a11y={{enabled:true,prevSlideMessage:'Carte précédente',nextSlideMessage:'Carte suivante',firstSlideMessage:'Première carte',lastSlideMessage:'Dernière carte',paginationBulletMessage:'Afficher la carte {{index}}',slideLabelMessage:'{{index}} sur {{slidesLength}}'}}>
    {slides.map((child,i)=><SwiperSlide key={i}>{child}</SwiperSlide>)}
  </Swiper>
 </div>;
}
