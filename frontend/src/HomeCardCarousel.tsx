import {Children,useEffect,useRef,useState,type ReactNode} from 'react';
import {Swiper,SwiperSlide} from 'swiper/react';
import {A11y} from 'swiper/modules';
import type {Swiper as SwiperInstance} from 'swiper';
import './home-card-carousel.css';

export function HomeCardCarousel({label,children,kind}:{label:string;children:ReactNode;kind:'trips'|'partners'|'companies'}){
 const slides=Children.toArray(children);
 const slider=useRef<SwiperInstance|null>(null);
 const [reduced,setReduced]=useState(false);
 useEffect(()=>{
  const media=window.matchMedia('(prefers-reduced-motion: reduce)');
  const update=()=>setReduced(media.matches);
  update();media.addEventListener('change',update);
  return()=>media.removeEventListener('change',update);
 },[]);
 const multiple=slides.length>1;
 if(!slides.length)return null;
 return <div role="region" aria-label={label} aria-roledescription="carrousel" className="home-card-carousel-region" tabIndex={multiple?0:undefined}
  onKeyDown={e=>{if(!multiple||e.target!==e.currentTarget)return;if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();if(e.key==='ArrowLeft')slider.current?.slidePrev();else slider.current?.slideNext()}}}>
  <Swiper className={'home-card-carousel home-card-carousel-'+kind+(multiple?' has-multiple':'')}
    modules={[A11y]} direction="horizontal" onSwiper={instance=>{slider.current=instance}} simulateTouch={true} allowTouchMove={multiple}
    grabCursor={multiple} threshold={6} touchAngle={40} preventClicks={true} preventClicksPropagation={true}
    speed={reduced?0:320} watchOverflow={true} loop={false}
    spaceBetween={12} slidesPerView={kind==='companies'?'auto':multiple?(kind==='trips'?1.06:1.12):1}
    breakpoints={{640:{slidesPerView:kind==='companies'?'auto':multiple?2:1,spaceBetween:14}}}
    navigation={false} pagination={false}
    a11y={{enabled:true,slideLabelMessage:'{{index}} sur {{slidesLength}}'}}>
    {slides.map((child,i)=><SwiperSlide key={i}>{child}</SwiperSlide>)}
  </Swiper>
 </div>;
}
