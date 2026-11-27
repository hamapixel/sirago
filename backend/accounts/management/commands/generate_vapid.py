from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import base64

class Command(BaseCommand):
    help="Generate VAPID keys. Save privately; never paste in chat or Git."
    def handle(self,*args,**options):
        key=ec.generate_private_key(ec.SECP256R1())
        enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip("=")
        self.stdout.write("SIRAGO_VAPID_PRIVATE_KEY="+enc(key.private_numbers().private_value.to_bytes(32,"big")))
        self.stdout.write("SIRAGO_VAPID_PUBLIC_KEY="+enc(key.public_key().public_bytes(Encoding.X962,PublicFormat.UncompressedPoint)))
