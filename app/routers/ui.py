from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# Point to the templates folder in the root
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def render_upload_page(request: Request):
    return templates.TemplateResponse(
    request=request, 
    name="index.html"
)