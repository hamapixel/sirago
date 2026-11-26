def search_term(request):
    value=request.GET.get("q","").strip()
    if len(value)>150:raise ValueError("Recherche trop longue (150 caractères maximum).")
    return value

def page_slice(request,qs,default_size=10):
    try:
        page=int(request.GET.get("page","1"))
        size=int(request.GET.get("page_size",str(default_size)))
    except ValueError:
        raise ValueError("Pagination invalide.")
    if not 1<=page<=100000 or size not in (10,20,50,100):
        raise ValueError("Pagination invalide.")
    total=qs.count()
    start=(page-1)*size
    return list(qs[start:start+size]),{"page":page,"page_size":size,"total":total,"has_next":start+size<total}
