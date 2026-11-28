import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {CompanyOptions} from './TravelResults';
it('affiche les compagnies réelles dans un carrousel avec leur logo, compte et sélection',()=>{const html=renderToStaticMarkup(<CompanyOptions companies={[{id:1,name:'Transport A',departures:2},{id:2,name:'Transport B',departures:1},{id:3,name:'Transport C',departures:4}]} selected="2" onChoose={()=>{}}/>);for(const s of ['Compagnies disponibles (3)','home-card-carousel-companies','Transport A','Transport B','Transport C','/api/v1/travel/partners/2/logo/','2 départs disponibles','aria-pressed="true"','Toutes'])expect(html).toContain(s);expect(html.match(/class="swiper-slide"/g)?.length).toBe(3);expect(html).not.toContain('swiper-button-next')});
