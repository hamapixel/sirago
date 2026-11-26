from uuid import uuid5
from .models import TestTicketReference

def ticket_groups(b,l):
    if b.ticket_mode=="individual":
        return [[i] for i in range(b.passengers)]
    premium=set(l.premium_positions)
    return [g for g in ([i for i in range(b.passengers) if i not in premium],
                        [i for i in range(b.passengers) if i in premium]) if g]

def ticket_code(b,l,indices):
    suffix=str(indices[0]) if len(indices)==1 else "group:"+",".join(map(str,indices))
    return "SRG-TEST-"+uuid5(b.request_id,f"{b.pk}:{l.pk}:{suffix}").hex.upper()

def register_refs(b,legs):
    TestTicketReference.objects.bulk_create([
        TestTicketReference(code=ticket_code(b,l,g),leg=l,anchor=g[0])
        for l in legs for g in ticket_groups(b,l)
    ])
