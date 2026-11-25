export const cities=['Bamako','Sikasso','Kayes','Ségou','Koutiala','Bougouni','Mopti','San','Kita'];
export function localToday(now=new Date()){return new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Bamako',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);}
export function validSearch(from:string,to:string,date:string,returnDate:string,round:boolean,count:number,today:string){return cities.includes(from)&&cities.includes(to)&&from!==to&&!!date&&date>=today&&(!round||(!!returnDate&&returnDate>=date))&&Number.isInteger(count)&&count>=1&&count<=10;}
