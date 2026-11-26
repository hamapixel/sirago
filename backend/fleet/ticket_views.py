"""Local test tickets; not valid for boarding."""
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
import qrcode
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from xml.sax.saxutils import escape
from reportlab.lib.colors import HexColor
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
    return b.legs.select_related("departure__route","departure__company","departure__bus").order_by("position")

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
        "company":d.company.name,"company_city":d.company.city,"bus_name":d.bus.name,"origin":d.route.origin,"destination":d.route.destination,
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
    """A6 boarding card. A group ticket keeps its complete passenger annex."""
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A6)
    w, h = A6
    green = "#103B38"
    mint = "#16836C"
    muted = "#506866"
    p.setTitle("SiraGo - Billet TEST")

    def label(value, x, y, size=9, color=green, bold=False):
        p.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        p.setFillColor(HexColor(color))
        p.drawString(x, y, str(value))

    def box(value, x, top, width, height, size=10, color=green, bold=False):
        # Wrap long fields within their own allocated region instead of clipping.
        font = "Helvetica-Bold" if bold else "Helvetica"
        value = escape(" ".join(str(value).split()))
        while True:
            style = ParagraphStyle("ticket", fontName=font, fontSize=size,
                                   leading=size * 1.15, textColor=HexColor(color),
                                   splitLongWords=True)
            paragraph = Paragraph(value, style)
            _, used = paragraph.wrap(width, height)
            if used <= height or size <= 3:
                break
            size -= .25
        paragraph.drawOn(p, x, top - used)

    def line(y):
        p.setStrokeColor(HexColor("#DCE6E3"))
        p.line(16, y, w-16, y)

    p.setFillColor(HexColor(green))
    p.roundRect(9, h-92, w-18, 83, 10, fill=1, stroke=0)
    label("SiraGo", 19, h-28, 16, "#FFFFFF", True)
    label("BILLET TEST", w-82, h-26, 8, "#F6B844", True)
    label("COMPAGNIE DE TRANSPORT", 19, h-40, 6.8, "#C6E6DC", True)
    box(t["company"], 19, h-43, w-38, 26, 12, "#FFFFFF", True)
    box(" · ".join(filter(None, (t.get("company_city"), t.get("bus_name")))),
        19, h-71, w-38, 17, 8, "#F6D38D")

    tz = ZoneInfo("Africa/Bamako")
    start = datetime.fromisoformat(t["starts_at"]).astimezone(tz)
    end = datetime.fromisoformat(t["ends_at"]).astimezone(tz)
    left, right = 18, w/2+7
    col = w/2-26
    for x, title, dt, city, station in (
        (left, "Départ", start, t["origin"], t["boarding_point"]),
        (right, "Arrivée", end, t["destination"], t["arrival_point"]),
    ):
        label(title, x, h-107, 8, muted)
        label(dt.strftime("%H:%M"), x, h-127, 18, green, True)
        label(dt.strftime("%d/%m/%Y"), x, h-139, 8, muted)
        box(city, x, h-142, col, 21, 11, green, True)
        box(station, x, h-165, col, 30, 8.5, muted)
    line(h-198)
    inline_names = 1 < t["count"] <= 2 and len(" · ".join(t["names"])) <= 70
    label("Passager" if t["count"] == 1 else f'Billet collectif · {t["count"]} passagers', left, h-211, 8, muted)
    box(t["name"] if t["count"] == 1 else " · ".join(t["names"]) if inline_names else f'{t["count"]} passagers - liste en annexe',
        left, h-214, w-36, 25, 11, green, True)
    label("Catégorie", left, h-248, 8, muted)
    label("Montant", right, h-248, 8, muted)
    label(t["category"], left, h-262, 11, "#94640C" if t["category"] == "Premium" else green, True)
    label(f'{t["amount"]:,}'.replace(",", " ") + " FCFA", right, h-262, 11, green, True)
    line(h-271)
    matrix = t["qr"]
    side = 95
    unit = side / len(matrix)
    x, y = 13, h-370
    p.setFillColor(HexColor("#FFFFFF"))
    p.rect(x, y, side, side, fill=1, stroke=0)
    p.setFillColor(HexColor("#000000"))
    for row, values in enumerate(matrix):
        for col_index, v in enumerate(values):
            if v == "1":
                p.rect(x+col_index*unit, y+(len(matrix)-1-row)*unit, unit, unit, fill=1, stroke=0)
    box("QR code individuel" if t["count"] == 1 else "QR code collectif",
        117, h-284, w-133, 20, 10, green, True)
    label("Contrôle TEST", 117, h-310, 8, muted)
    box(t["code"], 117, h-316, w-133, 45, 8, muted)
    p.setFillColor(HexColor("#FFF0E0"))
    p.roundRect(16, 25, w-32, 20, 6, fill=1, stroke=0)
    label("TEST - Non valable pour voyager", 24, 32, 9, "#963B0D", True)
    label("Propulsé par BTDIGIT", 18, 12, 7.5, muted)
    p.showPage()
    if t["count"] > 1 and not inline_names:
        for offset in range(0, t["count"], 11):
            label("SiraGo - Passagers TEST", 17, h-25, 15, green, True)
            box(t["company"], 17, h-31, w-34, 25, 10, green, True)
            box(t["code"], 17, h-58, w-34, 20, 8, muted)
            label(t["category"]+" - "+str(t["count"])+" passagers", 17, h-89, 9)
            label(f'Prix unitaire : {t["unit_price"]} FCFA', 17, h-102, 9)
            for j, name in enumerate(t["names"][offset:offset+11], start=offset+1):
                box(f"{j}. {name}", 17, h-115-(j-offset-1)*24, w-34, 23, 10)
            label("TEST - Non valable pour voyager", 17, 24, 9, "#963B0D", True)
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
