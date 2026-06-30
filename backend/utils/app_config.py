"""
App-wide runtime config (broadcast mode, feature flags, etc.).

Stocké en MongoDB collection `app_config`, lu avec cache 30s pour éviter
de requêter à chaque appel API.
"""
from __future__ import annotations

import time
from typing import Any


_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 30


async def get_config_value(db, key: str, default: Any = None) -> Any:
    """Récupère une valeur de config avec cache 30s."""
    now = time.time()
    cached = _CACHE.get(key)
    if cached and (now - cached[0] < _CACHE_TTL_SECONDS):
        return cached[1]
    doc = await db.app_config.find_one({"key": key}, {"_id": 0, "value": 1})
    value = doc["value"] if doc and "value" in doc else default
    _CACHE[key] = (now, value)
    return value


async def set_config_value(db, key: str, value: Any, updated_by: str | None = None) -> None:
    """Set/upsert une valeur de config + invalide le cache."""
    from datetime import datetime, timezone
    await db.app_config.update_one(
        {"key": key},
        {
            "$set": {
                "value": value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": updated_by,
            }
        },
        upsert=True,
    )
    _CACHE.pop(key, None)


async def is_broadcast_mode(db) -> bool:
    """Mode pré-lancement : tous les chauffeurs validés apparaissent dispo,
    chaque demande sonne sur tous les téléphones (le premier qui accepte gagne)."""
    return bool(await get_config_value(db, "broadcast_mode", False))
