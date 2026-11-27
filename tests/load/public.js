import http from 'k6/http';
import { check, sleep, fail } from 'k6';

const vus = Number(__ENV.VUS || '10');
const date = __ENV.LOAD_DATE || '';
if (![10,50,100,200].includes(vus)) throw new Error('Use a single approved stage: 10, 50, 100 or 200 VUs.');
if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error('LOAD_DATE must be the seeded date.');
// This intentionally has no external URL override. Run on the dedicated load edge network.
const base = 'http://gateway:8080';
const params = (name) => ({headers: {'Host':'load.example.test','X-Forwarded-Proto':'https'},tags:{name},timeout:'10s'});
const searchPath = '/api/v1/travel/search/?origin=Bamako&destination=Sikasso&date='+date+'&passengers=1';
export const options = {
  vus,
  duration:'60s',
  gracefulStop:'15s',
  thresholds:{
    http_req_failed:[{threshold:'rate<0.01',abortOnFail:true,delayAbortEval:'20s'}],
    checks:['rate>0.99'],
    http_req_duration:['p(95)<1000','p(99)<2500'],
    'http_req_duration{name:search}':['p(95)<1000'],
  },
  summaryTrendStats:['avg','med','p(90)','p(95)','p(99)','max'],
};
function get(path,name){return http.get(base+path,params(name))}
function parsed(r){try{return r.json()}catch(_){return null}}
export function setup(){
  const health=get('/api/v1/health/','health');
  const search=get(searchPath,'search');
  const body=parsed(search);
  if(health.status!==200 || search.status!==200 || !body || body.total!==100)
    fail('Unexpected fixture or unhealthy stack. No load test started.');
}
export default function(){
  const home=get('/api/v1/travel/home/','home');
  const h=parsed(home);
  check(home,{'home 200 and fixture present':r=>r.status===200 && Array.isArray(h?.departures) && h.departures.length>0});
  const search=get(searchPath,'search');
  const s=parsed(search);
  check(search,{'search 200 and 100 departures':r=>r.status===200 && s?.total===100 && Array.isArray(s.items) && s.items.length>0});
  sleep(1+Math.random()*2);
}
