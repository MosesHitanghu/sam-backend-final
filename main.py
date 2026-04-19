from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

import db_models
from database import get_db
from models import (
    AgentSignup,
    AuditLogRead,
    BonusInfoSection,
    DashboardStats,
    HeroSlideCreate,
    ListingCreate,
    ListingRead,
    ListingViewCreate,
    ListingViewRead,
    LoginPayload,
    NoteCreate,
    OfferCreate,
    SiteVisitCreate,
    UserCreate,
    UserRead,
    WishCreate,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BONUS_INFO_PATH = PROJECT_ROOT / "docs" / "bonus_info.md"

app = FastAPI(title="SAM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    db.execute(text("SELECT 1"))
    return {"message": "Database connected successfully"}


@app.post("/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = (
        db.query(db_models.User)
        .filter(
            or_(
                db_models.User.email == payload.identifier,
                db_models.User.phone_number == payload.identifier,
            )
        )
        .first()
    )
    if not user or user.password != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role == "agent" and user.status not in {"approved", "active"}:
        raise HTTPException(status_code=403, detail="Agent account is pending approval")

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


@app.post("/auth/agents/signup", response_model=UserRead, status_code=201)
def signup_agent(payload: AgentSignup, db: Session = Depends(get_db)):
    existing_user = (
        db.query(db_models.User)
        .filter(
            or_(
                db_models.User.email == payload.email,
                db_models.User.phone_number == payload.phone_number,
            )
        )
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    user = db_models.User(
        email=payload.email,
        phone_number=payload.phone_number,
        password=payload.password,
        role="agent",
        status="pending",
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=f"{payload.first_name} {payload.last_name}",
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
