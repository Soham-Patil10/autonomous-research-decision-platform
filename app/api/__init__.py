from fastapi import APIRouter

from app.api import routes_eval, routes_review, routes_tasks

api_router = APIRouter(prefix="/api")
api_router.include_router(routes_tasks.router)
api_router.include_router(routes_review.router)
api_router.include_router(routes_eval.router)

__all__ = ["api_router"]
