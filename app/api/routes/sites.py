from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.salon import Salon, SiteCustomization

router = APIRouter(prefix="/salons", tags=["Site Customization"])


class SiteCustomizationUpdate(BaseModel):
    template_name: Optional[str] = None
    color_scheme: Optional[Dict[str, str]] = None
    fonts: Optional[Dict[str, str]] = None
    hero_section: Optional[Dict[str, Any]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    custom_text_ru: Optional[str] = None
    custom_text_kk: Optional[str] = None
    custom_text_en: Optional[str] = None
    favicon_url: Optional[str] = None
    seo_settings: Optional[Dict[str, Any]] = None


@router.get("/{salon_id}/site")
async def get_site_customization(
    salon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current site customization settings"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Get customization
    customization = (
        db.query(SiteCustomization).filter(SiteCustomization.salon_id == salon_id).first()
    )

    if not customization:
        # Return default configuration
        return {
            "template_name": "modern",
            "color_scheme": {
                "primary_color": "#3B82F6",
                "secondary_color": "#1E40AF",
                "accent_color": "#F59E0B",
                "text_color": "#1F2937",
                "background_color": "#FFFFFF",
            },
            "fonts": {"heading_font": "Inter", "body_font": "Inter"},
            "hero_section": {
                "title": salon.display_name,
                "subtitle": "Professional beauty services",
                "background_image_url": salon.cover_image_url,
                "cta_button_text": "Book Now",
            },
            "sections": [
                {"section_type": "about", "is_visible": True, "sort_order": 1},
                {"section_type": "services", "is_visible": True, "sort_order": 2},
                {"section_type": "masters", "is_visible": True, "sort_order": 3},
                {"section_type": "portfolio", "is_visible": True, "sort_order": 4},
                {"section_type": "reviews", "is_visible": True, "sort_order": 5},
                {"section_type": "contacts", "is_visible": True, "sort_order": 6},
            ],
            "seo_settings": {
                "meta_title": salon.display_name,
                "meta_description": salon.description_ru or "",
                "meta_keywords": "",
            },
        }

    return {
        "template_name": customization.template_name,
        "color_scheme": customization.color_scheme,
        "fonts": customization.fonts,
        "hero_section": customization.hero_section,
        "sections": customization.sections,
        "custom_text_ru": customization.custom_text_ru,
        "custom_text_kk": customization.custom_text_kk,
        "custom_text_en": customization.custom_text_en,
        "favicon_url": customization.favicon_url,
        "seo_settings": customization.seo_settings,
    }


@router.put("/{salon_id}/site")
async def update_site_customization(
    salon_id: UUID,
    customization_data: SiteCustomizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update site customization settings"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Validate template
    valid_templates = ["modern", "classic", "minimalist", "luxury"]
    if customization_data.template_name and customization_data.template_name not in valid_templates:
        raise HTTPException(status_code=400, detail=f"Invalid template. Choose from: {valid_templates}")

    # Validate color scheme hex codes
    if customization_data.color_scheme:
        import re

        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for color_key, color_value in customization_data.color_scheme.items():
            if not hex_pattern.match(color_value):
                raise HTTPException(
                    status_code=400, detail=f"Invalid hex color code for {color_key}: {color_value}"
                )

    # Get or create customization
    customization = (
        db.query(SiteCustomization).filter(SiteCustomization.salon_id == salon_id).first()
    )

    if not customization:
        customization = SiteCustomization(salon_id=salon_id)
        db.add(customization)

    # Update fields
    if customization_data.template_name:
        customization.template_name = customization_data.template_name
    if customization_data.color_scheme:
        customization.color_scheme = customization_data.color_scheme
    if customization_data.fonts:
        customization.fonts = customization_data.fonts
    if customization_data.hero_section:
        customization.hero_section = customization_data.hero_section
    if customization_data.sections:
        customization.sections = customization_data.sections
    if customization_data.custom_text_ru is not None:
        customization.custom_text_ru = customization_data.custom_text_ru
    if customization_data.custom_text_kk is not None:
        customization.custom_text_kk = customization_data.custom_text_kk
    if customization_data.custom_text_en is not None:
        customization.custom_text_en = customization_data.custom_text_en
    if customization_data.favicon_url:
        customization.favicon_url = customization_data.favicon_url
    if customization_data.seo_settings:
        customization.seo_settings = customization_data.seo_settings

    db.commit()
    db.refresh(customization)

    # TODO: Invalidate site cache

    return {
        "message": "Site customization updated successfully",
        "template_name": customization.template_name,
    }


def generate_site_task(salon_id: str):
    """Background task to generate static site"""
    # TODO: Implement actual site generation logic
    # 1. Load salon data and customization
    # 2. Generate HTML/CSS/JS from template
    # 3. Upload to CDN or web server directory
    # 4. Update DNS if needed
    print(f"Generating site for salon {salon_id}...")


@router.post("/{salon_id}/site/publish", status_code=status.HTTP_202_ACCEPTED)
async def publish_site(
    salon_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish site changes (regenerate static site)"""
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Check permissions
    if salon.owner_id != current_user.id and current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Queue site generation
    background_tasks.add_task(generate_site_task, str(salon_id))

    return {
        "message": "Site publish initiated",
        "estimated_completion_time": "2 minutes",
        "site_url": f"https://{salon.slug}.jazyl.tech",
        "note": "In production, this would trigger static site generation and deployment",
    }
