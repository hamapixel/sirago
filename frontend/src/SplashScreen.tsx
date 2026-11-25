export default function SplashScreen({message='Chargement…'}:{message?:string}){
 return <main className="sirago-splash" aria-label="Démarrage de SiraGo"><div className="sirago-splash-content">
 <img className="sirago-splash-logo" src="/logo.svg" alt="" width={110} height={110}/>
 <h1 className="sirago-splash-name">SiraGo</h1>
 <p className="sirago-splash-tagline">Ka billet ta fô i sigi yorola.</p>
 <div className="sirago-splash-loader" aria-hidden="true"/>
 <p className="sirago-splash-status" role="status">{message}</p>
 <a className="sirago-splash-retry" href="">Recharger si nécessaire</a>
 </div><p className="sirago-splash-footer">Propulsé par BTDIGIT</p></main>
}
