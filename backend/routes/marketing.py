"""
Endpoint pour télécharger les assets marketing avec Content-Disposition: attachment
Évite que la PWA intercepte les liens et force le navigateur à télécharger le fichier
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

ASSETS_BASE = Path("/app/frontend/public/marketing")

ALLOWED_FILES = {
    # Vidéos finales campagne chauffeurs
    "video_1_chiffre_qui_fait_mal_FINAL.mp4": "video/mp4",
    "video_2_calcul_simple_FINAL.mp4": "video/mp4",
    "video_3_liberte_retrouvee_FINAL.mp4": "video/mp4",
    # Voix off
    "voix_1_chiffre_qui_fait_mal.mp3": "audio/mpeg",
    "voix_2_calcul_simple.mp3": "audio/mpeg",
    "voix_3_liberte_retrouvee.mp3": "audio/mpeg",
    # Flyers
    "flyers/flyer_chauffeur_A5.pdf": "application/pdf",
    "flyers/flyer_chauffeur_RECTO.png": "image/png",
    "flyers/flyer_chauffeur_VERSO.png": "image/png",
}


@router.get("/download/{filename:path}")
async def download_marketing_asset(filename: str):
    """
    Force le téléchargement d'un asset marketing.
    L'endpoint /api/* n'est pas dans le scope PWA donc le browser
    ouvre normalement le lien et déclenche le download.
    """
    if filename not in ALLOWED_FILES:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = ASSETS_BASE / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File missing on server")

    media_type = ALLOWED_FILES[filename]
    download_name = file_path.name  # Force le bon nom au téléchargement

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=download_name,
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Cache-Control": "public, max-age=3600",
        },
    )
