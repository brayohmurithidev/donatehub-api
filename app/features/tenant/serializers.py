from app.features.tenant.schemas import TenantListOut


def map_tenant_to_response_model(tenant, total_campaigns, total_raised) -> TenantListOut:
    return TenantListOut(
        id=tenant.id,
        name=tenant.name,
        logo_url=tenant.logo_url,
        description=tenant.description,
        short_description=tenant.description[:100] + "..." if tenant.description else None,
        email=tenant.email,
        phone=tenant.phone,
        website=tenant.website,
        location=tenant.location,
        total_campaigns=total_campaigns,
        total_raised=round(total_raised, 2),
        is_verified=tenant.is_Verified,
        date_joined=tenant.created_at,
    )


