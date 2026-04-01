"""
Routes API pour Métro-Taxi
Modules organisés par domaine fonctionnel
"""
from .regions import router as regions_router
from .drivers import router as drivers_router
from .matching import router as matching_router
from .notifications import router as notifications_router

__all__ = [
    'regions_router',
    'drivers_router', 
    'matching_router',
    'notifications_router'
]

