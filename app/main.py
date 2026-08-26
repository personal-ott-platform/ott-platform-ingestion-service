from app.api.v1.uploads import router as uploads_router
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Video Ingestion Pipeline", 
    description="APIs for complete video ingestion pipelines", 
    version="1.0.0",
)

app.include_router(uploads_router)

@app.get('/', include_in_schema=False)
async def root():
    return RedirectResponse(url='/docs')