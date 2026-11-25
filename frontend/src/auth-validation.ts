export const phoneValid=(phone:string)=>/^(?:\+223)?[0-9]{8}$/.test(phone.replace(/[\s-]/g,''));
export const emailValid=(email:string)=>!email.trim()||/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
export const passwordValid=(password:string,confirmation:string)=>password.length>=8&&password.length<=128&&password===confirmation;
