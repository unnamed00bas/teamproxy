from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    deployments,
    dns,
    health,
    nodes,
    peers,
    publications,
    published,
    services,
    settings,
    sites,
    tls,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sites.router, prefix="/sites", tags=["sites"])
api_router.include_router(peers.router, prefix="/peers", tags=["peers"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(
    published.router, prefix="/published-services", tags=["published-services"]
)
api_router.include_router(publications.router, prefix="/publications", tags=["publications"])
api_router.include_router(dns.router, prefix="/dns", tags=["dns"])
api_router.include_router(tls.router, prefix="/tls", tags=["tls"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(deployments.router, prefix="/deployments", tags=["deployments"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
