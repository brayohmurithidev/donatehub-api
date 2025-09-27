import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.common.deps import require_tenant_admin
from app.common.handle_error import handle_error
from app.common.redis import get_redis
from app.common.upload import upload_image, upload_documents
from app.common.utils import generate_verification_token, generate_verification_url, verify_verification_token
from app.db.index import get_db
from app.features.tenant.models import TenantSupportDocuments, Tenant
from app.features.tenant.schemas import TenantCreate, TenantUpdate
from app.features.tenant.serializers import map_tenant_to_response_model
from app.features.tenant.services import get_all_tenants, get_tenant_by_id, create_new_tenant, update_tenant_data, \
    get_campaigns_by_tenant_id, get_documents_by_tenant_id
from app.logger import logger
from app.services.rabbitmq.publisher import publish_notification, RoutingKeys

router = APIRouter()

"""
Public routes:
1. Get all tenants
2. Get tenant by ID
3. Register tenant
"""


@router.get('/')
def get_tenants(
        db: Session = Depends(get_db),
        verified: Optional[bool] = Query(None, description="Filter by verified status"),
        search: Optional[str] = Query(None, description="Filter by tenant name"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=200, description="Number of results per page")
):
    redis = get_redis()
    cache_key = None
    if redis:
        cache_key = f"tenants:list:v1:verified={verified}:search={search}:page={page}:limit={limit}"
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached)

    tenants, total_count = get_all_tenants(db, verified, search, page, limit)

    if not tenants:
        raise HTTPException(status_code=404, detail="No tenants found")

    results = [
        map_tenant_to_response_model(tenant, total_campaigns, total_raised) for tenant, total_campaigns, total_raised in
        tenants
    ]
    logger.info("Fetched tenants")
    # Ensure JSON-serializable response for caching
    response = {
        "tenants": [r.model_dump() for r in results],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count // limit) + (1 if total_count % limit > 0 else 0)
        }
    }
    if redis and cache_key:
        try:
            redis.setex(cache_key, 60, json.dumps(response))
        except Exception:
            pass
    return response


# Get tenant documents
@router.get("/documents")
def get_tenant_documents(
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth

    if not tenant:
        handle_error(403, "You need to be a tenant admin to view documents")

    try:
        documents = get_documents_by_tenant_id(db, tenant.id)
        if not documents:
            handle_error(404, "No documents found")
        return documents

    except Exception as e:
        logger.error(e)
        handle_error(500, "Error fetching documents", e)


# VERIFY EMAIL
@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = verify_verification_token(token)
        tenant_id = payload.get("sub")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            handle_error(404, "Tenant not found")

        if tenant.is_email_verified:
            handle_error(400, "Email already verified")

        tenant.is_email_verified = True
        db.commit()

        return JSONResponse(
            status_code=200,
            content={"message": "Email verified successfully"}
        )

    except ExpiredSignatureError as e:
        handle_error(400, "Verification link expired", e)
    except JWTError as e:
        handle_error(400, "Invalid verification link", e)
    except HTTPException:
        raise
    except Exception as e:
        handle_error(500, "Unexpected server error", e)


@router.get("/{tenant_id}")
def get_tenant(
        tenant_id: UUID,
        db: Session = Depends(get_db)
):
    result = get_tenant_by_id(db, tenant_id=tenant_id)
    if not result:
        handle_error(404, "Tenant not found")
    tenant, total_campaigns, total_raised = result
    return map_tenant_to_response_model(tenant, total_campaigns, total_raised)


# Get tenant campaigns
@router.get("/{tenant_id}/campaigns")
def get_tenant_campaigns(
        tenant_id: UUID,
        search: Optional[str] = Query(None, description="Filter by campaign name"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=200, description="Number of results per page"),
        db: Session = Depends(get_db)
):
    tenant = get_tenant_by_id(db, tenant_id=tenant_id)
    if not tenant:
        handle_error(404, "Tenant not found")
    try:
        campaigns, total_count = get_campaigns_by_tenant_id(db, tenant_id, search, page, limit)
        return {
            "campaigns": campaigns,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count // limit) + (1 if total_count % limit > 0 else 0)
            }
        }
    except Exception as e:
        logger.error(e)
        handle_error(500, "Error fetching campaigns", e)


# REGISTER NEW TENANT
@router.post("/")
async def create_tenant(
        payload: TenantCreate,
        db: Session = Depends(get_db)
):
    req_body = payload.model_dump()
    new_tenant = create_new_tenant(db, req_body)
    # Bust cached tenants lists
    try:
        redis = get_redis()
        if redis:
            for key in redis.scan_iter("tenants:list:v1:*"):
                redis.delete(key)
    except Exception:
        pass

    token = generate_verification_token(str(new_tenant.id))
    verification_url = generate_verification_url(token)

    payload = {
        "email": new_tenant.email,
        "tenant_id": str(new_tenant.id),
        "name": new_tenant.name,
        "verification_url": verification_url,
        "logo_url": new_tenant.logo_url
    }
    # Publish email verification Message
    try:
        await publish_notification(
            RoutingKeys.EMAIL_VERIFICATION,
            payload
        )
    except Exception as e:
        logger.info(f"Failed to enqueue verification email: {e}")

    return map_tenant_to_response_model(new_tenant, 0, 0)


# Verify Email


"""
Protected routes:
1. Update Tenant
"""


@router.put("/update")
def update_tenant(
        payload: TenantUpdate,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    if not tenant:
        handle_error(403, "You need to be a tenant admin to update a tenant")
    req_body = payload.model_dump(exclude_unset=True)
    print("Request body: ", req_body)
    new_tenant = update_tenant_data(db, tenant.id, req_body)
    try:
        redis = get_redis()
        if redis:
            for key in redis.scan_iter("tenants:list:v1:*"):
                redis.delete(key)
    except Exception:
        pass
    return map_tenant_to_response_model(new_tenant, 0, 0)


@router.put("/update/logo")
def update_tenant_logo(
        logo: UploadFile = File(..., description="Logo file"),
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    if not tenant:
        handle_error(403, "You need to be a tenant admin to update a tenant")
    if not logo:
        handle_error(400, "Logo file is required")

    try:

        logo_url = upload_image(logo, "tenant_logos", public_id=tenant.id)

        tenant.logo_url = logo_url
        db.commit()
        db.refresh(tenant)

        response = {
            "message": "Logo updated successfully",
            "tenant": map_tenant_to_response_model(tenant, 0, 0)
        }
        try:
            redis = get_redis()
            if redis:
                for key in redis.scan_iter("tenants:list:v1:*"):
                    redis.delete(key)
        except Exception:
            pass
        return response
    except Exception as e:
        db.rollback()
        handle_error(500, "Error updating logo", e)


# Upload Validation Documents
@router.post("/update/validation_documents")
def update_tenant_validation_documents(
        registration: Optional[UploadFile] = File(None, description="Registration Document"),
        tax_certificate: Optional[UploadFile] = File(None, description="Tax Certificate"),
        governance_document: Optional[UploadFile] = File(None, description="Board Resolution / Governance structure"),
        identification: Optional[UploadFile] = File(None, description="Director/ Trustee ID"),
        bank: Optional[UploadFile] = File(None, description="Bank Verification Document"),
        financial_report: Optional[UploadFile] = File(None, description="Audited Financial Statements"),
        report: Optional[UploadFile] = File(None, description="Annual / Impact Report"),
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    uploaded_files = {
        "registration": registration,
        "tax_certificate": tax_certificate,
        "governance_document": governance_document,
        "identification": identification,
        "bank": bank,
        "financial_report": financial_report,
        "report": report
    }

    results = {}

    # result = upload_support_documents(db, tenant.id, uploaded_files)
    for key, file in uploaded_files.items():
        if file is None:
            continue
        try:
            file_ext = file.filename.split(".")[-1].lower()
            base_id = f"{key}_{tenant.id}"
            file_url = upload_documents(file, "tenant_support_documents", f"{key}_{tenant.id}")

            # Check if a document already exists
            existing_document = (db.query(TenantSupportDocuments).filter(TenantSupportDocuments.tenant_id == tenant.id,
                                                                         TenantSupportDocuments.document_base_id == base_id).first())

            if existing_document:
                existing_document.document_url = file_url
                existing_document.document_type = file_ext
                db.commit()
                db.refresh(existing_document)
                results[key] = {"status": "success", "url": file_url}
            else:
                document = TenantSupportDocuments(
                    tenant_id=tenant.id,
                    document_name=key,
                    document_base_id=base_id,
                    document_url=file_url,
                    document_type=file_ext
                )
                db.add(document)
                db.commit()
                db.refresh(document)

                results[key] = {"status": "success", "url": file_url}
        except HTTPException as e:
            db.rollback()
            handle_error(400, e.detail, e)

        except IntegrityError as e:
            db.rollback()
            handle_error(400, "Document already exists", e)

    return {"tenant_id": str(tenant.id), "documents": results}
