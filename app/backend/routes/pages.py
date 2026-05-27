from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])

STATIC = Path(__file__).resolve().parents[2] / "static"


@router.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@router.get("/projects/{project_id}")
def project_page(project_id: str):
    return FileResponse(STATIC / "index.html")


@router.get("/requirements/{req_id}")
def requirement_page(req_id: str):
    return FileResponse(STATIC / "index.html")
