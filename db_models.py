from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    experience: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sales_closed: Mapped[int] = mapped_column(Integer, default=0)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(40), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_google_account: Mapped[bool] = mapped_column(Boolean, default=False)

    listings: Mapped[list["Listing"]] = relationship(back_populates="owner")
    offers: Mapped[list["Offer"]] = relationship(back_populates="user")
    notes: Mapped[list["Note"]] = relationship(back_populates="user")
    logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")


class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    district: Mapped[str] = mapped_column(String(120), index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="available", index=True)
    approval_status: Mapped[str] = mapped_column(String(30), default="approved", index=True)
    category: Mapped[str] = mapped_column(String(120), default="Land")
    size_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(120), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pictures: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    title_transfer_charges: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    owner: Mapped["User"] = relationship(back_populates="listings")
    comments: Mapped[list["Comment"]] = relationship(back_populates="listing")
    features: Mapped[list["Feature"]] = relationship(back_populates="listing")
    offers: Mapped[list["Offer"]] = relationship(back_populates="listing")
    site_visits: Mapped[list["SiteVisit"]] = relationship(back_populates="listing")
    notes: Mapped[list["Note"]] = relationship(back_populates="listing")
    views: Mapped[list["ListingView"]] = relationship(back_populates="listing")


class ListingView(Base):
    __tablename__ = "listing_views"
    __table_args__ = (UniqueConstraint("listing_id", "viewer_key", name="uq_listing_view_listing_viewer"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    viewer_key: Mapped[str] = mapped_column(String(255), index=True)
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    listing: Mapped["Listing"] = relationship(back_populates="views")


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)

    listing: Mapped["Listing"] = relationship(back_populates="comments")


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)

    listing: Mapped["Listing"] = relationship(back_populates="features")


class Offer(Base, TimestampMixin):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float)
    full_name: Mapped[str] = mapped_column(String(255))
    mobile_number: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="offers")
    user: Mapped["User"] = relationship(back_populates="offers")
    notes: Mapped[list["Note"]] = relationship(back_populates="offer")


class Wish(Base, TimestampMixin):
    __tablename__ = "wishes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    price_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    customer_mobile_number: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="pending")

    notes: Mapped[list["Note"]] = relationship(back_populates="wish")


class SiteVisit(Base, TimestampMixin):
    __tablename__ = "site_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    customer_mobile_number: Mapped[str] = mapped_column(String(30))
    scheduled_date: Mapped[str] = mapped_column(String(40))
    scheduled_time: Mapped[str] = mapped_column(String(40))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")

    listing: Mapped["Listing"] = relationship(back_populates="site_visits")
    notes: Mapped[list["Note"]] = relationship(back_populates="site_visit")


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listings.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    site_visit_id: Mapped[int | None] = mapped_column(ForeignKey("site_visits.id"), nullable=True)
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id"), nullable=True)
    wish_id: Mapped[int | None] = mapped_column(ForeignKey("wishes.id"), nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="notes")
    user: Mapped["User"] = relationship(back_populates="notes")
    site_visit: Mapped["SiteVisit"] = relationship(back_populates="notes")
    offer: Mapped["Offer"] = relationship(back_populates="notes")
    wish: Mapped["Wish"] = relationship(back_populates="notes")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    actor: Mapped["User"] = relationship(back_populates="logs")


class HeroSlide(Base, TimestampMixin):
    __tablename__ = "hero_slides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
