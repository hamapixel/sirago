"""Normalize small company images; never store original uploaded bytes."""
import base64
import binascii
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .models import Company
from .views import company_profile_error, data, error, limited, profile

MAX_INPUT = 800 * 1024

def normalize_image(value, kind):
    if value == "":
        return ""
    if not isinstance(value, str) or len(value) > 4 * MAX_INPUT // 3 + 128:
        raise ValueError("Image trop volumineuse.")
    prefix, sep, encoded = value.partition(",")
    if not sep or prefix not in ("data:image/png;base64", "data:image/jpeg;base64", "data:image/webp;base64"):
        raise ValueError("Choisissez une image PNG, JPEG ou WebP.")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_INPUT:
            raise ValueError("Image trop volumineuse.")
        with Image.open(BytesIO(raw)) as img:
            if img.format not in ("PNG", "JPEG", "WEBP") or max(img.size) > 4096 or img.width * img.height > 12_000_000 or getattr(img, "is_animated", False):
                raise ValueError("Image non prise en charge.")
            img = ImageOps.exif_transpose(img).convert("RGBA")
            img.thumbnail((256, 256) if kind == "logo" else (1200, 420), Image.Resampling.LANCZOS)
            clean = Image.new("RGB", img.size, "white")
            clean.paste(img, mask=img.getchannel("A"))
            out = BytesIO()
            clean.save(out, format="JPEG", quality=82, optimize=True)
            if out.tell() > 250_000:
                raise ValueError("Image trop détaillée.")
    except (binascii.Error, OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("Image invalide.") from exc
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")


@never_cache
@csrf_protect
@require_POST
def update(request):
    denied = company_profile_error(request)
    if denied is not None:
        return denied
    company = Company.objects.get(owner=request.user)
    if company.status not in (Company.Status.PENDING, Company.Status.VERIFIED):
        return error("Modifications bloquées.", 403)
    if limited(request, "company-branding", 12):
        return error("Trop de tentatives. Réessayez plus tard.", 429)
    try:
        values = data(request, max_bytes=1_200_000)
        kind = values.get("kind")
        if kind not in ("logo", "banner"):
            raise ValueError("Type d’image invalide.")
        value = normalize_image(values.get("image"), kind)
    except ValueError as exc:
        return error(str(exc))
    setattr(company, kind, value)
    company.save(update_fields=[kind])
    return JsonResponse(profile(request.user))
