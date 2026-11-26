"""Private server-side history search for PostgreSQL."""
import re
import unicodedata
from datetime import date
from django.db.models import (BigIntegerField, Case, CharField, Exists, F, Func,
    OuterRef, Prefetch, Q, Subquery, Sum, Value, When)
from django.db.models.functions import Cast, Coalesce, Lower
from .listing import page_slice, search_term
from .models import Booking, BookingLeg

ACCENTS="àâäáãåçéèêëíìîïñóòôöõúùûüýÿ"
PLAIN="aaaaaaceeeeiiiinooooouuuuyy"

def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if not unicodedata.combining(c))

def folded(field):
    return Func(Lower(Cast(field,CharField())),Value(ACCENTS),Value(PLAIN),function="TRANSLATE",output_field=CharField())

def history(request,now):
    qs=Booking.objects.filter(traveler=request.user).annotate(
        history_status=Case(
            When(sandbox_checkout__status="PAID",then=Value("SASPAY_PAID")),
            When(sandbox_checkout__status="REVIEW_PAID",then=Value("REVIEW")),
            When(sandbox_checkout__status="LATE_PAID",then=Value("LATE_PAID")),
            When(sandbox_checkout__status__in=["CREATING","UNKNOWN"],then=Value("REVIEW")),
            When(sandbox_checkout__status="PENDING",then=Value("SASPAY_PENDING")),
            When(sandbox_checkout__status="EXPIRED",then=Value("EXPIRED")),
            When(sandbox_checkout__status="CANCELLED",then=Value("CANCELLED")),
            When(status="HELD",expires_at__lte=now,then=Value("EXPIRED")),
            default=F("status"),output_field=CharField()),
    )
    status=request.GET.get("status","")
    if status not in ("","HELD","SASPAY_PENDING","SASPAY_PAID","TEST_PAID","EXPIRED","CANCELLED","REPORTED","LATE_PAID","REVIEW"):
        raise ValueError("Statut invalide.")
    if status:qs=qs.filter(history_status=status)
    term=normalized(search_term(request))
    if term:
        totals=BookingLeg.objects.filter(booking_id=OuterRef("pk")).order_by().values("booking_id").annotate(
            amount=Sum(F("unit_price")*(F("booking__passengers")-F("premium_count"))+F("premium_unit_price")*F("premium_count"),output_field=BigIntegerField())).values("amount")
        qs=qs.annotate(names_search=folded("passenger_names"),ref_search=folded("request_id"),
            created_search=Cast("created_at",CharField()), amount_search=Cast(Coalesce(Subquery(totals,output_field=BigIntegerField()),Value(0),output_field=BigIntegerField()),CharField()),
            state_search=Case(
                When(history_status="SASPAY_PAID",then=Value("saspay paye confirme test")),
                When(history_status="SASPAY_PENDING",then=Value("saspay pending en attente verification")),
                When(history_status="TEST_PAID",then=Value("paiement simule paye billet emis test")),
                When(history_status="HELD",then=Value("en attente paiement")),
                When(history_status="EXPIRED",then=Value("expire expiree")),
                When(history_status="CANCELLED",then=Value("annule annulee")),
                When(history_status="REPORTED",then=Value("reporte reportee")),
                When(history_status="LATE_PAID",then=Value("paiement tardif test")),
                default=Value("verification incertaine"),output_field=CharField()))
        # Handle a grouped FCFA amount or an explicit French date before tokenizing.
        if re.fullmatch(r"[0-9][0-9\s]*(?:\s*(?:fcfa|xof))?",term):
            term=re.sub(r"\s+|fcfa|xof","",term)
        def date_token(m):
            try:return date(int(m[3]),int(m[2]),int(m[1])).isoformat()
            except ValueError:return m[0]
        term=re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",date_token,term)
        for word in term.split():
            legs=BookingLeg.objects.filter(booking_id=OuterRef("pk")).annotate(
                origin_search=folded("departure__route__origin"),destination_search=folded("departure__route__destination"),
                company_search=folded("departure__company__name"),departure_search=Cast("departure__starts_at",CharField())
            ).filter(Q(origin_search__contains=word)|Q(destination_search__contains=word)|Q(company_search__contains=word)|Q(departure_search__contains=word))
            qs=qs.filter(Q(names_search__contains=word)|Q(ref_search__contains=word)|Q(created_search__contains=word)|Q(amount_search__contains=word)|Q(state_search__contains=word)|Q(Exists(legs)))
    qs=qs.select_related("sandbox_checkout","simulated_payment","outgoing_report").prefetch_related(
        Prefetch("legs",queryset=BookingLeg.objects.select_related("booking","departure__route","departure__company","departure__bus").order_by("position"),to_attr="history_legs")
    ).order_by("-id")
    return page_slice(request,qs,default_size=10)
