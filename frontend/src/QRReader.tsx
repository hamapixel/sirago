import {useEffect,useRef,useState} from 'react';
import {Camera,ImagePlus,Keyboard,ScanLine,ShieldCheck} from 'lucide-react';
import jsQR from 'jsqr';

export const validTicketCode=(value:string)=>/^SRG-TEST-[0-9A-F]{32}$/.test(value.trim().toUpperCase());
export function decodeTicketPixels(data:Uint8ClampedArray,width:number,height:number){
 const result=jsQR(data,width,height,{inversionAttempts:'attemptBoth'});
 return result?.data&&validTicketCode(result.data)?result.data.trim().toUpperCase():null;
}
function decodeSource(source:CanvasImageSource,width:number,height:number,canvas:HTMLCanvasElement,max:number){
 const scale=Math.min(1,max/Math.max(width,height));
 canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 if(!ctx)throw new Error('Lecture image indisponible.');
 ctx.drawImage(source,0,0,canvas.width,canvas.height);
 const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
 return decodeTicketPixels(pixels.data,pixels.width,pixels.height);
}
type Mode='camera'|'image'|'manual';
type Props={busy:boolean;code:string;onCode:(s:string)=>void;onLookup:(s:string)=>Promise<void>;onError:(s:string)=>void};
export default function QRReader({busy,code,onCode,onLookup,onError}:Props){
 const [mode,setMode]=useState<Mode>('camera'),[running,setRunning]=useState(false),[ready,setReady]=useState(false),[reading,setReading]=useState(false);
 const video=useRef<HTMLVideoElement>(null),fileInput=useRef<HTMLInputElement>(null),callbacks=useRef({onLookup,onError}),generation=useRef(0);
 callbacks.current={onLookup,onError};
 useEffect(()=>()=>{generation.current++},[]);
 function switchMode(next:Mode){generation.current++;setRunning(false);setReading(false);setReady(false);onError('');setMode(next)}
 useEffect(()=>{
  if(!running||mode!=='camera'||busy)return;
  let active=true;let stream:MediaStream|undefined;let timer:number|undefined;
  const canvas=document.createElement('canvas');
  async function start(){
   try{
    if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia)throw new Error('Caméra indisponible : utilisez localhost ou HTTPS, ou importez une image.');
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}},audio:false});
    if(!active){stream.getTracks().forEach(t=>t.stop());return}
    if(!video.current)throw new Error('Caméra indisponible.');
    video.current.srcObject=stream;await video.current.play();if(!active)return;setReady(true);
    const scan=()=>{
     if(!active||!video.current)return;
     try{
      const v=video.current;
      if(v.readyState>=2&&v.videoWidth&&v.videoHeight){
       const code=decodeSource(v,v.videoWidth,v.videoHeight,canvas,1280);
       if(code){setRunning(false);setReady(false);stream?.getTracks().forEach(t=>t.stop());void callbacks.current.onLookup(code);return}
      }
     }catch{callbacks.current.onError('Lecture caméra interrompue. Essayez une image.');setRunning(false);return}
     if(active)timer=window.setTimeout(scan,260);
    };
    scan();
   }catch(e){if(active){callbacks.current.onError(e instanceof Error&&e.name==='NotAllowedError'?'Autorisez la caméra dans votre navigateur.':e instanceof Error?e.message:'Caméra indisponible.');setRunning(false);setReady(false)}}
  }
  void start();
  return()=>{active=false;stream?.getTracks().forEach(t=>t.stop());if(timer!==undefined)window.clearTimeout(timer)};
 },[running,mode,busy]);
 async function readImage(file:File){
  if(reading||busy)return;
  if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>10*1024*1024){onError('Choisissez une image PNG, JPEG ou WebP de 10 Mo maximum.');return}
  const token=++generation.current;setReading(true);onError('');
  let bitmap:ImageBitmap|undefined;
  try{
   bitmap=await createImageBitmap(file);
   if(token!==generation.current)return;
   const canvas=document.createElement('canvas');
   let decoded=decodeSource(bitmap,bitmap.width,bitmap.height,canvas,2400);
   if(!decoded)decoded=decodeSource(bitmap,bitmap.width,bitmap.height,canvas,1200);
   if(!decoded)throw new Error('QR SiraGo TEST non reconnu. Recadrez la photo autour du QR code ou saisissez sa référence.');
   if(token===generation.current)await callbacks.current.onLookup(decoded);
  }catch(e){if(token===generation.current)callbacks.current.onError(e instanceof Error?e.message:'Impossible de lire cette image.')}
  finally{bitmap?.close();if(token===generation.current)setReading(false)}
 }
 return <section className="qr-reader" aria-label="Scanner un billet"><div className="qr-mode" role="group" aria-label="Mode de lecture">{([{id:'camera',label:'Caméra',Icon:Camera},{id:'image',label:'Image',Icon:ImagePlus},{id:'manual',label:'Manuel',Icon:Keyboard}] as const).map(({id,label,Icon})=><button type="button" key={id} aria-pressed={mode===id} disabled={busy} onClick={()=>switchMode(id)}><Icon size={19}/>{label}</button>)}</div>
 {mode==='camera'&&<><div className="qr-view">{running&&<video ref={video} autoPlay muted playsInline className="qr-video"/>}<div className="qr-target" aria-hidden="true"><i/><i/><i/><i/>{!running&&<ScanLine size={42}/>}<span className={ready&&running?'qr-line active':'qr-line'}/></div><span className="qr-view-label">{running?(ready?'Présentez le QR code':'Ouverture de la caméra…'):'Caméra PC ou téléphone'}</span></div><button type="button" className="primary" disabled={busy} onClick={()=>{onError('');setReady(false);setRunning(v=>!v)}}><Camera size={20}/>{running?'Arrêter la caméra':'Ouvrir la caméra'}</button><small>Autorisez la webcam et présentez un billet devant l’objectif.</small></>}
 {mode==='image'&&<><input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void readImage(file)}}/><button type="button" className="qr-upload" disabled={busy||reading} onClick={()=>fileInput.current?.click()}><ImagePlus size={34}/><strong>{reading?'Lecture du QR…':'Importer une image du billet'}</strong><small>PNG, JPEG ou WebP · 10 Mo maximum</small></button><small>Une capture d’écran du QR code suffit. Aucun fichier n’est envoyé au serveur.</small></>}
 {mode==='manual'&&<form className="boarding-manual" onSubmit={e=>{e.preventDefault();void onLookup(code)}}><label>Référence du billet<input value={code} onChange={e=>onCode(e.target.value)} maxLength={60} autoComplete="off" placeholder="SRG-TEST-…" disabled={busy}/></label><button className="primary" disabled={busy||!code.trim()} type="submit">{busy?'Recherche…':'Vérifier le billet'}</button></form>}
 <small className="qr-privacy"><ShieldCheck size={15}/> Lecture locale et vérification sécurisée.</small></section>
}
