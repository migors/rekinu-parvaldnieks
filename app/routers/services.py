"""Service / Product catalog API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user
from .. import crud, schemas

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=schemas.PaginatedServices)
def list_services(
    page: int = 1, 
    size: int = 10, 
    search: str = None, 
    db: Session = Depends(get_db), 
    user: str = Depends(get_current_user)
):
    return crud.get_services(db, page=page, size=size, search=search)


@router.get("/{service_id}", response_model=schemas.ServiceRead)
def read_service(service_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    svc = crud.get_service(db, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@router.post("", response_model=schemas.ServiceRead, status_code=201)
def create_service(data: schemas.ServiceCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return crud.create_service(db, data)


@router.put("/{service_id}", response_model=schemas.ServiceRead)
def update_service(service_id: int, data: schemas.ServiceUpdate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    svc = crud.update_service(db, service_id, data)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    if not crud.delete_service(db, service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"ok": True}
