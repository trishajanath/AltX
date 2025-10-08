from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# ===================================================================
# User Models
# ===================================================================

class UserBase(BaseModel):
    """Shared user attributes."""
    phone_number: str = Field(
        ...,
        description="User's phone number in international format.",
        examples=["+14155552671"]
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name.",
        examples=["John Doe"]
    )

class UserCreate(UserBase):
    """Properties to receive via API on user creation."""
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (will be hashed)."
    )

class UserUpdate(BaseModel):
    """Properties to receive via API on user update."""
    phone_number: str | None = Field(
        None,
        description="User's phone number in international format.",
        examples=["+14155552671"]
    )
    full_name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="User's full name.",
        examples=["Jane Doe"]
    )
    password: str | None = Field(
        None,
        min_length=8,
        description="User's new password (will be hashed)."
    )

class UserResponse(UserBase):
    """Properties to return to client."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# ===================================================================
# Address Models
# ===================================================================

class AddressBase(BaseModel):
    """Shared address attributes."""
    user_id: UUID = Field(..., description="The ID of the user this address belongs to.")
    street: str = Field(..., max_length=255, examples=["123 Main St"])
    city: str = Field(..., max_length=100, examples=["San Francisco"])
    postal_code: str = Field(..., max_length=20, examples=["94105"])
    is_default: bool = Field(False, description="Whether this is the user's default address.")
    latitude: float = Field(..., ge=-90, le=90, examples=[37.7749])
    longitude: float = Field(..., ge=-180, le=180, examples=[-122.4194])

class AddressCreate(AddressBase):
    """Properties to receive via API on address creation."""
    pass

class AddressUpdate(BaseModel):
    """Properties to receive via API on address update."""
    street: str | None = Field(None, max_length=255, examples=["456 Market St"])
    city: str | None = Field(None, max_length=100, examples=["Oakland"])
    postal_code: str | None = Field(None, max_length=20, examples=["94607"])
    is_default: bool | None = Field(None, description="Whether this is the user's default address.")
    latitude: float | None = Field(None, ge=-90, le=90, examples=[37.8044])
    longitude: float | None = Field(None, ge=-180, le=180, examples=[-122.2712])

class AddressResponse(AddressBase):
    """Properties to return to client."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID


# ===================================================================
# Product Models
# ===================================================================

class ProductBase(BaseModel):
    """Shared product attributes."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Organic Bananas"])
    description: str = Field(..., examples=["A bunch of fresh, organic bananas."])
    image_url: str = Field(..., max_length=2048, examples=["https://example.com/images/bananas.jpg"])
    price: float = Field(..., gt=0, description="Price of the product in USD.", examples=[1.99])
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity.", examples=[150])
    category: str = Field(..., max_length=100, examples=["Fruits"])
    fulfillment_center_id: UUID = Field(..., description="The ID of the fulfillment center stocking this product.")

class ProductCreate(ProductBase):
    """Properties to receive via API on product creation."""
    pass

class ProductUpdate(BaseModel):
    """Properties to receive via API on product update."""
    name: str | None = Field(None, min_length=1, max_length=255, examples=["Organic Apples"])
    description: str | None = Field(None, examples=["A bag of fresh, organic apples."])
    image_url: str | None = Field(None, max_length=2048, examples=["https://example.com/images/apples.jpg"])
    price: float | None = Field(None, gt=0, description="Price of the product in USD.", examples=[2.49])
    stock_quantity: int | None = Field(None, ge=0, description="Available stock quantity.", examples=[200])
    category: str | None = Field(None, max_length=100, examples=["Fruits"])
    fulfillment_center_id: UUID | None = Field(None, description="The ID of the fulfillment center stocking this product.")

class ProductResponse(ProductBase):
    """Properties to return to client."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID