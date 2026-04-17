from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@router.get("/upload-service")
async def upload_page(request: Request):
    return templates.TemplateResponse(request=request, name="upload.html", context={})

@router.get("/live-service")
async def live_page(request: Request):
    return templates.TemplateResponse(request=request, name="live.html", context={})
    
@router.get("/history")
async def history_page(request: Request):
    return templates.TemplateResponse(request=request, name="history.html", context={})