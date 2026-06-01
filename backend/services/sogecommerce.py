"""
Sogecommerce (Société Générale / vads-payment) — Signature & Helpers
====================================================================

Algorithme officiel HMAC-SHA-256 :
1. Filtrer les champs dont le nom commence par `vads_`.
2. Trier alphabétiquement par nom de champ.
3. Concaténer les VALEURS avec le caractère "+".
4. Ajouter "+" puis la clé (TEST ou PROD selon vads_ctx_mode) à la fin.
5. HMAC-SHA-256(message=chaîne_obtenue, key=clé), encodé en Base64.

Doc officielle :
https://paiement.systempay.fr/doc/en-EN/form-payment/quick-start-guide/computing-the-signature.html
"""
import base64
import hashlib
import hmac
import os
from typing import Dict


def compute_vads_signature(fields: Dict[str, str], key: str) -> str:
    """Calcule la signature HMAC-SHA-256 d'un payload vads_*.

    Args:
        fields: dictionnaire des champs envoyés (toutes clés, mais seules celles
                commençant par `vads_` sont prises en compte pour la signature).
        key:    clé secrète TEST ou PRODUCTION selon `vads_ctx_mode`.

    Returns:
        Signature Base64 à placer dans le champ `signature` du formulaire ou
        à comparer à celle reçue dans l'IPN.
    """
    vads_items = [(k, v) for k, v in fields.items() if k.startswith("vads_")]
    vads_items.sort(key=lambda kv: kv[0])
    joined_values = "+".join(str(v) for _, v in vads_items)
    message = f"{joined_values}+{key}"
    digest = hmac.new(
        key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify_vads_signature(fields: Dict[str, str], received_signature: str, key: str) -> bool:
    """Vérifie qu'une signature reçue correspond à celle calculée localement.

    Utilise `hmac.compare_digest` pour résister aux attaques par timing.
    """
    if not received_signature:
        return False
    expected = compute_vads_signature(fields, key)
    return hmac.compare_digest(expected, received_signature)


def get_active_key() -> str:
    """Retourne la clé TEST ou PRODUCTION selon `SOGECOMMERCE_MODE`."""
    mode = (os.environ.get("SOGECOMMERCE_MODE") or "TEST").upper()
    if mode == "PRODUCTION":
        key = os.environ.get("SOGECOMMERCE_PROD_KEY")
        if not key:
            raise RuntimeError("SOGECOMMERCE_PROD_KEY manquante alors que SOGECOMMERCE_MODE=PRODUCTION")
        return key
    key = os.environ.get("SOGECOMMERCE_TEST_KEY")
    if not key:
        raise RuntimeError("SOGECOMMERCE_TEST_KEY manquante (mode TEST)")
    return key


def get_ctx_mode() -> str:
    """`TEST` ou `PRODUCTION` à envoyer dans vads_ctx_mode."""
    mode = (os.environ.get("SOGECOMMERCE_MODE") or "TEST").upper()
    return "PRODUCTION" if mode == "PRODUCTION" else "TEST"


def get_shop_id() -> str:
    shop_id = os.environ.get("SOGECOMMERCE_SHOP_ID")
    if not shop_id:
        raise RuntimeError("SOGECOMMERCE_SHOP_ID manquant")
    return shop_id


def get_payment_url() -> str:
    """Endpoint Sogecommerce — identique TEST/PROD (différencié par site_id + key)."""
    return os.environ.get(
        "SOGECOMMERCE_PAYMENT_URL",
        "https://sogecommerce.societegenerale.eu/vads-payment/",
    )
