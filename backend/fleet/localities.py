from .models import Locality

def valid_localities(origin, destination):
    return isinstance(origin,str) and isinstance(destination,str) and origin != destination and Locality.objects.filter(name__in=[origin,destination]).count()==2

def locality_names():
    return Locality.objects.order_by("name").values_list("name",flat=True)
