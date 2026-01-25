# Stripe Connect Integration Guide

## How Payments Work in AltX

AltX uses **Stripe Connect** to enable payments in generated apps. This is the same architecture used by Gumroad, Substack, and Shopify apps.

### Key Principles

1. **App owners connect their own Stripe accounts** - The platform never holds money
2. **Generated apps never see Stripe keys** - All payments go through the platform backend
3. **Single webhook endpoint** - Routes events to the correct apps
4. **Stripe handles compliance** - KYC, tax, payouts, refunds

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        End User (Customer)                       │
│                    Clicks "Pay" in generated app                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Generated App (Frontend)                   │
│                    POST /api/payments/checkout                   │
│                    Headers: { app_id: "my-app" }                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AltX Platform Backend                       │
│  1. Looks up app_id → finds owner                               │
│  2. Gets owner's stripe_account_id                              │
│  3. Creates checkout session ON BEHALF of owner                 │
│     stripe.checkout.sessions.create(                            │
│       { ... },                                                  │
│       { stripeAccount: "acct_xxx" }  ← THE MAGIC LINE          │
│     )                                                           │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Stripe Checkout UI                         │
│              Customer completes payment on Stripe                │
│           Money goes DIRECTLY to app owner's account            │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Stripe Webhook                             │
│                 POST /webhooks/stripe                            │
│   Event contains: { account: "acct_xxx" }                       │
│   Platform routes to correct app owner                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Stripe Dashboard Setup

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Create a new account or use existing
3. Navigate to **Connect** → **Settings**
4. Enable **OAuth for Standard accounts** or **Express accounts**
5. Copy your:
   - `STRIPE_SECRET_KEY` (sk_test_... or sk_live_...)
   - `STRIPE_PUBLISHABLE_KEY` (pk_test_... or pk_live_...)
   - `STRIPE_CONNECT_CLIENT_ID` (ca_...)

### 2. Environment Variables

Add to your `.env` file:

```env
# Stripe Connect Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_CONNECT_CLIENT_ID=ca_your_client_id

# Optional: Platform fee (0-100%)
PLATFORM_FEE_PERCENT=0

# Frontend URL for redirects
FRONTEND_URL=http://localhost:3000
```

### 3. Webhook Setup

1. Go to **Developers** → **Webhooks**
2. Add endpoint: `https://your-domain.com/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `account.updated`
4. Copy the signing secret to `STRIPE_WEBHOOK_SECRET`

---

## API Endpoints

### Connect Stripe Account

```http
POST /api/payments/connect
Authorization: Bearer <token>

{
  "country": "US",
  "account_type": "express"
}
```

Response:
```json
{
  "success": true,
  "account_id": "acct_xxx",
  "message": "Stripe account created. Complete onboarding to start accepting payments."
}
```

### Get Onboarding Link

```http
GET /api/payments/onboarding-link
Authorization: Bearer <token>
```

Response:
```json
{
  "success": true,
  "url": "https://connect.stripe.com/setup/...",
  "expires_at": 1234567890
}
```

### Check Status

```http
GET /api/payments/status
Authorization: Bearer <token>
```

Response:
```json
{
  "success": true,
  "connected": true,
  "status": "verified",
  "charges_enabled": true,
  "payouts_enabled": true,
  "currency": "usd",
  "country": "US"
}
```

### Create Checkout (for generated apps)

```http
POST /api/payments/checkout
Headers:
  x-app-id: my-app-slug

{
  "line_items": [
    {"name": "Product", "price": 29.99, "quantity": 1}
  ],
  "success_url": "https://my-app.com/success",
  "cancel_url": "https://my-app.com/cancel",
  "customer_email": "customer@example.com"
}
```

Response:
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_xxx"
}
```

### Get Dashboard Link

```http
GET /api/payments/dashboard-link
Authorization: Bearer <token>
```

### Get Balance

```http
GET /api/payments/balance
Authorization: Bearer <token>
```

### Get Transactions

```http
GET /api/payments/transactions?limit=10
Authorization: Bearer <token>
```

### Create Refund

```http
POST /api/payments/refund
Authorization: Bearer <token>

{
  "app_id": "my-app",
  "payment_intent_id": "pi_xxx",
  "amount_cents": 1000,
  "reason": "requested_by_customer"
}
```

---

## Frontend Integration

### Settings Page UI

```jsx
// Payments Settings Component
const PaymentSettings = () => {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    fetchPaymentStatus();
  }, []);
  
  const fetchPaymentStatus = async () => {
    const res = await fetch('/api/payments/status', {
      headers: { Authorization: `Bearer ${token}` }
    });
    setStatus(await res.json());
  };
  
  const connectStripe = async () => {
    // Create account
    await fetch('/api/payments/connect', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ country: 'US' })
    });
    
    // Get onboarding link
    const res = await fetch('/api/payments/onboarding-link', {
      headers: { Authorization: `Bearer ${token}` }
    });
    const { url } = await res.json();
    
    // Redirect to Stripe
    window.location.href = url;
  };
  
  return (
    <div className="payment-settings">
      <h2>💳 Payments</h2>
      
      {!status?.connected ? (
        <button onClick={connectStripe}>
          Connect Stripe
        </button>
      ) : (
        <div className="status-card">
          <p>Status: {status.status === 'verified' ? '✅ Verified' : '⏳ Pending'}</p>
          <p>Currency: {status.currency?.toUpperCase()}</p>
          <p>Payouts: {status.payouts_enabled ? 'Enabled' : 'Disabled'}</p>
        </div>
      )}
    </div>
  );
};
```

### Generated App Checkout

```jsx
// In generated e-commerce app
const handleCheckout = async (cart) => {
  const response = await fetch('/api/payments/checkout', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-app-id': APP_ID  // Set during generation
    },
    body: JSON.stringify({
      line_items: cart.map(item => ({
        name: item.name,
        price: item.price,
        quantity: item.quantity
      })),
      success_url: `${window.location.origin}/order-success`,
      cancel_url: `${window.location.origin}/cart`
    })
  });
  
  const { checkout_url } = await response.json();
  window.location.href = checkout_url;
};
```

---

## What You Avoid

| ❌ Problem | ✅ Solution |
|-----------|-------------|
| Becoming a payment processor | Stripe handles everything |
| Holding user money | Direct charges to connected accounts |
| PCI compliance nightmares | Stripe is PCI compliant |
| KYC/AML requirements | Stripe handles verification |
| Tax complexity | Connected accounts handle their taxes |

---

## Revenue Options (Optional)

### Platform Fee

Set `PLATFORM_FEE_PERCENT` in `.env`:

```env
PLATFORM_FEE_PERCENT=5  # Take 5% of each transaction
```

### SaaS Subscription

Charge app owners monthly for the platform itself (separate from this system).

### Usage-Based

Track API calls, storage, bandwidth and bill accordingly.

---

## Common Mistakes to Avoid

1. ❌ **Creating Stripe accounts per end-customer** - Only app owners get accounts
2. ❌ **Letting apps use Stripe SDK directly** - All calls go through backend
3. ❌ **Mixing platform money + user money** - Use `stripeAccount` parameter
4. ❌ **Storing Stripe secrets in generated code** - Never expose keys
5. ❌ **Processing webhooks without signature verification** - Always verify

---

## Testing

### Test Mode

Use test keys (`sk_test_...`) for development. Stripe provides test card numbers:

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Requires authentication: `4000 0025 0000 3155`

### Webhook Testing

Use Stripe CLI for local testing:

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

---

## Support

- [Stripe Connect Docs](https://stripe.com/docs/connect)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Stripe Connect Account Types](https://stripe.com/docs/connect/accounts)
