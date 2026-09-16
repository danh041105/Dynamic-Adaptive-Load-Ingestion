from fastapi import FastAPI
from backend.routes.auth_route import router as auth_router
from backend.routes.source_route import router as source_router
from backend.routes.de_route import router as de_router
from backend.routes.rf_route import router as rf_router
from backend.routes.download_request_route import router as download_request_router



app = FastAPI()

app.include_router(auth_router)
app.include_router(rf_router)
app.include_router(de_router)
app.include_router(source_router)
app.include_router(download_request_router)
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"} 
