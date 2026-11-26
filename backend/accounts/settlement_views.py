"""Simulated settlements only. No provider payout API is invoked."""
from io import BytesIO
from uuid import UUID
from django.db import transaction, IntegrityError
from django.db.models import BigIntegerField, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, Cast
from django.db.models import CharField
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from fleet.models import SandboxCommission, SandboxSettlement, Booking
from fleet.listing import page_slice, search_term
from fleet.saspay import sandbox_tickets_enabled
from .models import Company, User
from .supervision import superuser_endpoint
from .views import data, error

def eligible():
    return SandboxCommission.objects.filter(checkout__status="PAID",checkout__issued_at__isnull=False,checkout__transaction_id__isnull=False,leg__booking__status=Booking.Status.TEST_PAID,rate_bps__isnull=False)

def company_totals(qs):
    def total(source,field):
        sub=source.filter(company_id=OuterRef("pk")).order_by().values("company_id").annotate(s=Sum(field)).values("s")
        return Coalesce(Subquery(sub,output_field=BigIntegerField()),Value(0),output_field=BigIntegerField())
    return qs.annotate(gross_test=total(eligible(),"gross"),commission_test=total(eligible(),"commission"),share_test=total(eligible(),"company_share"),settled_test=total(SandboxSettlement.objects.all(),"amount")).annotate(remaining_test=F("share_test")-F("settled_test"))

def row(c):
    return {"id":c.pk,"name":c.name,"city":c.city,"status":c.status,"gross":c.gross_test,"commission":c.commission_test,"share":c.share_test,"settled":c.settled_test,"remaining":c.remaining_test}

def settlement_row(s):
    return {"id":s.pk,"company":s.company.name,"reference":str(s.reference),"amount":s.amount,"created_at":s.created_at.isoformat()}

@superuser_endpoint
def balances(request):
    qs=Company.objects.all()
    for word in search_term(request).split():qs=qs.filter(Q(name__icontains=word)|Q(city__icontains=word))
    qs=company_totals(qs).order_by("name","pk")
    summary=qs.aggregate(total_gross=Sum("gross_test",default=0),total_commission=Sum("commission_test",default=0),total_share=Sum("share_test",default=0),total_settled=Sum("settled_test",default=0),total_remaining=Sum("remaining_test",default=0))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[row(c) for c in rows],"summary":{k.removeprefix("total_"):v for k,v in summary.items()},"enabled":sandbox_tickets_enabled(),**meta})

def history_data(request,qs):
    for word in search_term(request).split():
        qs=qs.annotate(ref_text=Cast("reference",CharField())).filter(Q(company__name__icontains=word)|Q(ref_text__icontains=word))
    rows,meta=page_slice(request,qs.select_related("company").order_by("-id"))
    return {"items":[settlement_row(s) for s in rows],**meta}

@superuser_endpoint
def history(request):
    return JsonResponse(history_data(request,SandboxSettlement.objects.all()))

@never_cache
@csrf_protect
@require_POST
def create(request,pk):
    if not request.user.is_authenticated:return error("Connexion requise.",401)
    if not request.user.is_active or not request.user.is_superuser:return error("Accès réservé au superadministrateur.",403)
    if not sandbox_tickets_enabled():return error("Reversements TEST désactivés.",403)
    if not 1<=pk<=2**63-1:return error("Compagnie introuvable.",404)
    try:
        v=data(request,1024)
        if set(v)!={"amount","reference","expected_remaining"}:raise ValueError("Données invalides.")
        amount,expected=v["amount"],v["expected_remaining"]
        if type(amount) is not int or type(expected) is not int or not 0<amount<=expected<=2**53-1:raise ValueError("Montant invalide.")
        if not isinstance(v["reference"],str):raise ValueError("Référence invalide.")
        ref=UUID(v["reference"])
    except (ValueError,TypeError):return error("Montant ou référence invalide.")
    try:
        with transaction.atomic():
            actor=User.objects.select_for_update().filter(pk=request.user.pk,is_active=True,is_superuser=True).first()
            if actor is None:return error("Accès réservé au superadministrateur.",403)
            company=Company.objects.select_for_update().filter(pk=pk).first()
            if company is None:return error("Compagnie introuvable.",404)
            existing=SandboxSettlement.objects.filter(reference=ref).first()
            if existing:
                if existing.company_id==pk and existing.amount==amount and existing.actor_id==actor.pk:return JsonResponse(settlement_row(existing))
                return error("Référence déjà utilisée.",409)
            if company.status!=Company.Status.VERIFIED:return error("Compagnie non validée.",403)
            current=company_totals(Company.objects.filter(pk=pk)).get()
            if current.remaining_test!=expected or amount>current.remaining_test:return error("Montant disponible modifié. Actualisez.",409)
            s=SandboxSettlement.objects.create(company=company,actor=actor,reference=ref,amount=amount)
            return JsonResponse(settlement_row(s),status=201)
    except IntegrityError:return error("Conflit de référence. Actualisez.",409)

def owner_company(request):
    if not request.user.is_authenticated:return None,error("Connexion requise.",401)
    if not request.user.is_active or request.user.is_superuser:return None,error("Accès réservé au responsable.",403)
    c=Company.objects.filter(owner=request.user,status=Company.Status.VERIFIED).first()
    return (c,None) if c else (None,error("Accès réservé au responsable.",403))

@never_cache
@require_GET
def company_view(request):
    c,denied=owner_company(request)
    if denied is not None:return denied
    try:return JsonResponse({"balance":row(company_totals(Company.objects.filter(pk=c.pk)).get()),**history_data(request,SandboxSettlement.objects.filter(company=c))})
    except (ValueError,OverflowError) as exc:return error(str(exc))

@never_cache
@require_GET
def receipt(request,pk):
    if not request.user.is_authenticated:return error("Connexion requise.",401)
    if not request.user.is_active:return error("Accès refusé.",403)
    if not 1<=pk<=2**63-1:return error("Reçu introuvable.",404)
    qs=SandboxSettlement.objects.select_related("company")
    if not request.user.is_superuser:
        c,denied=owner_company(request)
        if denied is not None:return denied
        qs=qs.filter(company=c)
    s=qs.filter(pk=pk).first()
    if s is None:return error("Reçu introuvable.",404)
    buf=BytesIO();p=canvas.Canvas(buf,pagesize=A4);w,h=A4
    p.setTitle("SiraGo - Justificatif TEST")
    p.setFillColor(HexColor("#103B38"));p.roundRect(30,h-126,w-60,96,12,fill=1,stroke=0)
    p.setFillColor(HexColor("#FFFFFF"));p.setFont("Helvetica-Bold",22);p.drawString(45,h-65,"SiraGo")
    p.setFont("Helvetica",13);p.drawString(45,h-95,"Justificatif de reversement TEST")
    p.setFillColor(HexColor("#94640C"));p.setFont("Helvetica-Bold",11);p.drawString(45,h-155,"SIMULATION - Aucun transfert réel")
    for y,label,value in [(h-205,"Compagnie",s.company.name),(h-265,"Référence",str(s.reference)),(h-325,"Date",timezone.localtime(s.created_at).strftime("%d/%m/%Y %H:%M")),(h-385,"Montant TEST",f"{s.amount:,}".replace(","," ")+" FCFA")]:
        p.setFillColor(HexColor("#506866"));p.setFont("Helvetica",11);p.drawString(45,y,label)
        p.setFillColor(HexColor("#103B38"));size=15
        while size>8 and stringWidth(value,"Helvetica-Bold",size)>w-90:size-=1
        while value and stringWidth(value,"Helvetica-Bold",size)>w-90:value=value[:-1]
        p.setFont("Helvetica-Bold",size);p.drawString(45,y-23,value)
    p.setFont("Helvetica",10);p.drawString(45,65,"Hors frais SasPay - Non valable comme preuve de paiement.")
    p.drawString(45,45,"Propulsé par BTDIGIT")
    p.save();r=HttpResponse(buf.getvalue(),content_type="application/pdf");r["Content-Disposition"]=f'attachment; filename="sirago-reversement-test-{s.pk}.pdf"';r["X-Content-Type-Options"]="nosniff";return r
