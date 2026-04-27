import os
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote_plus

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, inspect, or_, text
from sqlalchemy.orm import Session

import db_models
from database import engine, get_db
from models import (
    AgentSignup,
    AuditLogRead,
    AvailabilityRead,
    BonusInfoSection,
    DashboardStats,
    FeatureCreate,
    FeatureRead,
    HeroSlideCreate,
    ListingCreate,
    ListingRead,
    ListingSaleCreate,
    ListingSaleRead,
    ListingUpdate,
    ListingViewCreate,
    ListingViewRead,
    LoginPayload,
    NoteCreate,
    OfferCreate,
    ReactionCreate,
    ReactionRead,
    SiteVisitCreate,
    StatusUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
    WishCreate,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BONUS_INFO_PATH = PROJECT_ROOT / "docs" / "bonus_info.md"
DEFAULT_UPLOADS_DIR = Path("/tmp/uploads") if os.getenv("VERCEL") else PROJECT_ROOT / "backend" / "uploads"
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", str(DEFAULT_UPLOADS_DIR)))
DEFAULT_AGENT_AVATAR_BACKGROUND = "f3ede4"
DEFAULT_AGENT_AVATAR_COLOR = "ef5b2b"


def build_default_agent_avatar(first_name: str, last_name: str) -> str:
    name = quote_plus(f"{first_name} {last_name}".strip() or "SAM Agent")
    return (
        "https://ui-avatars.com/api/"
        f"?name={name}"
        f"&background={DEFAULT_AGENT_AVATAR_BACKGROUND}"
        f"&color={DEFAULT_AGENT_AVATAR_COLOR}"
        "&bold=true"
        "&format=svg"
    )


def log_action(
    db: Session,
    *,
    action: str,
    entity_type: str,
    description: str,
    actor_id: int | None = None,
    entity_id: int | None = None,
) -> None:
    db.add(
        db_models.AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            actor_id=actor_id,
        )
    )


def sync_existing_schema() -> None:
    metadata = db_models.Base.metadata
    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())

        for table in metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            existing_columns = {
                column_info["name"] for column_info in inspector.get_columns(table.name)
            }
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                column_type = column.type.compile(dialect=engine.dialect)
                connection.execute(
                    text(
                        f'ALTER TABLE "{table.name}" '
                        f'ADD COLUMN "{column.name}" {column_type}'
                    )
                )

        connection.execute(
            text(
                "UPDATE users SET sales_closed = 0 "
                "WHERE sales_closed IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE users SET is_google_account = false "
                "WHERE is_google_account IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE listings SET approval_status = 'approved' "
                "WHERE approval_status IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE listings SET category = 'Land' "
                "WHERE category IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE listings SET is_featured = false "
                "WHERE is_featured IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE listings SET total_views = 0 "
                "WHERE total_views IS NULL"
            )
        )
        connection.execute(
            text(
                "UPDATE listings SET total_sales = 0 "
                "WHERE total_sales IS NULL"
            )
        )
        for table in metadata.sorted_tables:
            column_names = {column.name for column in table.columns}
            if "created_at" in column_names:
                connection.execute(
                    text(
                        f'UPDATE "{table.name}" SET created_at = NOW() '
                        "WHERE created_at IS NULL"
                    )
                )
            if "updated_at" in column_names:
                connection.execute(
                    text(
                        f'UPDATE "{table.name}" SET updated_at = NOW() '
                        "WHERE updated_at IS NULL"
                    )
                )


def seed_defaults() -> None:
    db = next(get_db())
    try:
        default_users = [
            {
                "email": "hmosem@gmail.com",
                "username": "hmosem",
                "password": "12345678",
                "role": "super_admin",
                "status": "active",
                "first_name": "Hosem",
                "last_name": "Manager",
                "full_name": "SAM Super Admin",
                "phone_number": "+256763615316",
                "profile_picture": "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=900&q=80",
                "district": "Mukono",
                "village": "Kiwanga",
            },
            {
                "email": "nabasabrianish1@gmail.com",
                "username": "nabasabrianish1",
                "password": "12345678",
                "role": "agent",
                "status": "approved",
                "first_name": "Brian",
                "last_name": "Nabasa",
                "full_name": "Brian Nabasa",
                "phone_number": "+256752440513",
                "profile_picture": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80",
                "district": "Wakiso",
                "village": "Bweyogerere",
                "experience": "6 years",
                "sales_closed": 18,
            },
            {
                "email": "ghatejeka@gmail.com",
                "username": "ghatejeka",
                "password": "12345678",
                "role": "admin",
                "status": "active",
                "first_name": "Gha",
                "last_name": "Tejeka",
                "full_name": "SAM Admin",
                "phone_number": "+256701000001",
                "profile_picture": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=900&q=80",
                "district": "Kampala",
                "village": "Ntinda",
            },
            {
                "email": "sarah.namubiru@sam.ug",
                "username": "sarahnamubiru",
                "password": "12345678",
                "role": "agent",
                "status": "approved",
                "first_name": "Sarah",
                "last_name": "Namubiru",
                "full_name": "Sarah Namubiru",
                "phone_number": "+256706000102",
                "profile_picture": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=80",
                "district": "Wakiso",
                "village": "Entebbe",
                "experience": "4 years",
                "sales_closed": 11,
            },
            {
                "email": "david.kato@sam.ug",
                "username": "davidkato",
                "password": "12345678",
                "role": "agent",
                "status": "approved",
                "first_name": "David",
                "last_name": "Kato",
                "full_name": "David Kato",
                "phone_number": "+256703000103",
                "profile_picture": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80",
                "district": "Mukono",
                "village": "Seeta",
                "experience": "8 years",
                "sales_closed": 23,
            },
            {
                "email": "ruth.atwine@sam.ug",
                "username": "ruthatwine",
                "password": "12345678",
                "role": "agent",
                "status": "approved",
                "first_name": "Ruth",
                "last_name": "Atwine",
                "full_name": "Ruth Atwine",
                "phone_number": "+256704000104",
                "profile_picture": "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=900&q=80",
                "district": "Kampala",
                "village": "Muyenga",
                "experience": "5 years",
                "sales_closed": 14,
            },
        ]

        user_lookup: dict[str, db_models.User] = {}
        user_lookup_by_email: dict[str, db_models.User] = {}
        for payload in default_users:
            user = db.query(db_models.User).filter(db_models.User.email == payload["email"]).first()
            if not user:
                user = db_models.User(**payload)
                db.add(user)
                db.flush()
                log_action(
                    db,
                    action="seed_user",
                    entity_type="user",
                    entity_id=user.id,
                    description=f"Seeded default {user.role} account",
                    actor_id=user.id,
                )
            else:
                if payload["role"] in {"super_admin", "admin"}:
                    for field in ("password", "role", "status"):
                        setattr(user, field, payload[field])
                for field, value in payload.items():
                    if getattr(user, field, None) in (None, "") and value not in (None, ""):
                        setattr(user, field, value)
            user_lookup[payload["role"]] = user
            user_lookup_by_email[payload["email"]] = user

        if db.query(db_models.HeroSlide).count() == 0:
            for index in range(1, 6):
                db.add(
                    db_models.HeroSlide(
                        title=f"Exceptional properties {index}",
                        subtitle="Discover trusted land opportunities with SAM.UG",
                        image_url=f"/src/assets/hero/banner-{index}.jpg",
                        is_active=True,
                    )
                )

        listing_payloads = [
            {
                "title": "Serviced Plots in Mukono",
                "description": "Verified residential plots with flexible payment options and fast follow-up from the SAM team.",
                "price": 45000000,
                "district": "Mukono",
                "city": "Mukono",
                "address": "Namanve Industrial Park",
                "status": "available",
                "approval_status": "approved",
                "category": "Residential Land",
                "size_text": "50ft x 100ft",
                "purpose": "Residential",
                "thumbnail_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True,
                "total_views": 124,
                "total_sales": 3,
                "owner_email": "nabasabrianish1@gmail.com",
            },
            {
                "title": "Commercial Frontage Near Jinja Road",
                "description": "High-visibility frontage ideal for warehouses, retail, or mixed-use development.",
                "price": 125000000,
                "district": "Wakiso",
                "city": "Kira",
                "address": "Off Jomayi Stones",
                "status": "sold",
                "approval_status": "approved",
                "category": "Commercial Land",
                "size_text": "100ft x 100ft",
                "purpose": "Commercial",
                "thumbnail_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 92,
                "total_sales": 1,
                "owner_email": "ghatejeka@gmail.com",
            },
            {
                "title": "Agricultural Block With Access Road",
                "description": "Well-documented agricultural land with clear access and room for expansion.",
                "price": 78000000,
                "district": "Mukono",
                "city": "Katosi",
                "address": "Katosi Road",
                "status": "available",
                "approval_status": "approved",
                "category": "Agricultural Land",
                "size_text": "2 Acres",
                "purpose": "Agricultural",
                "thumbnail_url": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 41,
                "total_sales": 0,
                "owner_email": "david.kato@sam.ug",
            },
            {
                "title": "Lake View Family Estate in Entebbe",
                "description": "A premium residential estate parcel with lake views, paved access and ready utilities.",
                "price": 210000000,
                "district": "Wakiso",
                "city": "Entebbe",
                "address": "Garuga Hill",
                "status": "available",
                "approval_status": "approved",
                "category": "Residential Land",
                "size_text": "80ft x 120ft",
                "purpose": "Residential",
                "thumbnail_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1473448912268-2022ce9509d8?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True,
                "total_views": 186,
                "total_sales": 4,
                "owner_email": "sarah.namubiru@sam.ug",
            },
            {
                "title": "Townhouse Development Site in Naalya",
                "description": "Strategic infill site suitable for a townhouse cluster with strong middle-income demand.",
                "price": 165000000,
                "district": "Kampala",
                "city": "Naalya",
                "address": "Naalya Estate Road",
                "status": "available",
                "approval_status": "approved",
                "category": "Development Land",
                "size_text": "25 Decimals",
                "purpose": "Mixed Use",
                "thumbnail_url": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 153,
                "total_sales": 2,
                "owner_email": "ruth.atwine@sam.ug",
            },
            {
                "title": "Retail Plot Along Northern Bypass",
                "description": "A high-traffic roadside plot with excellent visibility for showrooms, fuel or neighborhood retail.",
                "price": 98000000,
                "district": "Wakiso",
                "city": "Bweyogerere",
                "address": "Northern Bypass Spur",
                "status": "sold",
                "approval_status": "approved",
                "category": "Commercial Land",
                "size_text": "70ft x 100ft",
                "purpose": "Commercial",
                "thumbnail_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 77,
                "total_sales": 1,
                "owner_email": "nabasabrianish1@gmail.com",
            },
            {
                "title": "Countryside Farm With Banana Plantation",
                "description": "Income-generating agricultural land with a mature plantation, water access and gentle slopes.",
                "price": 132000000,
                "district": "Mityana",
                "city": "Mityana",
                "address": "Mityana Farm Belt",
                "status": "available",
                "approval_status": "approved",
                "category": "Agricultural Land",
                "size_text": "6 Acres",
                "purpose": "Agricultural",
                "thumbnail_url": "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 68,
                "total_sales": 0,
                "owner_email": "david.kato@sam.ug",
            },
            {
                "title": "Executive Homesite in Muyenga",
                "description": "Ready-to-build homesite in a quiet upscale neighborhood with quick access to city conveniences.",
                "price": 245000000,
                "district": "Kampala",
                "city": "Muyenga",
                "address": "Tank Hill Road",
                "status": "sold",
                "approval_status": "approved",
                "category": "Residential Land",
                "size_text": "30 Decimals",
                "purpose": "Residential",
                "thumbnail_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 205,
                "total_sales": 5,
                "owner_email": "sarah.namubiru@sam.ug",
            },
            {
                "title": "Hilltop Residential Plots in Matugga",
                "description": "Gently elevated residential plots with neighborhood road access and strong buyer interest.",
                "price": 62000000,
                "district": "Wakiso",
                "city": "Matugga",
                "address": "Matugga Hill",
                "status": "available",
                "approval_status": "approved",
                "category": "Residential Land",
                "size_text": "60ft x 100ft",
                "purpose": "Residential",
                "thumbnail_url": "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 83,
                "total_sales": 1,
                "owner_email": "ruth.atwine@sam.ug",
            },
            {
                "title": "Industrial Yard Opportunity in Namanve",
                "description": "Industrial land suitable for storage, logistics and light manufacturing with direct highway access.",
                "price": 310000000,
                "district": "Mukono",
                "city": "Namanve",
                "address": "Namanve Industrial Zone",
                "status": "available",
                "approval_status": "approved",
                "category": "Industrial Land",
                "size_text": "1.5 Acres",
                "purpose": "Industrial",
                "thumbnail_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True,
                "total_views": 146,
                "total_sales": 2,
                "owner_email": "ghatejeka@gmail.com",
            },
            {
                "title": "Subdivision Acreage in Gayaza",
                "description": "Well-positioned acreage ideal for phased subdivision and family estate planning.",
                "price": 188000000,
                "district": "Wakiso",
                "city": "Gayaza",
                "address": "Gayaza Corridor",
                "status": "available",
                "approval_status": "approved",
                "category": "Development Land",
                "size_text": "4 Acres",
                "purpose": "Subdivision",
                "thumbnail_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 71,
                "total_sales": 0,
                "owner_email": "sarah.namubiru@sam.ug",
            },
            {
                "title": "Roadside Trading Plot in Lugazi",
                "description": "Compact roadside plot positioned for shops, trading units and fast-moving retail frontage.",
                "price": 54000000,
                "district": "Buikwe",
                "city": "Lugazi",
                "address": "Lugazi Main Road",
                "status": "available",
                "approval_status": "approved",
                "category": "Commercial Land",
                "size_text": "40ft x 80ft",
                "purpose": "Commercial",
                "thumbnail_url": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 59,
                "total_sales": 1,
                "owner_email": "nabasabrianish1@gmail.com",
            },
            {
                "title": "Fenced Banana Farm in Masaka",
                "description": "Productive farm parcel with established bananas, fencing and reliable seasonal access.",
                "price": 225000000,
                "district": "Masaka",
                "city": "Masaka",
                "address": "Masaka Farm Belt",
                "status": "available",
                "approval_status": "approved",
                "category": "Agricultural Land",
                "size_text": "9 Acres",
                "purpose": "Agricultural",
                "thumbnail_url": "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 132,
                "total_sales": 3,
                "owner_email": "david.kato@sam.ug",
            },
            {
                "title": "Investment Plots Near Seeta Town",
                "description": "Fast-selling investment plots close to the highway, schools and emerging commercial amenities.",
                "price": 58000000,
                "district": "Mukono",
                "city": "Seeta",
                "address": "Seeta Growth Corridor",
                "status": "sold",
                "approval_status": "approved",
                "category": "Residential Land",
                "size_text": "50ft x 100ft",
                "purpose": "Investment",
                "thumbnail_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1473448912268-2022ce9509d8?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "total_views": 97,
                "total_sales": 2,
                "owner_email": "ruth.atwine@sam.ug",
            },
            {
                "title": "School Development Site in Mpigi",
                "description": "Expansive level site appropriate for institutional development, sports grounds and phased construction.",
                "price": 275000000,
                "district": "Mpigi",
                "city": "Mpigi",
                "address": "Mpigi Education Corridor",
                "status": "available",
                "approval_status": "approved",
                "category": "Institutional Land",
                "size_text": "5 Acres",
                "purpose": "Institutional",
                "thumbnail_url": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1200&q=80",
                "pictures": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1200&q=80,https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True,
                "total_views": 111,
                "total_sales": 1,
                "owner_email": "ghatejeka@gmail.com",
            },
        ]
        for payload in listing_payloads:
            owner = user_lookup_by_email[payload["owner_email"]]
            listing_data = {key: value for key, value in payload.items() if key != "owner_email"}
            listing = db.query(db_models.Listing).filter(db_models.Listing.title == payload["title"]).first()
            if not listing:
                listing = db_models.Listing(**listing_data, owner_id=owner.id)
                db.add(listing)
                db.flush()
                log_action(
                    db,
                    action="seed_listing",
                    entity_type="listing",
                    entity_id=listing.id,
                    description=f"Seeded listing {listing.title}",
                    actor_id=listing.owner_id,
                )
            else:
                for field, value in listing_data.items():
                    if getattr(listing, field, None) in (None, "") and value not in (None, ""):
                        setattr(listing, field, value)
                listing.thumbnail_url = listing_data["thumbnail_url"]
                listing.pictures = listing_data["pictures"]
                listing.is_featured = listing_data["is_featured"]
                if listing.status != listing_data["status"]:
                    listing.status = listing_data["status"]
                if not listing.owner_id:
                    listing.owner_id = owner.id

        db.commit()
    finally:
        db.close()


app = FastAPI(title="SAM API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://sam-demo-delta.vercel.app",
    ],
    # Allows Vercel preview/production domains such as:
    # https://sam-demo-delta.vercel.app and future generated preview URLs.
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local uploads work normally. On Vercel, /tmp is temporary and not persistent,
# so use this only for testing. For production uploads, use Cloudinary/S3/etc.
try:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
except Exception as exc:
    print(f"Uploads disabled: {exc}")


def verify_admin_task_token(request: Request) -> None:
    """
    Optional protection for manual admin routes.
    If ADMIN_TASK_TOKEN is set, callers must send: x-admin-token: <token>
    If ADMIN_TASK_TOKEN is not set, routes remain open for local/testing use.
    """
    expected_token = os.getenv("ADMIN_TASK_TOKEN")
    if expected_token and request.headers.get("x-admin-token") != expected_token:
        raise HTTPException(status_code=403, detail="Invalid or missing admin task token")


def initialize_database() -> None:
    db_models.Base.metadata.create_all(bind=engine)
    sync_existing_schema()

def parse_bonus_sections() -> list[BonusInfoSection]:
    if not BONUS_INFO_PATH.exists():
        return []

    sections: list[BonusInfoSection] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    for raw_line in BONUS_INFO_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current_lines:
                sections.append(
                    BonusInfoSection(
                        heading=current_heading,
                        body="\n".join(current_lines).strip(),
                    )
                )
            current_heading = line.removeprefix("## ").strip()
            current_lines = []
            continue
        if line:
            current_lines.append(line)

    if current_lines:
        sections.append(
            BonusInfoSection(
                heading=current_heading,
                body="\n".join(current_lines).strip(),
            )
        )

    return sections


@app.get("/")
def greeting():
    return {"message": "SAM API is running successfully"}


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"message": "Database connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/init-db")
def init_db(request: Request):
    try:
        verify_admin_task_token(request)
        initialize_database()
        return {"message": "Database initialized successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insert-seed")
def insert_seed(request: Request):
    try:
        verify_admin_task_token(request)
        seed_defaults()
        return {"message": "Seed data inserted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    password = payload.password.strip()
    user = (
        db.query(db_models.User)
        .filter(
            or_(
                func.lower(db_models.User.email) == identifier.lower(),
                func.lower(db_models.User.username) == identifier.lower(),
                db_models.User.phone_number == identifier,
            )
        )
        .first()
    )
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role == "agent" and user.status in {"rejected", "deactivated"}:
        raise HTTPException(status_code=403, detail="Agent account is not active")

    log_action(
        db,
        action="login",
        entity_type="user",
        entity_id=user.id,
        description=f"{user.role} logged into the platform",
        actor_id=user.id,
    )
    db.commit()
    return {"message": "Login successful", "user": UserRead.model_validate(user)}


@app.get("/auth/check-availability", response_model=AvailabilityRead)
def check_availability(field: str, value: str, db: Session = Depends(get_db)):
    normalized = value.strip()
    allowed_fields = {"username", "email", "phone_number"}
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Unsupported field")
    if not normalized:
        return AvailabilityRead(
            field=field,
            value=normalized,
            available=False,
            message=f"{field.replace('_', ' ').title()} is required",
        )

    column = getattr(db_models.User, field)
    query_value = normalized.lower() if field in {"username", "email"} else normalized
    existing = (
        db.query(db_models.User)
        .filter(func.lower(column) == query_value if field in {"username", "email"} else column == query_value)
        .first()
    )
    label = field.replace("_", " ")
    return AvailabilityRead(
        field=field,
        value=normalized,
        available=existing is None,
        message=f"{label.title()} is available" if existing is None else f"{label.title()} is already in use",
    )


@app.post("/auth/agents/signup", response_model=UserRead, status_code=201)
def signup_agent(payload: AgentSignup, db: Session = Depends(get_db)):
    conflicts = [
        func.lower(db_models.User.email) == payload.email.lower(),
        func.lower(db_models.User.username) == payload.username.lower(),
    ]
    if payload.phone_number:
        conflicts.append(db_models.User.phone_number == payload.phone_number)
    existing_user = (
        db.query(db_models.User)
        .filter(or_(*conflicts))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    user = db_models.User(
        email=payload.email,
        username=payload.username,
        phone_number=payload.phone_number,
        password=payload.password,
        role="agent",
        status="pending",
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=f"{payload.first_name} {payload.last_name}",
        profile_picture=build_default_agent_avatar(
            payload.first_name,
            payload.last_name,
        ),
    )
    db.add(user)
    db.flush()
    log_action(
        db,
        action="agent_signup",
        entity_type="user",
        entity_id=user.id,
        description="Agent account created and waiting for approval",
        actor_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@app.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    conflicts = [func.lower(db_models.User.email) == payload.email.lower()]
    if payload.username:
        conflicts.append(func.lower(db_models.User.username) == payload.username.lower())
    if payload.phone_number:
        conflicts.append(db_models.User.phone_number == payload.phone_number)
    existing_user = (
        db.query(db_models.User)
        .filter(or_(*conflicts))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="Username, email, or phone number already exists")

    user = db_models.User(**payload.model_dump())
    db.add(user)
    db.flush()
    log_action(
        db,
        action="create_user",
        entity_type="user",
        entity_id=user.id,
        description=f"Created {user.role} account",
        actor_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[UserRead])
def list_users(role: str | None = None, db: Session = Depends(get_db)):
    query = db.query(db_models.User)
    if role:
        query = query.filter(db_models.User.role == role)
    return query.order_by(db_models.User.created_at.desc()).all()


@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(db_models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    log_action(
        db,
        action="update_user",
        entity_type="user",
        entity_id=user.id,
        description="Updated user profile information",
        actor_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}/approve", response_model=UserRead)
def approve_agent(user_id: int, db: Session = Depends(get_db)):
    user = db.get(db_models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = "approved"
    log_action(
        db,
        action="approve_agent",
        entity_type="user",
        entity_id=user.id,
        description="Agent account approved",
        actor_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}/reject", response_model=UserRead)
def reject_agent(user_id: int, db: Session = Depends(get_db)):
    user = db.get(db_models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = "rejected"
    log_action(
        db,
        action="reject_agent",
        entity_type="user",
        entity_id=user.id,
        description="Agent account rejected",
        actor_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(db_models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = "deactivated"
    log_action(
        db,
        action="deactivate_user",
        entity_type="user",
        entity_id=user.id,
        description="User account deactivated",
        actor_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(db_models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    has_related_records = any(
        (
            db.query(db_models.Listing.id)
            .filter(db_models.Listing.owner_id == user_id)
            .first(),
            db.query(db_models.Offer.id)
            .filter(db_models.Offer.user_id == user_id)
            .first(),
            db.query(db_models.Note.id)
            .filter(db_models.Note.user_id == user_id)
            .first(),
            db.query(db_models.AuditLog.id)
            .filter(db_models.AuditLog.actor_id == user_id)
            .first(),
        )
    )
    if has_related_records:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete this profile because it has related records.",
        )

    db.delete(user)
    db.commit()


@app.get("/hero-slides")
def list_hero_slides(db: Session = Depends(get_db)):
    return (
        db.query(db_models.HeroSlide)
        .filter(db_models.HeroSlide.is_active.is_(True))
        .all()
    )


@app.post("/hero-slides", status_code=201)
def create_hero_slide(payload: HeroSlideCreate, db: Session = Depends(get_db)):
    slide = db_models.HeroSlide(**payload.model_dump())
    db.add(slide)
    db.flush()
    log_action(
        db,
        action="create_hero_slide",
        entity_type="hero_slide",
        entity_id=slide.id,
        description=f"Created hero slide {slide.title}",
    )
    db.commit()
    return slide


@app.get("/listings", response_model=list[ListingRead])
def list_listings(
    featured: bool | None = None,
    latest: bool = False,
    district: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    owner_id: int | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(db_models.Listing)
    if featured is not None:
        query = query.filter(db_models.Listing.is_featured == featured)
    if district:
        query = query.filter(db_models.Listing.district.ilike(f"%{district}%"))
    if min_price is not None:
        query = query.filter(db_models.Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(db_models.Listing.price <= max_price)
    if owner_id:
        query = query.filter(db_models.Listing.owner_id == owner_id)
    if role == "agent" and owner_id:
        query = query.filter(db_models.Listing.owner_id == owner_id)

    ordering = (
        db_models.Listing.created_at.desc()
        if latest
        else db_models.Listing.is_featured.desc()
    )
    return query.order_by(ordering, db_models.Listing.created_at.desc()).all()


@app.get("/listings/{listing_id}", response_model=ListingRead)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(db_models.Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@app.post("/listings", response_model=ListingRead, status_code=201)
def create_listing(payload: ListingCreate, db: Session = Depends(get_db)):
    owner = db.get(db_models.User, payload.owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    listing = db_models.Listing(
        **payload.model_dump(exclude={"pictures"}),
        pictures=",".join(payload.pictures),
    )
    db.add(listing)
    db.flush()
    log_action(
        db,
        action="create_listing",
        entity_type="listing",
        entity_id=listing.id,
        description=f"Created listing {listing.title}",
        actor_id=listing.owner_id,
    )
    db.commit()
    db.refresh(listing)
    return listing


@app.post("/uploads/images")
async def upload_images(request: Request, files: list[UploadFile] = File(...)):
    urls: list[str] = []
    allowed_content_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    for file in files[:5]:
        if file.content_type not in allowed_content_types:
            raise HTTPException(status_code=400, detail="Only image uploads are allowed")

        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            suffix = ".jpg"

        filename = f"{uuid4().hex}{suffix}"
        target = UPLOADS_DIR / filename
        contents = await file.read()
        target.write_bytes(contents)
        urls.append(str(request.url_for("uploads", path=filename)))

    return {"urls": urls}


@app.patch("/listings/{listing_id}", response_model=ListingRead)
def update_listing(
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
):
    listing = db.get(db_models.Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    updates = payload.model_dump(exclude_unset=True)
    pictures = updates.pop("pictures", None)
    for field, value in updates.items():
        setattr(listing, field, value)
    if pictures is not None:
        listing.pictures = ",".join(pictures)

    log_action(
        db,
        action="update_listing",
        entity_type="listing",
        entity_id=listing.id,
        description=f"Updated listing {listing.title}",
        actor_id=listing.owner_id,
    )
    db.commit()
    db.refresh(listing)
    return listing


@app.post("/listings/{listing_id}/sale", response_model=ListingSaleRead, status_code=201)
def register_listing_sale(
    listing_id: int,
    payload: ListingSaleCreate,
    db: Session = Depends(get_db),
):
    listing = db.get(db_models.Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    existing_sale = (
        db.query(db_models.ListingSale)
        .filter(db_models.ListingSale.listing_id == listing_id)
        .first()
    )
    if existing_sale:
        raise HTTPException(status_code=409, detail="Listing sale already registered")

    sale = db_models.ListingSale(
        listing_id=listing_id,
        sale_price=payload.sale_price,
        sold_at=payload.sold_at,
        registered_by_id=payload.registered_by_id,
    )
    listing.status = "sold"
    listing.total_sales = max(listing.total_sales or 0, 1)
    db.add(sale)
    db.flush()
    log_action(
        db,
        action="register_listing_sale",
        entity_type="listing",
        entity_id=listing.id,
        description=f"Registered sale for {listing.title}",
        actor_id=payload.registered_by_id,
    )
    db.commit()
    db.refresh(sale)
    return sale


@app.delete("/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(db_models.Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    owner_id = listing.owner_id
    title = listing.title
    offer_ids = [
        offer_id
        for (offer_id,) in db.query(db_models.Offer.id)
        .filter(db_models.Offer.listing_id == listing_id)
        .all()
    ]
    site_visit_ids = [
        site_visit_id
        for (site_visit_id,) in db.query(db_models.SiteVisit.id)
        .filter(db_models.SiteVisit.listing_id == listing_id)
        .all()
    ]
    db.query(db_models.Note).filter(db_models.Note.listing_id == listing_id).delete(
        synchronize_session=False
    )
    if offer_ids:
        db.query(db_models.Note).filter(db_models.Note.offer_id.in_(offer_ids)).delete(
            synchronize_session=False
        )
    if site_visit_ids:
        db.query(db_models.Note).filter(
            db_models.Note.site_visit_id.in_(site_visit_ids)
        ).delete(synchronize_session=False)
    db.query(db_models.ListingView).filter(
        db_models.ListingView.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.query(db_models.ListingSale).filter(
        db_models.ListingSale.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.query(db_models.Comment).filter(
        db_models.Comment.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.query(db_models.Feature).filter(
        db_models.Feature.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.query(db_models.Reaction).filter(
        db_models.Reaction.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.query(db_models.Offer).filter(
        db_models.Offer.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.query(db_models.SiteVisit).filter(
        db_models.SiteVisit.listing_id == listing_id
    ).delete(synchronize_session=False)
    db.delete(listing)
    log_action(
        db,
        action="delete_listing",
        entity_type="listing",
        entity_id=listing_id,
        description=f"Deleted listing {title}",
        actor_id=owner_id,
    )
    db.commit()


@app.post("/listings/{listing_id}/view", response_model=ListingViewRead, status_code=201)
def register_listing_view(
    listing_id: int,
    payload: ListingViewCreate,
    db: Session = Depends(get_db),
):
    listing = db.get(db_models.Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    viewer_key = payload.viewer_key.strip()
    if not viewer_key:
        raise HTTPException(status_code=400, detail="viewer_key is required")

    now = datetime.utcnow()
    threshold = now - timedelta(hours=24)

    existing_view = (
        db.query(db_models.ListingView)
        .filter(
            db_models.ListingView.listing_id == listing_id,
            db_models.ListingView.viewer_key == viewer_key,
        )
        .first()
    )

    counted = False
    if existing_view is None:
        db.add(
            db_models.ListingView(
                listing_id=listing_id,
                viewer_key=viewer_key,
                last_viewed_at=now,
            )
        )
        listing.total_views += 1
        counted = True
    elif existing_view.last_viewed_at <= threshold:
        existing_view.last_viewed_at = now
        listing.total_views += 1
        counted = True

    db.commit()
    db.refresh(listing)
    return ListingViewRead(
        listing_id=listing.id,
        total_views=listing.total_views,
        counted=counted,
    )


@app.post("/listings/{listing_id}/reaction", response_model=ReactionRead, status_code=201)
def rate_listing(
    listing_id: int,
    payload: ReactionCreate,
    db: Session = Depends(get_db),
):
    listing = db.get(db_models.Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    viewer_key = payload.viewer_key.strip()
    if not viewer_key:
        raise HTTPException(status_code=400, detail="viewer_key is required")

    reaction = (
        db.query(db_models.Reaction)
        .filter(
            db_models.Reaction.listing_id == listing_id,
            db_models.Reaction.viewer_key == viewer_key,
        )
        .first()
    )

    if reaction is None:
        reaction = db_models.Reaction(
            listing_id=listing_id,
            viewer_key=viewer_key,
            rating=payload.rating,
        )
        db.add(reaction)
    else:
        reaction.rating = payload.rating

    db.commit()
    db.refresh(reaction)
    return reaction


@app.post("/features", response_model=FeatureRead, status_code=201)
def create_feature(payload: FeatureCreate, db: Session = Depends(get_db)):
    listing = db.get(db_models.Listing, payload.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    feature = db_models.Feature(
        category=payload.category.strip(),
        title=payload.title.strip(),
        listing_id=payload.listing_id,
    )
    if not feature.category or not feature.title:
        raise HTTPException(status_code=400, detail="Feature category and title are required")

    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature


@app.post("/wishes", status_code=201)
def create_wish(payload: WishCreate, db: Session = Depends(get_db)):
    wish = db_models.Wish(**payload.model_dump())
    db.add(wish)
    db.flush()
    log_action(
        db,
        action="create_wish",
        entity_type="wish",
        entity_id=wish.id,
        description=f"Created wish {wish.title}",
    )
    db.commit()
    return wish


@app.get("/wishes")
def list_wishes(db: Session = Depends(get_db)):
    return db.query(db_models.Wish).order_by(db_models.Wish.created_at.desc()).all()


@app.patch("/wishes/{wish_id}/status")
def update_wish_status(wish_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    wish = db.get(db_models.Wish, wish_id)
    if not wish:
        raise HTTPException(status_code=404, detail="Wish not found")
    wish.status = payload.status
    log_action(
        db,
        action="update_wish_status",
        entity_type="wish",
        entity_id=wish.id,
        description=f"Changed wish status to {wish.status}",
    )
    db.commit()
    db.refresh(wish)
    return wish


@app.post("/offers", status_code=201)
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)):
    listing = db.get(db_models.Listing, payload.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    offer = db_models.Offer(**payload.model_dump())
    db.add(offer)
    db.flush()
    log_action(
        db,
        action="create_offer",
        entity_type="offer",
        entity_id=offer.id,
        description=f"Offer placed on listing {listing.title}",
        actor_id=offer.user_id,
    )
    db.commit()
    return offer


@app.get("/offers")
def list_offers(db: Session = Depends(get_db)):
    return db.query(db_models.Offer).order_by(db_models.Offer.created_at.desc()).all()


@app.patch("/offers/{offer_id}/status")
def update_offer_status(offer_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    offer = db.get(db_models.Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    offer.status = payload.status
    log_action(
        db,
        action="update_offer_status",
        entity_type="offer",
        entity_id=offer.id,
        description=f"Changed offer status to {offer.status}",
        actor_id=offer.user_id,
    )
    db.commit()
    db.refresh(offer)
    return offer


@app.post("/site-visits", status_code=201)
def create_site_visit(payload: SiteVisitCreate, db: Session = Depends(get_db)):
    site_visit = db_models.SiteVisit(**payload.model_dump())
    db.add(site_visit)
    db.flush()
    log_action(
        db,
        action="create_site_visit",
        entity_type="site_visit",
        entity_id=site_visit.id,
        description=f"Site visit booked for listing {site_visit.listing_id}",
    )
    db.commit()
    return site_visit


@app.get("/site-visits")
def list_site_visits(db: Session = Depends(get_db)):
    return db.query(db_models.SiteVisit).order_by(db_models.SiteVisit.created_at.desc()).all()


@app.patch("/site-visits/{site_visit_id}/status")
def update_site_visit_status(
    site_visit_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
):
    site_visit = db.get(db_models.SiteVisit, site_visit_id)
    if not site_visit:
        raise HTTPException(status_code=404, detail="Site visit not found")
    site_visit.status = payload.status
    log_action(
        db,
        action="update_site_visit_status",
        entity_type="site_visit",
        entity_id=site_visit.id,
        description=f"Changed site visit status to {site_visit.status}",
    )
    db.commit()
    db.refresh(site_visit)
    return site_visit


@app.post("/notes", status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    note = db_models.Note(**payload.model_dump())
    db.add(note)
    db.flush()
    log_action(
        db,
        action="create_note",
        entity_type="note",
        entity_id=note.id,
        description="Created a note on an operational record",
        actor_id=note.user_id,
    )
    db.commit()
    return note


@app.get("/notes")
def list_notes(db: Session = Depends(get_db)):
    return db.query(db_models.Note).order_by(db_models.Note.created_at.desc()).all()


@app.get("/dashboard/{role}/{user_id}", response_model=DashboardStats)
def dashboard_stats(role: str, user_id: int, db: Session = Depends(get_db)):
    listings_query = db.query(db_models.Listing)
    if role == "agent":
        listings_query = listings_query.filter(db_models.Listing.owner_id == user_id)

    listings = listings_query.all()
    total_listings = len(listings)
    approved_listings = sum(
        1 for listing in listings if listing.approval_status == "approved"
    )
    rejected_listings = sum(
        1 for listing in listings if listing.approval_status == "rejected"
    )
    total_views = sum(listing.total_views for listing in listings)
    total_sales = sum(listing.total_sales for listing in listings)

    return DashboardStats(
        role=role,
        total_listings=total_listings,
        approved_listings=approved_listings,
        rejected_listings=rejected_listings,
        total_views=total_views,
        total_sales=total_sales,
        pending_agents=db.query(func.count(db_models.User.id))
        .filter(db_models.User.role == "agent", db_models.User.status == "pending")
        .scalar()
        or 0,
        total_agents=db.query(func.count(db_models.User.id))
        .filter(db_models.User.role == "agent")
        .scalar()
        or 0,
        total_wishes=db.query(func.count(db_models.Wish.id)).scalar() or 0,
        total_site_visits=db.query(func.count(db_models.SiteVisit.id)).scalar() or 0,
        total_offers=db.query(func.count(db_models.Offer.id)).scalar() or 0,
    )


@app.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.query(db_models.AuditLog).order_by(db_models.AuditLog.created_at.desc()).all()


@app.get("/content/bonus-info", response_model=list[BonusInfoSection])
def bonus_info():
    return parse_bonus_sections()
