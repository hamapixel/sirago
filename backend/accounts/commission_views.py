"""Explicit commission configuration only; no money movement."""
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from fleet.listing import page_slice, search_term
from .models import Company, CompanyCommission, CommissionChange, User
from .supervision import superuser_endpoint
from .views import data, error

def company_row(company):
    policy = getattr(company, "commission_policy", None)
    return {"id":company.pk,"name":company.name,"city":company.city,
            "rate_bps":policy.rate_bps if policy else None}

@superuser_endpoint
def policies(request):
    qs=Company.objects.select_related("commission_policy").order_by("name","pk")
    for word in search_term(request).split():
        qs=qs.filter(Q(name__icontains=word)|Q(city__icontains=word))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[company_row(c) for c in rows],**meta})

@never_cache
@csrf_protect
@require_POST
def update(request,pk):
    if not request.user.is_authenticated:return error("Connexion requise.",401)
    if not request.user.is_active or not request.user.is_superuser:return error("Accès réservé au superadministrateur.",403)
    if not 1<=pk<=2**63-1:return error("Compagnie introuvable.",404)
    try:
        values=data(request,1024)
        if set(values)!={"rate_bps","expected_bps"}:raise ValueError("Données invalides.")
        rate,expected=values["rate_bps"],values["expected_bps"]
        if type(rate) is not int or not 0<=rate<=1000 or (expected is not None and (type(expected) is not int or not 0<=expected<=1000)):
            raise ValueError("Taux autorisé : 0 à 10 %.")
    except ValueError as exc:return error(str(exc))
    with transaction.atomic():
        actor=User.objects.select_for_update().filter(pk=request.user.pk,is_active=True,is_superuser=True).first()
        if actor is None:return error("Accès réservé au superadministrateur.",403)
        company=Company.objects.select_for_update().filter(pk=pk).first()
        if company is None:return error("Compagnie introuvable.",404)
        policy=CompanyCommission.objects.filter(company=company).first()
        previous=policy.rate_bps if policy else None
        if previous!=expected:return error("Taux modifié. Actualisez avant de réessayer.",409)
        if previous!=rate:
            CompanyCommission.objects.update_or_create(company=company,defaults={"rate_bps":rate})
            CommissionChange.objects.create(company=company,actor=actor,previous_bps=previous,new_bps=rate)
    return JsonResponse({"id":pk,"rate_bps":rate})

@superuser_endpoint
def changes(request):
    qs=CommissionChange.objects.select_related("company","actor").order_by("-id")
    for word in search_term(request).split():
        qs=qs.filter(Q(company__name__icontains=word)|Q(actor__username__icontains=word))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":c.pk,"company":c.company.name,"actor":c.actor.get_full_name() or c.actor.username,"previous_bps":c.previous_bps,"new_bps":c.new_bps,"created_at":c.created_at.isoformat()} for c in rows],**meta})
