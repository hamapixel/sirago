"""Local test tickets; not valid for boarding."""
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
import qrcode
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from .booking_views import simulation_enabled, traveler_error
from .models import Booking
from .ticket_refs import ticket_groups, ticket_code
from accounts.views import error

def ticket_booking(request,pk):
    if not simulation_enabled():
        return None,error("Billets de test indisponibles.",404)
    denied=traveler_error(request)
    if denied is not None:
        return None,denied
    if not 1<=pk<=2**63-1:
        return None,error("Réservation introuvable.",404)
    b=Booking.objects.filter(pk=pk,traveler=request.user).first()
    if b is None:
        return None,error("Réservation introuvable.",404)
    if b.status!=Booking.Status.TEST_PAID or not (hasattr(b,"simulated_payment") or (hasattr(b,"sandbox_checkout") and b.sandbox_checkout.issued_at and b.sandbox_checkout.status=="PAID" and b.sandbox_checkout.transaction_id)):
        return None,error("Aucun billet de test disponible.",409)
    return b,None

def legs_for(b):
    return b.legs.select_related("departure__route","departure__company").order_by("position")

def ticket_data(b,l,indices):
    i=indices[0]
    code=ticket_code(b,l,indices)
    premium=i in l.premium_positions
    names=[b.passenger_names[j] if j<len(b.passenger_names) else f"Passager {j+1}" for j in indices]
    unit=l.premium_unit_price if premium else l.unit_price
    d=l.departure
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,border=4,box_size=1)
    qr.add_data(code)
    qr.make(fit=True)
    return {"code":code,"leg":l.position,"passenger":i,
        "name":names[0],"names":names,"count":len(indices),"unit_price":unit,
        "category":"Premium" if premium else "Standard",
        "amount":unit*len(indices),
        "company":d.company.name,"origin":d.route.origin,"destination":d.route.destination,
        "starts_at":d.starts_at.isoformat(),"ends_at":d.ends_at.isoformat(),
        "boarding_point":d.route.boarding_point,"arrival_point":d.route.arrival_point,
        "qr":["".join("1" if v else "0" for v in row) for row in qr.get_matrix()]}

@never_cache
@require_GET
def tickets(request,pk):
    b,denied=ticket_booking(request,pk)
    if denied is not None:return denied
    return JsonResponse({"items":[ticket_data(b,l,g) for l in legs_for(b) for g in ticket_groups(b,l)]})

def make_pdf(t):
    buf=BytesIO()
    p=canvas.Canvas(buf,pagesize=A5)
    w,h=A5
    green="#103B38"
    p.setTitle("SiraGo - Billet TEST")
    def label(value,x,y,size=11,color=green,bold=False,max_width=None):
        font="Helvetica-Bold" if bold else "Helvetica"
        value=str(value)
        width=max_width or w-x-26
        while size>5 and stringWidth(value,font,size)>width:size-=.5
        p.setFillColor(HexColor(color))
        p.setFont(font,size)
        p.drawString(x,y,value)
    def line(y):
        p.setStrokeColor(HexColor("#DCE6E3"))
        p.line(30,y,w-30,y)
    p.setFillColor(HexColor(green))
    p.roundRect(16,h-155,w-32,137,15,fill=1,stroke=0)
    label("SiraGo",32,h-49,25,"#FFFFFF",True)
    label("Ka billet ta fô i sigi yorola.",32,h-72,11,"#F6B844")
    label(t["origin"]+" - "+t["destination"],32,h-106,17,"#FFFFFF",True)
    label(t["company"],32,h-129,12,"#FFFFFF")
    tz=ZoneInfo("Africa/Bamako")
    start=datetime.fromisoformat(t["starts_at"]).astimezone(tz)
    end=datetime.fromisoformat(t["ends_at"]).astimezone(tz)
    label("Départ",32,h-180,10)
    label("Arrivée",w/2+8,h-180,10)
    label(start.strftime("%H:%M"),32,h-205,23,green,True)
    label(end.strftime("%H:%M"),w/2+8,h-205,23,green,True)
    label(t["origin"],32,h-224,12,green,True,w/2-45)
    label(t["destination"],w/2+8,h-224,12,green,True,w/2-42)
    label(t["boarding_point"],32,h-237,8,green,False,w/2-45)
    label(t["arrival_point"],w/2+8,h-237,8,green,False,w/2-42)
    line(h-247)
    label("Passager" if t["count"]==1 else "Billet collectif",32,h-263,10)
    label(t["name"] if t["count"]==1 else f'{t["count"]} passagers - liste en annexe',32,h-279,12,green,True)
    label("Catégorie",32,h-298,10)
    label("Montant",w/2+8,h-298,10)
    label(t["category"],32,h-315,12,"#94640C" if t["category"]=="Premium" else green,True)
    label(f'{t["amount"]:,}'.replace(","," ")+" FCFA",w/2+8,h-315,12,green,True)
    label("Date : "+start.strftime("%d/%m/%Y"),32,h-333,11)
    line(h-343)
    matrix=t["qr"];side=112;unit=side/len(matrix);x=(w-side)/2;y=h-466
    p.setFillColor(HexColor("#FFFFFF"))
    p.rect(x,y,side,side,fill=1,stroke=0)
    p.setFillColor(HexColor("#000000"))
    for row,values in enumerate(matrix):
        for col,v in enumerate(values):
            if v=="1":p.rect(x+col*unit,y+(len(matrix)-1-row)*unit,unit,unit,fill=1,stroke=0)
    label("QR code individuel" if t["count"]==1 else "QR code collectif",w/2-52,h-480,11,green,True)
    label(t["code"],32,h-496,8)
    p.setFillColor(HexColor("#FFF0E0"))
    p.roundRect(30,h-527,w-60,23,6,fill=1,stroke=0)
    label("TEST - Non valable pour voyager",39,h-519,11,"#963B0D",True)
    label("Propulsé par BTDIGIT",32,33,10,"#506866")
    p.showPage()
    if t["count"]>1:
        for offset in range(0,t["count"],24):
            label("SiraGo - Liste des passagers TEST",30,h-40,16,green,True)
            label(t["code"],30,h-60,9)
            label(t["category"]+" - "+str(t["count"])+" passagers",30,h-80,11)
            label(f'Prix unitaire : {t["unit_price"]} FCFA',30,h-98,10)
            for j,name in enumerate(t["names"][offset:offset+24],start=offset+1):
                label(f"{j}. {name}",30,h-123-(j-offset-1)*18,10)
            label("TEST - Non valable pour voyager",30,30,10,"#963B0D",True)
            p.showPage()
    p.save()
    return buf.getvalue()

@never_cache
@require_GET
def ticket_pdf(request,pk,leg,passenger):
    b,denied=ticket_booking(request,pk)
    if denied is not None:return denied
    l=legs_for(b).filter(position=leg).first() if leg in (0,1) else None
    if l is None or not 0<=passenger<b.passengers:
        return error("Billet introuvable.",404)
    group=next((g for g in ticket_groups(b,l) if g[0]==passenger),None)
    if group is None:return error("Billet introuvable.",404)
    t=ticket_data(b,l,group)
    response=HttpResponse(make_pdf(t),content_type="application/pdf")
    response["Content-Disposition"]='attachment; filename="'+t["code"]+'.pdf"'
    response["X-Content-Type-Options"]="nosniff"
    return response
