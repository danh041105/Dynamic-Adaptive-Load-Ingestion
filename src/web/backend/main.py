from fastapi import FastAPI
from backend.routes.auth_route import router as auth_router

app = FastAPI()
app.include_router(auth_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}