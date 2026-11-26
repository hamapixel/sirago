"""Freeze test allocations at checkout creation under the existing company locks."""
from accounts.models import CompanyCommission
from .models import SandboxCommission

def fee_per_ticket(price,rate_bps):
    return (price*rate_bps+5000)//10000

def freeze_commissions(checkout,legs):
    rates=dict(CompanyCommission.objects.filter(company_id__in={l.departure.company_id for l in legs}).values_list("company_id","rate_bps"))
    rows=[]
    for leg in legs:
        company_id=leg.departure.company_id
        rate=rates.get(company_id)
        gross=leg.total
        fee=None if rate is None else (leg.booking.passengers-leg.premium_count)*fee_per_ticket(leg.unit_price,rate)+leg.premium_count*fee_per_ticket(leg.premium_unit_price,rate)
        rows.append(SandboxCommission(checkout=checkout,leg=leg,company_id=company_id,gross=gross,rate_bps=rate,commission=fee,company_share=None if fee is None else gross-fee))
    SandboxCommission.objects.bulk_create(rows)
