# Website Analyzer - "Build a Website Like X" Feature

## Overview

This feature allows users to request websites similar to popular sites like Amazon, Netflix, Spotify, etc. When a user says something like "build a website like Amazon", the system will:

1. **Detect the website reference** from the user's prompt
2. **Scrape the actual website** to extract design patterns
3. **Analyze the design** including colors, layout, typography, components
4. **Generate a similar but unique design** inspired by the original

## How It Works

### 1. Website Detection

The system uses pattern matching to detect website references in prompts:

```
"build a website like Amazon" → amazon → https://www.amazon.com
"create something similar to Spotify" → spotify → https://www.spotify.com
"make a clone of https://example.com" → example.com → https://example.com
```

### 2. Website Analysis

The analyzer extracts:

- **Layout Type**: sidebar-layout, grid-layout, landing-page-layout, ecommerce-layout
- **Grid System**: tailwind-grid, bootstrap-12-column, flexbox-grid, css-grid
- **Page Structure**: header, navigation, hero-section, main-content, footer
- **Color Palette**: Primary colors, accent colors, background style (light/dark/gradient)
- **Typography**: Font families, heading styles, body text styles
- **Navigation**: Horizontal, sidebar, fixed, has-search, has-cart, has-user-menu
- **Components**: Cards, buttons, modals, carousels, accordions, tabs, etc.
- **Hero Section**: Has image/video, CTA buttons, style (full-screen, split-layout)
- **Product Cards**: Layout, has-price, has-rating, has-add-to-cart
- **Features**: Search, shopping-cart, authentication, wishlist, reviews, filters
- **CSS Techniques**: Flexbox, CSS Grid, glassmorphism, gradients, animations
- **Animations**: Fade-in, slide-in, scale, hover-effects, scroll-animations

### 3. Screenshot Capture (Optional)

The system can capture screenshots using:
- **Playwright** (preferred - best quality)
- **Selenium** (fallback)
- **External Screenshot API** (last resort)

### 4. Similar But Different

The AI uses the analysis to create a design that:
- ✅ Captures the essence and functionality of the original
- ✅ Uses similar layout patterns and navigation
- ✅ Implements comparable features
- ❌ Does NOT copy exact colors, fonts, or branding
- ❌ Does NOT replicate copyrighted content
- ✅ Adds unique creative interpretations

## Supported Popular Sites

### E-Commerce
- Amazon, eBay, Shopify, Etsy, Walmart, Target, Alibaba, AliExpress

### Social Media
- Twitter/X, Facebook, Instagram, LinkedIn, Pinterest, Reddit, TikTok

### Tech/SaaS
- GitHub, GitLab, Notion, Slack, Discord, Trello, Asana, Figma, Canva

### Streaming/Media
- Netflix, Spotify, YouTube, Twitch, Hulu, Disney+

### Travel
- Airbnb, Booking.com, Expedia, TripAdvisor

### Food/Delivery
- DoorDash, UberEats, Grubhub, Instacart

### Finance
- Stripe, PayPal, Robinhood, Coinbase

### News/Content
- Medium, Substack, WordPress

### Productivity
- Dropbox, Zoom, Calendly

## API Endpoints

### GET /api/website-analyzer/popular-sites
Returns list of all popular sites that can be used as inspiration.

```json
{
  "available": true,
  "sites": {
    "amazon": "https://www.amazon.com",
    "spotify": "https://www.spotify.com",
    ...
  },
  "categories": {
    "ecommerce": ["amazon", "ebay", "shopify"],
    "social": ["twitter", "facebook", "instagram"],
    ...
  }
}
```

### POST /api/website-analyzer/analyze
Analyze a specific website.

**Request:**
```json
{
  "url": "https://www.amazon.com",
  "site_name": "Amazon",
  "take_screenshot": false
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "website_name": "Amazon",
    "layout_type": "ecommerce-layout",
    "primary_colors": ["#ff9900", "#232f3e", "#ffffff"],
    "navigation_type": "horizontal",
    "has_search": true,
    "has_cart": true,
    "components": [
      {"name": "card", "count": 25},
      {"name": "button", "count": 50}
    ],
    "design_suggestions": {
      "color_theme": "Consider a dark mode variant...",
      "layout": "Try a Pinterest-style infinite scroll...",
      "differentiation": "Create unique hero section with 3D elements..."
    }
  }
}
```

### POST /api/website-analyzer/extract-reference
Extract website reference from a user prompt.

**Request:**
```json
{
  "prompt": "build a website like amazon for selling electronics"
}
```

**Response:**
```json
{
  "found": true,
  "site_name": "amazon",
  "url": "https://www.amazon.com",
  "message": "Detected reference to amazon - will analyze for design inspiration"
}
```

### GET /api/website-analyzer/screenshot/{site_name}
Get a screenshot of a popular website.

```json
{
  "success": true,
  "site_name": "amazon",
  "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgA...",
  "content_type": "image/png"
}
```

## Integration with Project Generation

When creating a project, the system automatically:

1. Checks if the idea contains a website reference
2. If found, analyzes the referenced website
3. Adds the analysis context to the AI prompt
4. Generates a project inspired by (but not copying) the original

### Example Flow

```python
# User Input
"Create an e-commerce website like Amazon for selling handmade crafts"

# System Actions
1. Detects "Amazon" reference
2. Scrapes amazon.com
3. Extracts: ecommerce-layout, search bar, shopping cart, product cards, etc.
4. AI generates: Similar functionality but with:
   - Different color scheme (artisanal/warm tones)
   - Unique "Handmade" branding
   - Craft-specific categories
   - Artisan profiles
   - Custom product cards with maker info
```

## Design Variation Suggestions

The analyzer provides suggestions to make the design unique:

| Aspect | Original | Suggestion |
|--------|----------|------------|
| Colors | Amazon's orange/dark | Warm earth tones for handmade feel |
| Layout | Standard ecommerce | Pinterest-style masonry grid |
| Navigation | Mega-menu | Clean minimal nav with search focus |
| Components | Standard cards | Cards with artisan photos |
| Features | Reviews | Maker stories + reviews |

## Files

- `website_analyzer.py` - Main analyzer module
- `design_trend_scraper.py` - Integration with design trends
- `pure_ai_generator.py` - Uses analysis in project generation
- `main.py` - API endpoints

## Dependencies

Required:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

Optional (for screenshots):
- `playwright` - Browser automation (preferred)
- `selenium` - Browser automation (fallback)
