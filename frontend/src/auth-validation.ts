export const phoneValid=(phone:string)=>/^(?:\+223)?[0-9]{8}$/.test(phone.replace(/[\s-]/g,''));
export const emailValid=(email:string)=>!email.trim()||/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
export const passwordChecks=(password:string,confirmation:string)=>({
 length:password.length>=8&&password.length<=128,
 matching:password.length>0&&password===confirmation,
});
export const passwordValid=(password:string,confirmation:string)=>{
 const checks=passwordChecks(password,confirmation);
 return checks.length&&checks.matching;
};
