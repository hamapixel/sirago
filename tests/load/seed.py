"""Load-test fixture: execute only in the isolated sirago-load Compose stack."""
from datetime import datetime, time, timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from accounts.models import Company, User
from fleet.models import Bus, Departure, Locality, Route

if (settings.DATABASES["default"]["NAME"] != "sirago_load"
        or "load.example.test" not in settings.ALLOWED_HOSTS
        or settings.DEBUG or not settings.SIRAGO_ADMIN_MFA_REQUIRED):
    raise RuntimeError("Refusing to seed outside the isolated production-profile load database.")

day = timezone.localdate() + timedelta(days=1)
with transaction.atomic():
    if Company.objects.exists() or User.objects.exists() or Departure.objects.exists():
        raise RuntimeError("Load database must be empty; refusing to alter existing data.")
    Locality.objects.get_or_create(name="Bamako", defaults={"kind": "DISTRICT"})
    Locality.objects.get_or_create(name="Sikasso", defaults={"kind": "REGION"})
    for i in range(10):
        owner = User.objects.create_user(username=f"load-owner-{i}", role=User.Role.COMPANY)
        company = Company.objects.create(owner=owner, name=f"Load Test {i+1}",
            city="Bamako", address="Gare fictive", status=Company.Status.VERIFIED)
        route = Route.objects.create(company=company, origin="Bamako", destination="Sikasso",
            boarding_point="Gare A", arrival_point="Gare B", duration_minutes=420, price=8000+i*100)
        for j in range(10):
            bus = Bus.objects.create(company=company, name=f"Car test {j+1}",
                plate=f"LOAD-{i}-{j}", capacity=50)
            for offset in (0, 1):
                start = timezone.make_aware(datetime.combine(day+timedelta(days=offset),time(6+j%5)),
                                             timezone.get_default_timezone())
                Departure.objects.create(company=company, bus=bus, route=route, starts_at=start,
                    ends_at=start+timedelta(hours=7), price=route.price, capacity=bus.capacity,
                    status=Departure.Status.PUBLISHED)
print(f"LOAD_DATE={day.isoformat()}")
print("Created 10 companies, 100 buses, 200 departures (100 per day); no payments or real accounts.")
