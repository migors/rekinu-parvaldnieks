"""Client API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user
from .. import crud, schemas

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=schemas.PaginatedClients)
def list_clients(
    page: int = 1, 
    size: int = 10, 
    search: str = None, 
    db: Session = Depends(get_db), 
    user: str = Depends(get_current_user)
):
    return crud.get_clients(db, page=page, size=size, search=search)


@router.get("/lookup/{reg_number}")
def lookup_company(reg_number: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Lookup company data by registration number."""
    from ..utils import fetch_company_data
    
    data = fetch_company_data(reg_number)
    if not data:
        raise HTTPException(status_code=404, detail="Company not found or API error")
        
    return data


@router.get("/search")
def search_clients_api(q: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Search companies by name (autocomplete)."""
    from ..utils import search_companies
    
    return search_companies(q)


@router.get("/{client_id}", response_model=schemas.ClientRead)
def read_client(client_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=schemas.ClientRead, status_code=201)
def create_client(data: schemas.ClientCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return crud.create_client(db, data)


@router.put("/{client_id}", response_model=schemas.ClientRead)
def update_client(client_id: int, data: schemas.ClientUpdate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    client = crud.update_client(db, client_id, data)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    if not crud.delete_client(db, client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"ok": True}



