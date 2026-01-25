"""
Stripe Connect Payment System for AltX No-Code Platform

This module implements Stripe Connect for handling payments in generated apps.
Each app owner connects their own Stripe account - the platform never holds user money.

Architecture:
- App owners connect Stripe accounts via OAuth (Express or Standard)
- Generated apps call platform backend for payments
- Backend creates checkout sessions on behalf of connected accounts
- Single webhook endpoint routes events to correct apps

This is how Gumroad, Substack, and Shopify apps work internally.
"""

import os
import stripe
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_CONNECT_CLIENT_ID = os.getenv("STRIPE_CONNECT_CLIENT_ID")
PLATFORM_FEE_PERCENT = float(os.getenv("PLATFORM_FEE_PERCENT", "0"))  # Optional platform fee

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    print("✅ Stripe initialized")
else:
    print("⚠️  Stripe not configured - set STRIPE_SECRET_KEY in .env")


# ==================== ENUMS ====================

class StripeAccountStatus(str, Enum):
    """Stripe Connect account verification status"""
    NOT_CONNECTED = "not_connected"
    PENDING = "pending"
    VERIFIED = "verified"
    RESTRICTED = "restricted"
    REJECTED = "rejected"


class PayoutSchedule(str, Enum):
    """Payout frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


# ==================== PYDANTIC MODELS ====================

class StripeConnectInfo(BaseModel):
    """Stripe Connect account information stored per user"""
    stripe_account_id: Optional[str] = None
    status: StripeAccountStatus = StripeAccountStatus.NOT_CONNECTED
    charges_enabled: bool = False
    payouts_enabled: bool = False
    details_submitted: bool = False
    default_currency: Optional[str] = None
    country: Optional[str] = None
    payout_schedule: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session"""
    app_id: str = Field(..., description="The app making the payment request")
    line_items: List[Dict[str, Any]] = Field(..., description="Products/services being purchased")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after cancelled payment")
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    mode: str = Field(default="payment", description="payment, subscription, or setup")


class CreateProductRequest(BaseModel):
    """Request to create a product for the connected account"""
    app_id: str
    name: str
    description: Optional[str] = None
    price_cents: int = Field(..., ge=50, description="Price in cents (min 50)")
    currency: str = Field(default="usd")
    recurring: Optional[Dict[str, str]] = None  # For subscriptions: {"interval": "month"}
    metadata: Optional[Dict[str, str]] = None


class RefundRequest(BaseModel):
    """Request to refund a payment"""
    app_id: str
    payment_intent_id: str
    amount_cents: Optional[int] = None  # Partial refund, or full if None
    reason: Optional[str] = None


class WebhookEvent(BaseModel):
    """Parsed webhook event"""
    event_type: str
    stripe_account_id: str
    data: Dict[str, Any]
    app_id: Optional[str] = None


# ==================== STRIPE CONNECT SERVICE ====================

class StripeConnectService:
    """
    Handles all Stripe Connect operations.
    
    Key principle: Platform NEVER touches money directly.
    All payments flow through connected accounts.
    """
    
    def __init__(self):
        self.is_configured = bool(STRIPE_SECRET_KEY)
    
    def _check_configured(self):
        """Ensure Stripe is configured"""
        if not self.is_configured:
            raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY in .env")
    
    # ==================== ACCOUNT ONBOARDING ====================
    
    def create_connect_account(
        self,
        user_id: str,
        email: str,
        country: str = "US",
        account_type: str = "express"
    ) -> Dict[str, Any]:
        """
        Create a new Stripe Connect account for an app owner.
        
        Express accounts: Stripe handles KYC UI (recommended)
        Standard accounts: Full Stripe dashboard access
        
        Args:
            user_id: Platform user ID
            email: User's email
            country: Two-letter country code
            account_type: "express" or "standard"
        
        Returns:
            Account ID and onboarding URL
        """
        self._check_configured()
        
        try:
            # Create the connected account
            account = stripe.Account.create(
                type=account_type,
                country=country,
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={
                    "platform_user_id": user_id,
                    "platform": "altx"
                }
            )
            
            return {
                "success": True,
                "account_id": account.id,
                "account_type": account_type
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_account_link(
        self,
        account_id: str,
        refresh_url: str,
        return_url: str,
        link_type: str = "account_onboarding"
    ) -> Dict[str, Any]:
        """
        Create an account link for onboarding or updating.
        
        This generates a URL where the user completes KYC on Stripe's UI.
        The platform never sees sensitive verification data.
        
        Args:
            account_id: Stripe Connect account ID
            refresh_url: URL if the link expires
            return_url: URL after completion
            link_type: "account_onboarding" or "account_update"
        
        Returns:
            Onboarding URL (expires in ~15 minutes)
        """
        self._check_configured()
        
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type=link_type,
            )
            
            return {
                "success": True,
                "url": account_link.url,
                "expires_at": account_link.expires_at
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get the current status of a connected account.
        
        Returns verification status, payout settings, etc.
        """
        self._check_configured()
        
        try:
            account = stripe.Account.retrieve(account_id)
            
            # Determine overall status
            if account.details_submitted and account.charges_enabled:
                status = StripeAccountStatus.VERIFIED
            elif account.requirements.disabled_reason:
                status = StripeAccountStatus.REJECTED
            elif account.requirements.currently_due:
                status = StripeAccountStatus.PENDING
            else:
                status = StripeAccountStatus.RESTRICTED
            
            return {
                "success": True,
                "account_id": account.id,
                "status": status.value,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
                "default_currency": account.default_currency,
                "country": account.country,
                "requirements": {
                    "currently_due": account.requirements.currently_due,
                    "eventually_due": account.requirements.eventually_due,
                    "disabled_reason": account.requirements.disabled_reason
                },
                "settings": {
                    "payout_schedule": account.settings.payouts.schedule if account.settings else None
                }
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_login_link(self, account_id: str) -> Dict[str, Any]:
        """
        Create a login link to the Express dashboard.
        
        Only works for Express accounts. Standard accounts use
        the regular Stripe dashboard.
        """
        self._check_configured()
        
        try:
            login_link = stripe.Account.create_login_link(account_id)
            return {
                "success": True,
                "url": login_link.url
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== PAYMENTS ====================
    
    def create_checkout_session(
        self,
        connected_account_id: str,
        line_items: List[Dict[str, Any]],
        success_url: str,
        cancel_url: str,
        mode: str = "payment",
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        application_fee_percent: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a Checkout Session on behalf of a connected account.
        
        THIS IS THE KEY FUNCTION.
        The stripeAccount parameter makes the payment go to the app owner.
        
        Args:
            connected_account_id: The app owner's Stripe account
            line_items: Products being purchased
            success_url: Redirect URL after success
            cancel_url: Redirect URL after cancel
            mode: "payment", "subscription", or "setup"
            customer_email: Pre-fill customer email
            metadata: Custom data (e.g., order_id, user_id)
            application_fee_percent: Optional platform fee (0-100)
        
        Returns:
            Checkout session URL and ID
        """
        self._check_configured()
        
        try:
            session_params = {
                "mode": mode,
                "line_items": line_items,
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
            
            if customer_email:
                session_params["customer_email"] = customer_email
            
            if metadata:
                session_params["metadata"] = metadata
            
            # Add platform fee if configured
            fee_percent = application_fee_percent or PLATFORM_FEE_PERCENT
            if fee_percent > 0 and mode == "payment":
                # Calculate fee as percentage of total
                session_params["payment_intent_data"] = {
                    "application_fee_amount": None,  # Will be set per-item
                }
            
            # THE MAGIC LINE - creates session on connected account
            session = stripe.checkout.Session.create(
                **session_params,
                stripe_account=connected_account_id  # This routes payment to app owner
            )
            
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url,
                "expires_at": session.expires_at
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_payment_intent(
        self,
        connected_account_id: str,
        amount_cents: int,
        currency: str = "usd",
        metadata: Optional[Dict[str, str]] = None,
        application_fee_cents: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a Payment Intent for custom payment flows.
        
        Use this if you need more control than Checkout Sessions.
        """
        self._check_configured()
        
        try:
            intent_params = {
                "amount": amount_cents,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
            }
            
            if metadata:
                intent_params["metadata"] = metadata
            
            if application_fee_cents:
                intent_params["application_fee_amount"] = application_fee_cents
            
            intent = stripe.PaymentIntent.create(
                **intent_params,
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_refund(
        self,
        connected_account_id: str,
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment.
        
        Refunds go through the connected account's Stripe.
        """
        self._check_configured()
        
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
            }
            
            if amount_cents:
                refund_params["amount"] = amount_cents
            
            if reason:
                refund_params["reason"] = reason
            
            refund = stripe.Refund.create(
                **refund_params,
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount,
                "status": refund.status
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== PRODUCTS & PRICES ====================
    
    def create_product(
        self,
        connected_account_id: str,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a product on the connected account.
        """
        self._check_configured()
        
        try:
            product_params = {
                "name": name,
            }
            
            if description:
                product_params["description"] = description
            
            if metadata:
                product_params["metadata"] = metadata
            
            product = stripe.Product.create(
                **product_params,
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "product_id": product.id,
                "name": product.name
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_price(
        self,
        connected_account_id: str,
        product_id: str,
        unit_amount_cents: int,
        currency: str = "usd",
        recurring: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a price for a product.
        
        Args:
            recurring: {"interval": "month"} for subscriptions
        """
        self._check_configured()
        
        try:
            price_params = {
                "product": product_id,
                "unit_amount": unit_amount_cents,
                "currency": currency,
            }
            
            if recurring:
                price_params["recurring"] = recurring
            
            price = stripe.Price.create(
                **price_params,
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "price_id": price.id,
                "unit_amount": price.unit_amount,
                "currency": price.currency,
                "recurring": price.recurring
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== SUBSCRIPTIONS ====================
    
    def create_subscription_checkout(
        self,
        connected_account_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription checkout session.
        
        Subscriptions belong to the connected account.
        Customer invoices come from the app owner.
        Platform stays invisible.
        """
        self._check_configured()
        
        try:
            session_params = {
                "mode": "subscription",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
            
            if customer_email:
                session_params["customer_email"] = customer_email
            
            if metadata:
                session_params["metadata"] = metadata
            
            if trial_days:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_days
                }
            
            session = stripe.checkout.Session.create(
                **session_params,
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_subscription(
        self,
        connected_account_id: str,
        subscription_id: str,
        immediately: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.
        """
        self._check_configured()
        
        try:
            if immediately:
                subscription = stripe.Subscription.delete(
                    subscription_id,
                    stripe_account=connected_account_id
                )
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                    stripe_account=connected_account_id
                )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== WEBHOOKS ====================
    
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify and parse a webhook from Stripe.
        
        All webhook events hit a single endpoint.
        The event contains the connected account ID for routing.
        """
        self._check_configured()
        
        secret = webhook_secret or STRIPE_WEBHOOK_SECRET
        if not secret:
            return {
                "success": False,
                "error": "Webhook secret not configured"
            }
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, secret
            )
            
            # Extract connected account from event
            # This is how we route to the correct app
            connected_account_id = event.get("account")
            
            return {
                "success": True,
                "event_id": event.id,
                "event_type": event.type,
                "account": connected_account_id,
                "data": event.data.object,
                "created": event.created
            }
            
        except stripe.error.SignatureVerificationError as e:
            return {
                "success": False,
                "error": f"Invalid signature: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_webhook_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        connected_account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a webhook event and return relevant info.
        
        Common events:
        - checkout.session.completed: Payment successful
        - payment_intent.succeeded: Direct payment successful
        - customer.subscription.created: New subscription
        - customer.subscription.deleted: Subscription cancelled
        - invoice.paid: Recurring payment successful
        - invoice.payment_failed: Recurring payment failed
        - account.updated: Connected account status changed
        """
        
        result = {
            "event_type": event_type,
            "connected_account": connected_account_id,
            "action_required": False,
            "notification": None
        }
        
        # Handle different event types
        if event_type == "checkout.session.completed":
            result["payment_status"] = "completed"
            result["customer_email"] = data.get("customer_email")
            result["amount_total"] = data.get("amount_total")
            result["metadata"] = data.get("metadata", {})
            result["notification"] = "Payment received!"
            
        elif event_type == "payment_intent.succeeded":
            result["payment_status"] = "succeeded"
            result["amount"] = data.get("amount")
            result["currency"] = data.get("currency")
            
        elif event_type == "payment_intent.payment_failed":
            result["payment_status"] = "failed"
            result["action_required"] = True
            result["error"] = data.get("last_payment_error", {}).get("message")
            result["notification"] = "Payment failed"
            
        elif event_type == "customer.subscription.created":
            result["subscription_status"] = "active"
            result["subscription_id"] = data.get("id")
            result["notification"] = "New subscription started!"
            
        elif event_type == "customer.subscription.deleted":
            result["subscription_status"] = "cancelled"
            result["subscription_id"] = data.get("id")
            result["notification"] = "Subscription cancelled"
            
        elif event_type == "invoice.paid":
            result["invoice_status"] = "paid"
            result["amount_paid"] = data.get("amount_paid")
            
        elif event_type == "invoice.payment_failed":
            result["invoice_status"] = "failed"
            result["action_required"] = True
            result["notification"] = "Invoice payment failed"
            
        elif event_type == "account.updated":
            # Connected account status changed
            result["account_status"] = {
                "charges_enabled": data.get("charges_enabled"),
                "payouts_enabled": data.get("payouts_enabled"),
                "details_submitted": data.get("details_submitted")
            }
            
        return result
    
    # ==================== REPORTING ====================
    
    def get_balance(self, connected_account_id: str) -> Dict[str, Any]:
        """
        Get the balance for a connected account.
        """
        self._check_configured()
        
        try:
            balance = stripe.Balance.retrieve(
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "available": [
                    {"amount": b.amount, "currency": b.currency}
                    for b in balance.available
                ],
                "pending": [
                    {"amount": b.amount, "currency": b.currency}
                    for b in balance.pending
                ]
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_transactions(
        self,
        connected_account_id: str,
        limit: int = 10,
        starting_after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List recent transactions for a connected account.
        """
        self._check_configured()
        
        try:
            params = {"limit": limit}
            if starting_after:
                params["starting_after"] = starting_after
            
            charges = stripe.Charge.list(
                **params,
                stripe_account=connected_account_id
            )
            
            return {
                "success": True,
                "transactions": [
                    {
                        "id": c.id,
                        "amount": c.amount,
                        "currency": c.currency,
                        "status": c.status,
                        "created": c.created,
                        "customer_email": c.receipt_email,
                        "description": c.description
                    }
                    for c in charges.data
                ],
                "has_more": charges.has_more
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }


# ==================== SINGLETON INSTANCE ====================

stripe_connect_service = StripeConnectService()


# ==================== HELPER FUNCTIONS ====================

def format_line_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format line items for Stripe Checkout.
    
    Input format (from generated apps):
    [
        {"name": "Product", "price": 9.99, "quantity": 1},
        ...
    ]
    
    Output format (Stripe):
    [
        {
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Product"},
                "unit_amount": 999
            },
            "quantity": 1
        },
        ...
    ]
    """
    formatted = []
    
    for item in items:
        formatted.append({
            "price_data": {
                "currency": item.get("currency", "usd"),
                "product_data": {
                    "name": item.get("name", "Product"),
                    "description": item.get("description"),
                },
                "unit_amount": int(item.get("price", 0) * 100),  # Convert to cents
            },
            "quantity": item.get("quantity", 1)
        })
    
    return formatted
