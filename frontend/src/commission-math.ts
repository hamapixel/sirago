export const MAX_RATE=1000;
export const MAX_PRICE=10000000;
export const MAX_VOLUME=10000;
export function boundedNumber(value:number,max:number){return Number.isFinite(value)?Math.min(max,Math.max(0,Math.round(value))):0}
export function commissionQuote(price:number,bps:number,volume:number){
 const amount=boundedNumber(price,MAX_PRICE),rate=boundedNumber(bps,MAX_RATE),count=boundedNumber(volume,MAX_VOLUME);
 const fee=Math.floor((amount*rate+5000)/10000);
 return {amount,rate,count,fee,net:amount-fee,day:fee*count,month:fee*count*30};
}
export const rateText=(bps:number)=>new Intl.NumberFormat('fr-FR',{maximumFractionDigits:2}).format(bps/100)+' %';
export function parseRate(raw:string){const value=raw.trim().replace(',','.');if(!/^\d{1,2}(?:\.\d{1,2})?$/.test(value))return null;const bps=Math.round(Number(value)*100);return bps<=MAX_RATE?bps:null}
