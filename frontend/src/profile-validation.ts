export function initials(first:string,last:string){return [first,last].map(n=>Array.from(n.trim())[0]||'').join('').toLocaleUpperCase('fr')||'SG'}
export function validProfileName(name:string){return name.trim().length>0&&name.length<=150&&!/[\x00-\x1F]/.test(name)}
