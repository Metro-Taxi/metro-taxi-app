"""
Tests de régression sur la signature Sogecommerce.

Oracle officiel : exemple de la documentation systempay/Lyra
https://paiement.systempay.fr/doc/en-EN/form-payment/quick-start-guide/computing-the-signature.html
"""
import os
import pytest

from services.sogecommerce import (
    compute_vads_signature,
    verify_vads_signature,
    get_active_key,
    get_ctx_mode,
    get_shop_id,
)


# Exemple officiel de la doc Sogecommerce / Systempay
DOC_FIELDS = {
    "vads_action_mode": "INTERACTIVE",
    "vads_amount": "5124",
    "vads_ctx_mode": "TEST",
    "vads_currency": "978",
    "vads_page_action": "PAYMENT",
    "vads_payment_config": "SINGLE",
    "vads_site_id": "12345678",
    "vads_trans_date": "20170129130025",
    "vads_trans_id": "123456",
    "vads_version": "V2",
}
DOC_KEY = "1122334455667788"
DOC_EXPECTED_SIGNATURE = "ycA5Do5tNvsnKdc/eP1bj2xa19z9q3iWPy9/rpesfS0="


def test_signature_matches_official_doc_example():
    """Reproduit l'exemple officiel byte-for-byte."""
    sig = compute_vads_signature(DOC_FIELDS, DOC_KEY)
    assert sig == DOC_EXPECTED_SIGNATURE


def test_signature_ignores_non_vads_fields():
    extra = {**DOC_FIELDS, "signature": "ignored", "pay": "Pay", "custom": "x"}
    sig = compute_vads_signature(extra, DOC_KEY)
    assert sig == DOC_EXPECTED_SIGNATURE


def test_signature_order_independent_input():
    reversed_fields = dict(reversed(list(DOC_FIELDS.items())))
    sig = compute_vads_signature(reversed_fields, DOC_KEY)
    assert sig == DOC_EXPECTED_SIGNATURE


def test_verify_signature_ok():
    assert verify_vads_signature(DOC_FIELDS, DOC_EXPECTED_SIGNATURE, DOC_KEY) is True


def test_verify_signature_wrong_key():
    assert verify_vads_signature(DOC_FIELDS, DOC_EXPECTED_SIGNATURE, "wrong_key") is False


def test_verify_signature_tampered_amount():
    tampered = {**DOC_FIELDS, "vads_amount": "9999"}
    assert verify_vads_signature(tampered, DOC_EXPECTED_SIGNATURE, DOC_KEY) is False


def test_verify_signature_empty():
    assert verify_vads_signature(DOC_FIELDS, "", DOC_KEY) is False


def test_get_active_key_test_mode(monkeypatch):
    monkeypatch.setenv("SOGECOMMERCE_MODE", "TEST")
    monkeypatch.setenv("SOGECOMMERCE_TEST_KEY", "testkey123")
    monkeypatch.delenv("SOGECOMMERCE_PROD_KEY", raising=False)
    assert get_active_key() == "testkey123"
    assert get_ctx_mode() == "TEST"


def test_get_active_key_prod_mode(monkeypatch):
    monkeypatch.setenv("SOGECOMMERCE_MODE", "PRODUCTION")
    monkeypatch.setenv("SOGECOMMERCE_PROD_KEY", "prodkey456")
    assert get_active_key() == "prodkey456"
    assert get_ctx_mode() == "PRODUCTION"


def test_get_active_key_missing_raises(monkeypatch):
    monkeypatch.setenv("SOGECOMMERCE_MODE", "TEST")
    monkeypatch.delenv("SOGECOMMERCE_TEST_KEY", raising=False)
    with pytest.raises(RuntimeError):
        get_active_key()


def test_get_shop_id(monkeypatch):
    monkeypatch.setenv("SOGECOMMERCE_SHOP_ID", "43696939")
    assert get_shop_id() == "43696939"


def test_signature_with_apple_pay_fields():
    """Régression : champs supplémentaires (cust, ext_info) ne cassent pas l'algo."""
    fields = {
        **DOC_FIELDS,
        "vads_cust_email": "test@metro-taxi.com",
        "vads_cust_id": "user-uuid-123",
        "vads_ext_info_plan_id": "1month",
        "vads_ext_info_region_id": "paris",
    }
    sig = compute_vads_signature(fields, DOC_KEY)
    # Différent du sample doc puisque plus de champs, mais doit être déterministe et vérifiable
    assert sig
    assert verify_vads_signature(fields, sig, DOC_KEY)
