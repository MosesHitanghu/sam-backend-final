from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str | None = None
    email: str
    phone_number: str | None = None
    role: str
    status: str = "active"
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    profile_picture: str | None = None
    address: str | None = None
    district: str | None = None
    village: str | None = None
    experience: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    nationality: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class AgentSignup(BaseModel):
    username: str
    email: str
    phone_number: str | None = None
    password: str = Field(min_length=8)
    first_name: str
    last_name: str


class LoginPayload(BaseModel):
    identifier: str
    password: str


class AvailabilityRead(BaseModel):
    field: str
    value: str
    available: bool
    message: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sales_closed: int
    approval_notes: str | None = None
    is_google_account: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    profile_picture: str | None = None
    phone_number: str | None = None
    address: str | None = None
    district: str | None = None
    village: str | None = None
    experience: str | None = None
    nationality: str | None = None


class ListingSaleCreate(BaseModel):
    sale_price: float = Field(gt=0)
    sold_at: str
    registered_by_id: int | None = None


class ListingSaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    sale_price: float
    sold_at: str
    registered_by_id: int | None = None
    created_at: datetime


class ListingCreate(BaseModel):
    title: str
    description: str
    price: float
    district: str
    city: str | None = None
    address: str | None = None
    owner_id: int
    category: str = "Land"
    size_text: str | None = None
    purpose: str | None = None
    thumbnail_url: str | None = None
    pictures: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    title_transfer_charges: float | None = None
    is_featured: bool = False
    status: str = "available"
    approval_status: str = "approved"


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    district: str | None = None
    city: str | None = None
    address: str | None = None
    category: str | None = None
    size_text: str | None = None
    purpose: str | None = None
    thumbnail_url: str | None = None
    pictures: list[str] | None = None
    latitude: float | None = None
    longitude: float | None = None
    title_transfer_charges: float | None = None
    is_featured: bool | None = None
    status: str | None = None
    approval_status: str | None = None


class FeatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    listing_id: int


class FeatureCreate(BaseModel):
    category: str
    title: str
    listing_id: int


class ListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    price: float
    district: str
    city: str | None
    address: str | None
    status: str
    approval_status: str
    category: str
    size_text: str | None
    purpose: str | None
    thumbnail_url: str | None
    pictures: str | None
    latitude: float | None
    longitude: float | None
    title_transfer_charges: float | None
    is_featured: bool
    total_views: int
    total_sales: int
    owner_id: int
    features: list[FeatureRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ListingViewCreate(BaseModel):
    viewer_key: str


class ListingViewRead(BaseModel):
    listing_id: int
    total_views: int
    counted: bool


class ReactionCreate(BaseModel):
    viewer_key: str
    rating: float = Field(ge=0.5, le=5)


class ReactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    viewer_key: str
    rating: float
    created_at: datetime
    updated_at: datetime


class WishCreate(BaseModel):
    title: str
    description: str
    price_range: str | None = None
    purpose: str | None = None
    district: str | None = None
    village: str | None = None
    size_range: str | None = None
    customer_name: str
    customer_email: str
    customer_mobile_number: str


class OfferCreate(BaseModel):
    listing_id: int
    amount: float
    full_name: str
    mobile_number: str
    email: str
    user_id: int | None = None


class SiteVisitCreate(BaseModel):
    listing_id: int
    customer_name: str
    customer_email: str
    customer_mobile_number: str
    scheduled_date: str
    scheduled_time: str
    message: str | None = None


class StatusUpdate(BaseModel):
    status: str


class NoteCreate(BaseModel):
    content: str
    listing_id: int | None = None
    user_id: int | None = None
    site_visit_id: int | None = None
    offer_id: int | None = None
    wish_id: int | None = None


class HeroSlideCreate(BaseModel):
    title: str
    subtitle: str | None = None
    image_url: str
    is_active: bool = True


class DashboardStats(BaseModel):
    role: str
    total_listings: int
    approved_listings: int
    rejected_listings: int
    total_views: int
    total_sales: int
    pending_agents: int = 0
    total_agents: int = 0
    total_wishes: int = 0
    total_site_visits: int = 0
    total_offers: int = 0


class BonusInfoSection(BaseModel):
    heading: str
    body: str


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: int | None
    description: str
    actor_id: int | None
    created_at: datetime
