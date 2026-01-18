from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.models import Base
from app.db.session import engine
from app.api.routes_hcps import router as hcps_router
from app.api.routes_interactions import router as interactions_router
from app.api.routes_agent import router as agent_router

def create_app():
    app = FastAPI(title="AI-First CRM HCP Module")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)

    app.include_router(hcps_router)
    app.include_router(interactions_router)
    app.include_router(agent_router)

    return app

app = create_app()
