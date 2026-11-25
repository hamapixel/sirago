from io import BytesIO
from django.http import JsonResponse,HttpResponse
from django.utils import timezone
from accounts.models import Company
from accounts.views import error
from .models import Booking,Departure,TestBoarding
from .availability import active_legs
from .views import company_endpoint,TZ
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import datetime

def manifest_data(company,pk):
    if not 1<=pk<=2**63-1:return None
    d=Departure.objects.select_related("route","bus").filter(pk=pk,company=company).first()
    if not d:return None
    now=timezone.now()
    legs=list(active_legs(now).filter(departure=d).select_related("booking").order_by("id"))
    boarded={(r.leg_id,r.passenger):r.boarded_at.isoformat() for r in TestBoarding.objects.filter(leg_id__in=[l.pk for l in legs])}
    rows=[];pending=simulated=standard=premium=sim_total=pending_total=0
    finished=now>=d.ends_at and d.status==Departure.Status.PUBLISHED
    for l in legs:
        b=l.booking
        paid=b.status==Booking.Status.TEST_PAID
        if paid:simulated+=b.passengers;sim_total+=l.total
        else:pending+=b.passengers;pending_total+=l.total
        premium+=l.premium_count;standard+=b.passengers-l.premium_count
        for i in range(b.passengers):
            is_premium=i in l.premium_positions
            at=boarded.get((l.pk,i)) if paid else None
            state="BOARDED" if at else "PENDING" if not paid else "ABSENT" if finished else "WAITING"
            rows.append({"id":f"{l.pk}-{i}","name":b.passenger_names[i] if i<len(b.passenger_names) else f"Passager {i+1}","category":"Premium" if is_premium else "Standard","amount":l.premium_unit_price if is_premium else l.unit_price,"state":state,"boarded_at":at})
    return {"departure_id":d.pk,"company":company.name,"origin":d.route.origin,"destination":d.route.destination,"boarding_point":d.route.boarding_point,"bus":d.bus.name,"plate":d.bus.plate,"starts_at":d.starts_at.isoformat(),"ends_at":d.ends_at.isoformat(),"generated_at":now.isoformat(),"status":d.status,"capacity":d.capacity,"reserved":len(rows),"standard":standard,"premium":premium,"pending":pending,"simulated":simulated,"boarded":sum(r["state"]=="BOARDED" for r in rows),"absent":sum(r["state"]=="ABSENT" for r in rows),"waiting":sum(r["state"]=="WAITING" for r in rows),"remaining":max(0,d.capacity-len(rows)),"simulated_amount":sim_total,"pending_amount":pending_total,"real_amount":0,"items":rows}

def access(request,company,pk):
    if request.method!="GET":return None,error("Méthode non autorisée.",405)
    if company.status!=Company.Status.VERIFIED:return None,error("Compagnie non validée.",403)
    result=manifest_data(company,pk)
    if result is not None and getattr(request,"company_agent",None):
        for key in ("simulated_amount","pending_amount","real_amount"):result.pop(key,None)
        for item in result["items"]:item.pop("amount",None)
    return (result,None) if result is not None else (None,error("Départ introuvable.",404))

@company_endpoint
def manifest(request,company,pk):
    result,denied=access(request,company,pk)
    return denied if denied is not None else JsonResponse(result)

LABELS={"BOARDED":"Embarqué TEST","PENDING":"Paiement en attente","ABSENT":"Absent TEST","WAITING":"Non embarqué TEST"}
def make_pdf(m):
    buf=BytesIO();p=canvas.Canvas(buf,pagesize=landscape(A4))
    w,h=landscape(A4)
    def text(value,x,y,size=10,bold=False,width=None,color="#103B38"):
        font="Helvetica-Bold" if bold else "Helvetica"
        value=str(value)
        if width:
            while size>6 and stringWidth(value,font,size)>width:size-=.5
            if stringWidth(value,font,size)>width:
                while value and stringWidth(value+"...",font,size)>width:value=value[:-1]
                value+="..."
        p.setFont(font,size);p.setFillColor(HexColor(color));p.drawString(x,y,value)
    def fmt(v):return datetime.fromisoformat(v).astimezone(TZ).strftime("%d/%m/%Y %H:%M")
    def money(v):return f"{v:,}".replace(","," ")+" FCFA"
    rows=m["items"];pages=max(1,(len(rows)+17)//18)
    for page in range(pages):
        p.setFillColor(HexColor("#103B38"));p.rect(24,h-85,w-48,60,fill=1,stroke=0)
        text("SiraGo Pro - Manifeste voyageurs",36,h-49,18,True,color="#FFFFFF")
        text(m["company"]+" | "+m["origin"]+" - "+m["destination"],36,h-70,12,width=w-75,color="#FFFFFF")
        text(fmt(m["starts_at"])+" | "+m["bus"]+" | "+m["plate"]+" | "+m["boarding_point"],30,h-105,11,width=w-60)
        text(f'Capacité : {m["capacity"]}  |  Réservés : {m["reserved"]}  |  Standard : {m["standard"]}  |  Premium : {m["premium"]}  |  Libres : {m["remaining"]}',30,h-125,11,True)
        text(f'En attente : {m["pending"]}  |  Embarqués TEST : {m["boarded"]}  |  Non embarqués : {m["waiting"]}  |  Absents TEST : {m["absent"]}',30,h-144,10)
        if "real_amount" in m:
            text("Simulé : "+money(m["simulated_amount"])+"   |   En attente : "+money(m["pending_amount"])+"   |   Recettes réelles : 0 FCFA",30,h-163,10,True)
        else:text("Document opérationnel - Montants masqués",30,h-163,10,True)
        text("MODE TEST - Aucun encaissement ni embarquement réel",30,h-181,10,True,color="#94640C")
        cols=[30,64,365,450,560,705]
        for x,label in zip(cols,["N°","Passager","Catégorie","Montant" if "real_amount" in m else "", "Statut","Heure TEST"]):text(label,x,h-206,10,True)
        for j,r in enumerate(rows[page*18:(page+1)*18]):
            y=h-226-j*17
            p.setStrokeColor(HexColor("#DCE6E3"));p.line(30,y-5,w-30,y-5)
            for x,value,width in zip(cols,[page*18+j+1,r["name"],r["category"],money(r["amount"]) if "amount" in r else "",LABELS[r["state"]],fmt(r["boarded_at"]) if r["boarded_at"] else "-"],[30,295,80,105,140,105]):text(value,x,y,9,width=width)
        if not rows:text("Aucun voyageur réservé.",30,h-235)
        text("Propulsé par BTDIGIT | Généré le "+fmt(m["generated_at"]),30,30,9)
        text(f"{page+1}/{pages}",w-65,30,9)
        p.showPage()
    p.save();return buf.getvalue()

@company_endpoint
def manifest_pdf(request,company,pk):
    result,denied=access(request,company,pk)
    if denied is not None:return denied
    r=HttpResponse(make_pdf(result),content_type="application/pdf")
    r["Content-Disposition"]=f'attachment; filename="sirago-manifeste-{pk}.pdf"'
    r["X-Content-Type-Options"]="nosniff"
    return r
