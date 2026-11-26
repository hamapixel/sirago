"""Read-only financial TEST report, by issuance / settlement date."""
from datetime import date, datetime, time, timedelta
from io import BytesIO
from html import escape
from zoneinfo import ZoneInfo
from django.db.models import BigIntegerField, ExpressionWrapper, F, Q, Sum, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from fleet.models import Booking, BookingLeg, SandboxCommission, SandboxSettlement
from fleet.listing import page_slice, search_term
from .models import Company
from .supervision import superuser_endpoint

TZ=ZoneInfo("Africa/Bamako")
LIMIT=2000
KEYS=("sandbox","local","commission","share","unallocated","settled")
LABELS=("SasPay TEST","Local TEST","Commission TEST","Part compagnie TEST","Non réparti TEST","Reversé TEST")
def inputs(request):
    today=timezone.now().astimezone(TZ).date()
    first=date.fromisoformat(request.GET.get("date_from",today.replace(day=1).isoformat()))
    last=date.fromisoformat(request.GET.get("date_to",today.isoformat()))
    if first>last or (last-first).days>365:raise ValueError("Période de 366 jours maximum.")
    return first,last,datetime.combine(first,time.min,TZ),datetime.combine(last+timedelta(days=1),time.min,TZ)

def datasets(request):
    first,last,start,end=inputs(request)
    companies=Company.objects.all()
    for word in search_term(request).split():
        companies=companies.filter(Q(name__icontains=word)|Q(city__icontains=word))
    amount=ExpressionWrapper(F("unit_price")*(F("booking__passengers")-F("premium_count"))+F("premium_unit_price")*F("premium_count"),output_field=BigIntegerField())
    legs=BookingLeg.objects.filter(booking__status=Booking.Status.TEST_PAID,departure__company__in=companies).annotate(report_amount=amount)
    sandbox=legs.filter(booking__sandbox_checkout__status="PAID",booking__sandbox_checkout__transaction_id__isnull=False,booking__sandbox_checkout__issued_at__gte=start,booking__sandbox_checkout__issued_at__lt=end)
    local=legs.filter(booking__simulated_payment__created_at__gte=start,booking__simulated_payment__created_at__lt=end,booking__sandbox_checkout__isnull=True)
    commissions=SandboxCommission.objects.filter(leg__in=sandbox.values("pk"),checkout__status="PAID",checkout__issued_at__isnull=False,checkout__transaction_id__isnull=False)
    settled=SandboxSettlement.objects.filter(company__in=companies,created_at__gte=start,created_at__lt=end)
    def total(qs,field,group):
        sub=qs.filter(**{group:OuterRef("pk")}).order_by().values(group).annotate(total_value=Sum(field)).values("total_value")
        return Coalesce(Subquery(sub,output_field=BigIntegerField()),Value(0),output_field=BigIntegerField())
    ranking=companies.annotate(
        sandbox=total(sandbox,"report_amount","departure__company_id"),
        local=total(local,"report_amount","departure__company_id"),
        commission=total(commissions,"commission","company_id"),
        share=total(commissions,"company_share","company_id"),
        settled=total(settled,"amount","company_id"),
    ).annotate(unallocated=F("sandbox")-F("commission")-F("share")).filter(Q(sandbox__gt=0)|Q(local__gt=0)|Q(settled__gt=0)).order_by("-sandbox","name","pk")
    return first,last,ranking,commissions.select_related("company","checkout","leg__booking","leg__departure__route").order_by("-checkout__issued_at","-pk"),settled.select_related("company").order_by("-created_at","-pk")

def summary_for(ranking):
    values=ranking.aggregate(**{"sum_"+key:Sum(key,default=0) for key in KEYS})
    return {**{key:values["sum_"+key] for key in KEYS},"real":0}
def ranking_row(c):
    return {"id":c.pk,"name":c.name,"city":c.city,**{k:getattr(c,k) for k in KEYS}}
def commission_row(c):
    route=c.leg.departure.route
    return {"id":c.pk,"name":c.company.name,"date":c.checkout.issued_at.isoformat(),"reference":str(c.leg.booking.request_id),"route":f"{route.origin} → {route.destination}","gross":c.gross,"rate_bps":c.rate_bps,"commission":c.commission,"share":c.company_share}
def settlement_row(s):
    return {"id":s.pk,"name":s.company.name,"date":s.created_at.isoformat(),"reference":str(s.reference),"amount":s.amount}
def mode(request):
    value=request.GET.get("view","companies")
    if value not in ("companies","commissions","settlements"):raise ValueError("Vue invalide.")
    return value

@superuser_endpoint
def report(request):
    first,last,ranking,commissions,settled=datasets(request)
    view=mode(request)
    qs,serialize={"companies":(ranking,ranking_row),"commissions":(commissions,commission_row),"settlements":(settled,settlement_row)}[view]
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[serialize(r) for r in rows],"summary":summary_for(ranking),"date_from":first.isoformat(),"date_to":last.isoformat(),"real_payments_enabled":False,"view":view,**meta})

def export_data(request):
    first,last,ranking,commissions,settled=datasets(request)
    if any(q.count()>LIMIT for q in (ranking,commissions,settled)):
        raise ValueError("Export limité à 2000 lignes par rubrique. Réduisez la période ou la recherche.")
    summary=summary_for(ranking)
    sections=[
        ("Synthèse",["Indicateur","FCFA"],[[label,summary[key]] for key,label in zip(KEYS,LABELS)]+[["Recettes réelles",0]]),
        ("Compagnies",["Compagnie","Ville",*LABELS],[[c.name,c.city,*[getattr(c,k) for k in KEYS]] for c in ranking]),
        ("Commissions",["Compagnie","Date","Référence","Trajet","Billets FCFA","Taux %","Commission FCFA","Part FCFA"],[[c.company.name,timezone.localtime(c.checkout.issued_at,TZ).strftime("%d/%m/%Y %H:%M"),str(c.leg.booking.request_id),str(c.leg.departure.route.origin)+" - "+str(c.leg.departure.route.destination),c.gross,None if c.rate_bps is None else c.rate_bps/100,c.commission,c.company_share] for c in commissions]),
        ("Reversements",["Compagnie","Date","Référence","FCFA"],[[s.company.name,timezone.localtime(s.created_at,TZ).strftime("%d/%m/%Y %H:%M"),str(s.reference),s.amount] for s in settled]),
    ]
    return first,last,sections

def attachment(buf,kind,content_type):
    r=HttpResponse(buf.getvalue(),content_type=content_type)
    r["Content-Disposition"]=f'attachment; filename="sirago-finances-test.{kind}"'
    r["X-Content-Type-Options"]="nosniff"
    return r

@superuser_endpoint
def excel(request):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    first,last,sections=export_data(request)
    book=Workbook();book.remove(book.active)
    for title,headers,rows in sections:
        ws=book.create_sheet(title)
        ws.append(["SiraGo - RAPPORT TEST"])
        ws.append([f"{first:%d/%m/%Y} - {last:%d/%m/%Y} | Aucun fonds réel | Hors frais SasPay"])
        ws.append(headers)
        ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(headers))
        ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=len(headers))
        for values in rows:
            ws.append(values)
            # Force all user-controlled text to literal strings, never formulas.
            for cell,value in zip(ws[ws.max_row],values):
                if isinstance(value,str):cell.data_type="s"
                elif isinstance(value,(int,float)):cell.number_format="#,##0.##"
        for cell in ws[3]:
            cell.fill=PatternFill("solid",fgColor="103B38");cell.font=Font(color="FFFFFF",bold=True)
            cell.alignment=Alignment(wrap_text=True,vertical="center")
        ws["A1"].font=Font(size=18,bold=True,color="103B38")
        ws["A2"].font=Font(color="956400")
        ws.row_dimensions[3].height=32
        ws.freeze_panes="A4";ws.auto_filter.ref=f"A3:{get_column_letter(len(headers))}{ws.max_row}"
        for i,header in enumerate(headers,1):
            ws.column_dimensions[get_column_letter(i)].width=40 if header in ("Compagnie","Référence","Trajet","Indicateur") else 22
    buf=BytesIO();book.save(buf)
    return attachment(buf,"xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@superuser_endpoint
def pdf(request):
    first,last,sections=export_data(request)
    buf=BytesIO();doc=SimpleDocTemplate(buf,pagesize=landscape(A4),rightMargin=30,leftMargin=30,topMargin=30,bottomMargin=30)
    styles=getSampleStyleSheet();styles["Title"].textColor=colors.HexColor("#103B38")
    body=styles["BodyText"];body.fontSize=8;body.leading=11;body.splitLongWords=True
    def paragraph(value):
        if value is None:value="—"
        if isinstance(value,int):value=f"{value:,}".replace(","," ")
        return Paragraph(escape(str(value), quote=False),body)
    story=[Paragraph("SiraGo | Rapport financier TEST",styles["Title"]),Paragraph(f"{first:%d/%m/%Y} - {last:%d/%m/%Y} · Aucun transfert réel · Hors frais SasPay",styles["Normal"]),Spacer(1,12)]
    for title,headers,rows in sections:
        story.append(Paragraph(title,styles["Heading2"]))
        data=[[paragraph(h) for h in headers]]+[[paragraph(v) for v in row] for row in rows]
        if not rows:data.append([paragraph("Aucun résultat")]+[""]*(len(headers)-1))
        table=Table(data,colWidths=[doc.width/len(headers)]*len(headers),repeatRows=1,hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E3F2ED")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F6F5")]),("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),7)]))
        story.extend([table,Spacer(1,14)])
    def footer(canvas,doc):
        canvas.setFont("Helvetica",9);canvas.drawString(30,15,"BTDIGIT · TEST · Non valable comme preuve de paiement");canvas.drawRightString(landscape(A4)[0]-30,15,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return attachment(buf,"pdf","application/pdf")
