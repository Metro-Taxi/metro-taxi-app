"""
Legal documents serving routes — Métro-Taxi.

Sert les CGU/CGV et le Contrat de Partenariat Chauffeur depuis les fichiers
Markdown de référence, et expose des endpoints pour enregistrer l'acceptation
horodatée par les Utilisateurs.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from datetime import datetime, timezone
import os
import logging

from database import db
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["legal"])

LEGAL_DIR = "/app/memory/legal"

# Version des documents en vigueur (à incrémenter à chaque modification majeure)
CURRENT_VERSIONS = {
    "cgv": "2026-05-28",
    "contract-driver": "2026-07-20",
}

FILES = {
    "cgv": "CGU_CGV_Metro-Taxi_2026-05-28.md",
    "contract-driver": "Contrat_Partenariat_Chauffeur_2026-07-20.md",
}


@router.get("/legal/{doc_id}", response_class=PlainTextResponse)
async def get_legal_document(doc_id: str):
    """Public: retourne le contenu Markdown du document légal demandé.

    doc_id ∈ {"cgv", "contract-driver"}
    """
    if doc_id not in FILES:
        raise HTTPException(status_code=404, detail="Document inconnu")

    file_path = os.path.join(LEGAL_DIR, FILES[doc_id])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document indisponible")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"X-Document-Version": CURRENT_VERSIONS[doc_id]},
        )
    except Exception as e:
        logging.error(f"Failed to serve legal document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur de lecture du document")


@router.get("/legal/versions/current")
async def get_current_versions():
    """Public: retourne les versions courantes des documents légaux."""
    return {"versions": CURRENT_VERSIONS}


@router.post("/legal/{doc_id}/accept")
async def accept_legal_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Enregistre l'acceptation horodatée d'un document légal pour l'usager
    ou le chauffeur connecté.

    Sert de preuve juridique opposable : (user_id, document, version, timestamp).
    """
    if doc_id not in FILES:
        raise HTTPException(status_code=404, detail="Document inconnu")

    version = CURRENT_VERSIONS[doc_id]
    now_iso = datetime.now(timezone.utc).isoformat()
    role = current_user.get("role")
    user_id = current_user.get("user_id")

    field_prefix = "cgv" if doc_id == "cgv" else "contract"
    update = {
        f"{field_prefix}_accepted_version": version,
        f"{field_prefix}_accepted_at": now_iso,
    }

    if role == "user":
        await db.users.update_one({"id": user_id}, {"$set": update})
    elif role == "driver":
        await db.drivers.update_one({"id": user_id}, {"$set": update})
    else:
        raise HTTPException(status_code=403, detail="Acceptation réservée aux usagers/chauffeurs")

    return {"status": "ok", "doc_id": doc_id, "version": version, "accepted_at": now_iso}
