"""
Website Analyzer - Scrape and analyze real websites to inspire generated designs

When user says "build a website like Amazon", this module:
1. Finds and scrapes Amazon's actual website
2. Takes a screenshot (if possible)
3. Extracts design patterns, colors, layout, components
4. Creates a similar but unique design inspiration
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import base64
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from urllib.parse import urljoin, urlparse, quote
import os

# Try to import screenshot capabilities
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


@dataclass
class WebsiteAnalysis:
    """Complete analysis of a scraped website"""
    website_name: str
    website_url: str
    screenshot_base64: Optional[str] = None
    screenshot_url: Optional[str] = None
    
    # Layout & Structure
    layout_type: str = ""
    grid_system: str = ""
    page_structure: List[str] = field(default_factory=list)
    
    # Visual Design
    color_palette: List[str] = field(default_factory=list)
    primary_colors: List[str] = field(default_factory=list)
    accent_colors: List[str] = field(default_factory=list)
    background_style: str = ""
    
    # Typography
    font_families: List[str] = field(default_factory=list)
    heading_style: str = ""
    body_text_style: str = ""
    
    # Navigation
    navigation_type: str = ""
    navigation_items: List[str] = field(default_factory=list)
    has_search: bool = False
    has_cart: bool = False
    has_user_menu: bool = False
    
    # Components Found
    components: List[Dict[str, Any]] = field(default_factory=list)
    hero_section: Optional[Dict[str, Any]] = None
    product_cards: Optional[Dict[str, Any]] = None
    footer_structure: Optional[Dict[str, Any]] = None
    
    # Features Detected
    features: List[str] = field(default_factory=list)
    interactive_elements: List[str] = field(default_factory=list)
    
    # CSS Techniques
    css_techniques: List[str] = field(default_factory=list)
    animation_styles: List[str] = field(default_factory=list)
    
    # Similar-but-different suggestions
    design_suggestions: Dict[str, str] = field(default_factory=dict)
    
    # Analysis metadata
    analyzed_at: str = ""
    analysis_quality: str = "basic"  # basic, detailed, with_screenshot


# Common website URL mappings for popular sites
POPULAR_SITES = {
    # E-commerce
    "amazon": "https://www.amazon.com",
    "ebay": "https://www.ebay.com",
    "shopify": "https://www.shopify.com",
    "etsy": "https://www.etsy.com",
    "walmart": "https://www.walmart.com",
    "target": "https://www.target.com",
    "alibaba": "https://www.alibaba.com",
    "aliexpress": "https://www.aliexpress.com",
    
    # Social Media
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "pinterest": "https://www.pinterest.com",
    "reddit": "https://www.reddit.com",
    "tiktok": "https://www.tiktok.com",
    
    # Tech/SaaS
    "google": "https://www.google.com",
    "github": "https://github.com",
    "gitlab": "https://gitlab.com",
    "notion": "https://www.notion.so",
    "slack": "https://slack.com",
    "discord": "https://discord.com",
    "trello": "https://trello.com",
    "asana": "https://asana.com",
    "figma": "https://www.figma.com",
    "canva": "https://www.canva.com",
    
    # Streaming/Media
    "netflix": "https://www.netflix.com",
    "spotify": "https://www.spotify.com",
    "youtube": "https://www.youtube.com",
    "twitch": "https://www.twitch.tv",
    "hulu": "https://www.hulu.com",
    "disney": "https://www.disneyplus.com",
    
    # Travel
    "airbnb": "https://www.airbnb.com",
    "booking": "https://www.booking.com",
    "expedia": "https://www.expedia.com",
    "tripadvisor": "https://www.tripadvisor.com",
    
    # Food/Delivery
    "doordash": "https://www.doordash.com",
    "ubereats": "https://www.ubereats.com",
    "grubhub": "https://www.grubhub.com",
    "instacart": "https://www.instacart.com",
    
    # Finance
    "stripe": "https://stripe.com",
    "paypal": "https://www.paypal.com",
    "robinhood": "https://robinhood.com",
    "coinbase": "https://www.coinbase.com",
    
    # News/Content
    "medium": "https://medium.com",
    "substack": "https://substack.com",
    "wordpress": "https://wordpress.com",
    
    # Productivity
    "dropbox": "https://www.dropbox.com",
    "zoom": "https://zoom.us",
    "calendly": "https://calendly.com",
}


class WebsiteAnalyzer:
    """Analyzes real websites to extract design patterns for inspiration"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.screenshot_service_url = os.getenv("SCREENSHOT_SERVICE_URL", "")
    
    def extract_website_reference(self, user_prompt: str) -> Optional[Tuple[str, str]]:
        """
        Extract website reference from user prompt
        
        Examples:
        - "build a website like Amazon" -> ("amazon", "https://www.amazon.com")
        - "create something similar to Spotify" -> ("spotify", "https://www.spotify.com")
        - "make a clone of https://example.com" -> ("example.com", "https://example.com")
        
        Returns: (site_name, url) or None
        """
        prompt_lower = user_prompt.lower()
        
        # Patterns to detect website references
        patterns = [
            r"like\s+(?:the\s+)?(?:a\s+)?([a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})?)",
            r"similar\s+to\s+(?:the\s+)?(?:a\s+)?([a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})?)",
            r"inspired\s+by\s+(?:the\s+)?(?:a\s+)?([a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})?)",
            r"clone\s+(?:of\s+)?(?:the\s+)?(?:a\s+)?([a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})?)",
            r"based\s+on\s+(?:the\s+)?(?:a\s+)?([a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})?)",
            r"style\s+of\s+(?:the\s+)?(?:a\s+)?([a-zA-Z0-9\-\.]+(?:\.[a-zA-Z]{2,})?)",
            r"(?:https?://)?(?:www\.)?([a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[^\s]*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                site_ref = match.group(1).strip().rstrip('.,!?')
                
                # Remove common suffixes that might be captured
                site_ref = re.sub(r'\s*(website|site|app|platform|service)s?$', '', site_ref).strip()
                
                # Check if it's a known popular site
                if site_ref in POPULAR_SITES:
                    return (site_ref, POPULAR_SITES[site_ref])
                
                # Check if it's a URL
                if '.' in site_ref:
                    if not site_ref.startswith('http'):
                        site_ref = 'https://' + site_ref
                    return (urlparse(site_ref).netloc or site_ref, site_ref)
                
                # Try adding .com
                if site_ref + '.com' in prompt_lower or site_ref in POPULAR_SITES:
                    pass  # Already checked
                elif site_ref.isalpha():
                    # Try to guess the URL
                    guessed_url = f"https://www.{site_ref}.com"
                    return (site_ref, guessed_url)
        
        return None
    
    async def analyze_website(self, url: str, site_name: str = "", take_screenshot: bool = True) -> WebsiteAnalysis:
        """
        Fully analyze a website for design patterns
        
        Args:
            url: The website URL to analyze
            site_name: Optional name for the site
            take_screenshot: Whether to attempt screenshot capture
            
        Returns:
            WebsiteAnalysis object with all extracted patterns
        """
        print(f"🔍 Analyzing website: {url}")
        
        analysis = WebsiteAnalysis(
            website_name=site_name or urlparse(url).netloc,
            website_url=url,
            analyzed_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        try:
            # Step 1: Fetch the webpage
            response = self.session.get(url, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"⚠️ HTTP {response.status_code} for {url}")
                analysis.analysis_quality = "failed"
                return analysis
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Step 2: Extract design patterns
            analysis = await self._extract_all_patterns(soup, analysis)
            
            # Step 3: Try to take a screenshot
            if take_screenshot:
                screenshot = await self._capture_screenshot(url)
                if screenshot:
                    analysis.screenshot_base64 = screenshot
                    analysis.analysis_quality = "with_screenshot"
                else:
                    analysis.analysis_quality = "detailed"
            else:
                analysis.analysis_quality = "detailed"
            
            # Step 4: Generate "similar but different" suggestions
            analysis.design_suggestions = self._generate_design_variations(analysis)
            
            print(f"✅ Analysis complete: {analysis.analysis_quality} quality")
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            analysis.analysis_quality = "failed"
            return analysis
    
    async def _extract_all_patterns(self, soup: BeautifulSoup, analysis: WebsiteAnalysis) -> WebsiteAnalysis:
        """Extract all design patterns from the parsed HTML"""
        
        # Layout Analysis
        analysis.layout_type = self._detect_layout_type(soup)
        analysis.grid_system = self._detect_grid_system(soup)
        analysis.page_structure = self._detect_page_structure(soup)
        
        # Color Extraction
        colors = self._extract_colors(soup)
        analysis.color_palette = colors.get('all', [])
        analysis.primary_colors = colors.get('primary', [])
        analysis.accent_colors = colors.get('accent', [])
        analysis.background_style = colors.get('background', 'light')
        
        # Typography
        fonts = self._extract_typography(soup)
        analysis.font_families = fonts.get('families', [])
        analysis.heading_style = fonts.get('heading_style', 'bold sans-serif')
        analysis.body_text_style = fonts.get('body_style', 'regular sans-serif')
        
        # Navigation
        nav_info = self._analyze_navigation(soup)
        analysis.navigation_type = nav_info.get('type', 'horizontal')
        analysis.navigation_items = nav_info.get('items', [])
        analysis.has_search = nav_info.get('has_search', False)
        analysis.has_cart = nav_info.get('has_cart', False)
        analysis.has_user_menu = nav_info.get('has_user_menu', False)
        
        # Components
        analysis.components = self._detect_components(soup)
        analysis.hero_section = self._analyze_hero_section(soup)
        analysis.product_cards = self._analyze_product_cards(soup)
        analysis.footer_structure = self._analyze_footer(soup)
        
        # Features
        analysis.features = self._detect_features(soup)
        analysis.interactive_elements = self._detect_interactive_elements(soup)
        
        # CSS Techniques
        analysis.css_techniques = self._extract_css_techniques(soup)
        analysis.animation_styles = self._detect_animations(soup)
        
        return analysis
    
    def _detect_layout_type(self, soup: BeautifulSoup) -> str:
        """Detect the primary layout pattern"""
        body_classes = ' '.join(soup.body.get('class', [])).lower() if soup.body else ''
        all_classes = self._get_all_classes(soup, limit=100)
        class_str = ' '.join(all_classes).lower()
        
        # Check for specific layout patterns
        if any(x in class_str for x in ['sidebar', 'aside', 'left-nav', 'right-panel']):
            return "sidebar-layout"
        elif any(x in class_str for x in ['grid', 'masonry', 'gallery']):
            return "grid-layout"
        elif any(x in class_str for x in ['dashboard', 'admin', 'panel']):
            return "dashboard-layout"
        elif any(x in class_str for x in ['landing', 'hero', 'full-width']):
            return "landing-page-layout"
        elif any(x in class_str for x in ['blog', 'article', 'post']):
            return "content-layout"
        elif any(x in class_str for x in ['shop', 'store', 'product', 'catalog']):
            return "ecommerce-layout"
        else:
            return "standard-layout"
    
    def _detect_grid_system(self, soup: BeautifulSoup) -> str:
        """Detect the grid system being used"""
        all_classes = self._get_all_classes(soup, limit=200)
        class_str = ' '.join(all_classes).lower()
        
        # Check for common grid systems
        if 'grid-cols' in class_str or 'col-span' in class_str:
            # Tailwind CSS Grid
            cols = re.findall(r'grid-cols-(\d+)', class_str)
            if cols:
                return f"tailwind-grid-{max(int(c) for c in cols)}-columns"
            return "tailwind-grid"
        elif any(f'col-{i}' in class_str or f'col-md-{i}' in class_str for i in range(1, 13)):
            return "bootstrap-12-column"
        elif 'flex' in class_str and ('flex-wrap' in class_str or 'flex-row' in class_str):
            return "flexbox-grid"
        elif 'css-grid' in class_str or 'display-grid' in class_str:
            return "css-grid"
        elif 'masonry' in class_str:
            return "masonry-grid"
        else:
            return "custom-grid"
    
    def _detect_page_structure(self, soup: BeautifulSoup) -> List[str]:
        """Detect the major page sections"""
        sections = []
        
        # Check for semantic elements
        if soup.find('header') or soup.find(class_=re.compile(r'header', re.I)):
            sections.append('header')
        if soup.find('nav') or soup.find(class_=re.compile(r'nav(bar)?', re.I)):
            sections.append('navigation')
        if soup.find(class_=re.compile(r'hero|banner|jumbotron', re.I)):
            sections.append('hero-section')
        if soup.find('main') or soup.find(class_=re.compile(r'main-content', re.I)):
            sections.append('main-content')
        if soup.find('aside') or soup.find(class_=re.compile(r'sidebar', re.I)):
            sections.append('sidebar')
        if soup.find(class_=re.compile(r'product|catalog|grid', re.I)):
            sections.append('product-grid')
        if soup.find(class_=re.compile(r'featured|showcase', re.I)):
            sections.append('featured-section')
        if soup.find(class_=re.compile(r'testimonial|review', re.I)):
            sections.append('testimonials')
        if soup.find(class_=re.compile(r'cta|call-to-action', re.I)):
            sections.append('cta-section')
        if soup.find('footer') or soup.find(class_=re.compile(r'footer', re.I)):
            sections.append('footer')
        
        return sections
    
    def _extract_colors(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract color palette from the website"""
        colors = {
            'all': [],
            'primary': [],
            'accent': [],
            'background': 'light'
        }
        
        # Extract from inline styles
        style_tags = soup.find_all('style')
        css_content = ' '.join(s.string or '' for s in style_tags)
        
        # Extract hex colors
        hex_colors = re.findall(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b', css_content)
        colors['all'].extend([f'#{c}' for c in hex_colors[:20]])
        
        # Extract rgb/rgba colors
        rgb_colors = re.findall(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', css_content)
        for r, g, b in rgb_colors[:10]:
            colors['all'].append(f'rgb({r},{g},{b})')
        
        # Extract from Tailwind/utility classes
        all_classes = self._get_all_classes(soup, limit=500)
        class_str = ' '.join(all_classes)
        
        # Tailwind color patterns
        tailwind_colors = re.findall(r'(?:bg|text|border)-(\w+)-(\d+)', class_str)
        for color_name, shade in tailwind_colors[:15]:
            colors['all'].append(f'{color_name}-{shade}')
        
        # Determine primary colors (most common)
        if colors['all']:
            from collections import Counter
            color_counts = Counter(colors['all'])
            most_common = color_counts.most_common(3)
            colors['primary'] = [c[0] for c in most_common]
        
        # Determine background style
        if any(dark in class_str.lower() for dark in ['dark', 'bg-black', 'bg-gray-900', 'bg-slate-900']):
            colors['background'] = 'dark'
        elif any(grad in class_str.lower() for grad in ['gradient', 'bg-gradient']):
            colors['background'] = 'gradient'
        else:
            colors['background'] = 'light'
        
        # Deduplicate
        colors['all'] = list(dict.fromkeys(colors['all']))[:15]
        
        return colors
    
    def _extract_typography(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract typography information"""
        fonts = {
            'families': [],
            'heading_style': 'bold sans-serif',
            'body_style': 'regular sans-serif'
        }
        
        # Check style tags for font-family
        style_tags = soup.find_all('style')
        css_content = ' '.join(s.string or '' for s in style_tags)
        
        font_matches = re.findall(r"font-family:\s*['\"]?([^;'\"]+)", css_content, re.I)
        for match in font_matches:
            # Extract first font in the stack
            first_font = match.split(',')[0].strip().strip("'\"")
            if first_font and first_font not in fonts['families']:
                fonts['families'].append(first_font)
        
        # Check for Google Fonts links
        for link in soup.find_all('link', href=True):
            if 'fonts.googleapis.com' in link['href']:
                font_match = re.search(r'family=([^:&]+)', link['href'])
                if font_match:
                    font_name = font_match.group(1).replace('+', ' ')
                    if font_name not in fonts['families']:
                        fonts['families'].append(font_name)
        
        # Analyze heading styles
        headings = soup.find_all(['h1', 'h2', 'h3'])
        if headings:
            h_classes = ' '.join(' '.join(h.get('class', [])) for h in headings[:5]).lower()
            if 'bold' in h_classes or 'font-bold' in h_classes:
                fonts['heading_style'] = 'bold'
            if 'italic' in h_classes:
                fonts['heading_style'] += ' italic'
            if 'serif' in h_classes:
                fonts['heading_style'] += ' serif'
            else:
                fonts['heading_style'] += ' sans-serif'
        
        fonts['families'] = fonts['families'][:5]  # Limit to 5
        
        return fonts
    
    def _analyze_navigation(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze navigation patterns"""
        nav_info = {
            'type': 'horizontal',
            'items': [],
            'has_search': False,
            'has_cart': False,
            'has_user_menu': False
        }
        
        # Find navigation elements
        nav = soup.find('nav') or soup.find('header') or soup.find(class_=re.compile(r'nav|header', re.I))
        
        if nav:
            nav_classes = ' '.join(nav.get('class', [])).lower()
            
            # Determine nav type
            if 'sidebar' in nav_classes or 'side' in nav_classes:
                nav_info['type'] = 'sidebar'
            elif 'vertical' in nav_classes:
                nav_info['type'] = 'vertical'
            elif 'fixed' in nav_classes or 'sticky' in nav_classes:
                nav_info['type'] = 'fixed-horizontal'
            else:
                nav_info['type'] = 'horizontal'
            
            # Extract nav items
            nav_links = nav.find_all('a', href=True)[:10]
            for link in nav_links:
                text = link.get_text(strip=True)[:30]
                if text and len(text) > 1:
                    nav_info['items'].append(text)
            
            # Check for common features
            nav_text = nav.get_text().lower()
            nav_info['has_search'] = bool(nav.find('input', type='search') or 
                                          nav.find(class_=re.compile(r'search', re.I)) or
                                          'search' in nav_text)
            nav_info['has_cart'] = bool(nav.find(class_=re.compile(r'cart|basket', re.I)) or
                                        'cart' in nav_text)
            nav_info['has_user_menu'] = bool(nav.find(class_=re.compile(r'user|account|profile|login', re.I)) or
                                             any(x in nav_text for x in ['sign in', 'login', 'account']))
        
        return nav_info
    
    def _detect_components(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Detect UI components used on the page"""
        components = []
        
        component_patterns = [
            ('card', r'card|tile|box', 'Card component with content container'),
            ('button', r'btn|button', 'Action buttons'),
            ('modal', r'modal|dialog|popup', 'Modal/dialog overlays'),
            ('carousel', r'carousel|slider|swiper', 'Image/content carousel'),
            ('accordion', r'accordion|collapse|expand', 'Collapsible content sections'),
            ('tabs', r'tab|tabbed', 'Tabbed navigation/content'),
            ('dropdown', r'dropdown|select|menu', 'Dropdown menus'),
            ('badge', r'badge|tag|chip', 'Badge/tag elements'),
            ('avatar', r'avatar|profile-pic', 'User avatar images'),
            ('rating', r'rating|stars|review', 'Star ratings'),
            ('pagination', r'pagination|pager', 'Page navigation'),
            ('breadcrumb', r'breadcrumb|crumb', 'Breadcrumb navigation'),
            ('toast', r'toast|notification|alert', 'Toast notifications'),
            ('progress', r'progress|loading|spinner', 'Progress indicators'),
            ('form', r'form|input-group', 'Form elements'),
        ]
        
        all_classes = self._get_all_classes(soup, limit=300)
        class_str = ' '.join(all_classes).lower()
        
        for comp_name, pattern, description in component_patterns:
            if re.search(pattern, class_str, re.I):
                # Count occurrences
                count = len(re.findall(pattern, class_str, re.I))
                components.append({
                    'name': comp_name,
                    'description': description,
                    'count': min(count, 50),
                    'detected': True
                })
        
        return components
    
    def _analyze_hero_section(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Analyze the hero/banner section"""
        hero = soup.find(class_=re.compile(r'hero|banner|jumbotron|masthead', re.I))
        
        if not hero:
            # Try to find the first major section
            first_section = soup.find('section') or soup.find(class_=re.compile(r'section', re.I))
            if first_section:
                hero = first_section
            else:
                return None
        
        hero_info = {
            'has_image': bool(hero.find('img')),
            'has_video': bool(hero.find('video')),
            'has_heading': bool(hero.find(['h1', 'h2'])),
            'has_cta_button': bool(hero.find(class_=re.compile(r'btn|button|cta', re.I))),
            'has_subtext': bool(hero.find('p')),
            'style': 'standard'
        }
        
        hero_classes = ' '.join(hero.get('class', [])).lower()
        if 'full' in hero_classes or 'vh-100' in hero_classes:
            hero_info['style'] = 'full-screen'
        elif 'split' in hero_classes:
            hero_info['style'] = 'split-layout'
        elif hero.find('video'):
            hero_info['style'] = 'video-background'
        
        return hero_info
    
    def _analyze_product_cards(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Analyze product/item card patterns"""
        cards = soup.find_all(class_=re.compile(r'product|item|card', re.I))[:5]
        
        if not cards:
            return None
        
        card = cards[0]
        card_info = {
            'count': len(cards),
            'has_image': bool(card.find('img')),
            'has_price': bool(card.find(class_=re.compile(r'price', re.I)) or 
                             '$' in card.get_text() or '€' in card.get_text()),
            'has_rating': bool(card.find(class_=re.compile(r'rating|star', re.I))),
            'has_add_to_cart': bool(card.find(class_=re.compile(r'cart|buy|add', re.I))),
            'layout': 'vertical'
        }
        
        card_classes = ' '.join(card.get('class', [])).lower()
        if 'horizontal' in card_classes or 'row' in card_classes:
            card_info['layout'] = 'horizontal'
        
        return card_info
    
    def _analyze_footer(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Analyze footer structure"""
        footer = soup.find('footer') or soup.find(class_=re.compile(r'footer', re.I))
        
        if not footer:
            return None
        
        footer_info = {
            'has_logo': bool(footer.find('img') or footer.find(class_=re.compile(r'logo', re.I))),
            'has_social_links': bool(footer.find(class_=re.compile(r'social', re.I)) or
                                     any(s in footer.get_text().lower() for s in ['facebook', 'twitter', 'instagram'])),
            'has_newsletter': bool(footer.find('form') or footer.find(class_=re.compile(r'newsletter|subscribe', re.I))),
            'has_links': len(footer.find_all('a', href=True)) > 5,
            'column_count': 1
        }
        
        # Estimate column count
        footer_classes = ' '.join(footer.get('class', [])).lower()
        if 'col-' in footer_classes or 'grid-cols' in footer_classes:
            cols = re.findall(r'(?:col-|grid-cols-)(\d+)', footer_classes)
            if cols:
                footer_info['column_count'] = int(cols[0])
        
        return footer_info
    
    def _detect_features(self, soup: BeautifulSoup) -> List[str]:
        """Detect features present on the website"""
        features = []
        
        page_text = soup.get_text().lower()
        all_classes = ' '.join(self._get_all_classes(soup, limit=500)).lower()
        
        feature_checks = [
            ('search', lambda: bool(soup.find('input', type='search') or 'search' in all_classes)),
            ('shopping-cart', lambda: 'cart' in all_classes or 'basket' in all_classes),
            ('user-authentication', lambda: any(x in page_text for x in ['sign in', 'login', 'register'])),
            ('wishlist', lambda: 'wishlist' in all_classes or 'favorite' in all_classes),
            ('reviews', lambda: 'review' in all_classes or 'rating' in all_classes),
            ('filters', lambda: 'filter' in all_classes or 'sort' in all_classes),
            ('pagination', lambda: 'pagination' in all_classes or 'pager' in all_classes),
            ('infinite-scroll', lambda: 'infinite' in all_classes or 'load-more' in all_classes),
            ('newsletter', lambda: 'newsletter' in all_classes or 'subscribe' in all_classes),
            ('live-chat', lambda: 'chat' in all_classes or 'messenger' in all_classes),
            ('dark-mode', lambda: 'dark-mode' in all_classes or 'theme-toggle' in all_classes),
            ('multi-language', lambda: 'language' in all_classes or 'locale' in all_classes),
        ]
        
        for feature_name, check_func in feature_checks:
            try:
                if check_func():
                    features.append(feature_name)
            except:
                pass
        
        return features
    
    def _detect_interactive_elements(self, soup: BeautifulSoup) -> List[str]:
        """Detect interactive elements"""
        elements = []
        
        if soup.find_all('button'):
            elements.append('buttons')
        if soup.find_all('form'):
            elements.append('forms')
        if soup.find_all('input'):
            elements.append('input-fields')
        if soup.find_all('select'):
            elements.append('dropdowns')
        if soup.find_all(class_=re.compile(r'modal|dialog', re.I)):
            elements.append('modals')
        if soup.find_all(class_=re.compile(r'tooltip', re.I)):
            elements.append('tooltips')
        if soup.find_all(class_=re.compile(r'accordion|collapse', re.I)):
            elements.append('accordions')
        if soup.find_all(class_=re.compile(r'tab', re.I)):
            elements.append('tabs')
        if soup.find_all(class_=re.compile(r'carousel|slider', re.I)):
            elements.append('carousels')
        
        return elements
    
    def _extract_css_techniques(self, soup: BeautifulSoup) -> List[str]:
        """Extract CSS techniques being used"""
        techniques = []
        all_classes = ' '.join(self._get_all_classes(soup, limit=300)).lower()
        
        # Check style content
        style_content = ' '.join(s.string or '' for s in soup.find_all('style')).lower()
        
        technique_patterns = [
            ('flexbox', ['flex', 'flex-row', 'flex-col', 'justify-', 'items-']),
            ('css-grid', ['grid', 'grid-cols', 'grid-template', 'col-span']),
            ('glassmorphism', ['backdrop-blur', 'bg-opacity', 'glass']),
            ('gradients', ['gradient', 'bg-gradient', 'from-', 'to-']),
            ('shadows', ['shadow', 'drop-shadow', 'box-shadow']),
            ('rounded-corners', ['rounded', 'border-radius']),
            ('transitions', ['transition', 'duration-', 'ease-']),
            ('transforms', ['transform', 'rotate', 'scale', 'translate']),
            ('animations', ['animate-', 'animation', '@keyframes']),
            ('responsive', ['sm:', 'md:', 'lg:', 'xl:', '@media']),
            ('dark-mode', ['dark:', 'dark-mode']),
            ('custom-properties', ['var(--', '--color', '--font']),
        ]
        
        combined = all_classes + ' ' + style_content
        for tech_name, patterns in technique_patterns:
            if any(p in combined for p in patterns):
                techniques.append(tech_name)
        
        return techniques
    
    def _detect_animations(self, soup: BeautifulSoup) -> List[str]:
        """Detect animation patterns"""
        animations = []
        all_classes = ' '.join(self._get_all_classes(soup, limit=200)).lower()
        
        animation_patterns = {
            'fade-in': ['fade', 'opacity'],
            'slide-in': ['slide', 'translate'],
            'scale': ['scale', 'zoom', 'grow'],
            'rotate': ['rotate', 'spin'],
            'bounce': ['bounce', 'elastic'],
            'pulse': ['pulse', 'ping'],
            'hover-effects': ['hover:', 'hover-'],
            'scroll-animations': ['scroll', 'aos', 'intersection'],
        }
        
        for anim_name, patterns in animation_patterns.items():
            if any(p in all_classes for p in patterns):
                animations.append(anim_name)
        
        return animations
    
    async def _capture_screenshot(self, url: str) -> Optional[str]:
        """Capture a screenshot of the website"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _sync_capture_playwright(url: str) -> Optional[str]:
            """Synchronous playwright capture to run in thread"""
            if not PLAYWRIGHT_AVAILABLE:
                return None
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    screenshot_bytes = page.screenshot(type='png')
                    browser.close()
                    return base64.b64encode(screenshot_bytes).decode('utf-8')
            except Exception as e:
                print(f"Playwright screenshot failed: {e}")
                return None
        
        def _sync_capture_selenium(url: str) -> Optional[str]:
            """Synchronous selenium capture to run in thread"""
            if not SELENIUM_AVAILABLE:
                return None
            try:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                
                driver = webdriver.Chrome(options=options)
                driver.get(url)
                time.sleep(3)  # Wait for page load
                screenshot_bytes = driver.get_screenshot_as_png()
                driver.quit()
                return base64.b64encode(screenshot_bytes).decode('utf-8')
            except Exception as e:
                print(f"Selenium screenshot failed: {e}")
                return None
        
        # Method 1: Try Playwright in thread pool
        if PLAYWRIGHT_AVAILABLE:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, _sync_capture_playwright, url)
                    if result:
                        return result
            except Exception as e:
                print(f"Playwright async screenshot failed: {e}")
        
        # Method 2: Try Selenium in thread pool
        if SELENIUM_AVAILABLE:
            try:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, _sync_capture_selenium, url)
                    if result:
                        return result
            except Exception as e:
                print(f"Selenium async screenshot failed: {e}")
        
        # Method 3: Try external screenshot service
        if self.screenshot_service_url:
            try:
                encoded_url = quote(url, safe='')
                response = requests.get(
                    f"{self.screenshot_service_url}?url={encoded_url}&width=1920&height=1080",
                    timeout=30
                )
                if response.status_code == 200:
                    return base64.b64encode(response.content).decode('utf-8')
            except Exception as e:
                print(f"Screenshot service failed: {e}")
        
        # Method 4: Try free screenshot API (limited)
        try:
            # Using a free screenshot API as fallback
            api_url = f"https://api.apiflash.com/v1/urltoimage?access_key=demo&url={quote(url, safe='')}&format=png&width=1920&height=1080"
            response = requests.get(api_url, timeout=30)
            if response.status_code == 200 and len(response.content) > 1000:
                return base64.b64encode(response.content).decode('utf-8')
        except:
            pass
        
        print("⚠️ All screenshot methods failed")
        return None
    
    def _generate_design_variations(self, analysis: WebsiteAnalysis) -> Dict[str, str]:
        """Generate suggestions for creating a similar but different design"""
        suggestions = {}
        
        # Color variations
        if 'light' in analysis.background_style:
            suggestions['color_theme'] = "Consider a dark mode variant or a gradient background for a fresh look"
        else:
            suggestions['color_theme'] = "Try a light theme with vibrant accent colors for contrast"
        
        # Layout variations
        layout_alternatives = {
            'sidebar-layout': 'Try a full-width layout with a collapsible hamburger menu',
            'grid-layout': 'Consider a masonry or bento-style grid for more visual interest',
            'dashboard-layout': 'Use a card-based layout with floating action buttons',
            'landing-page-layout': 'Add parallax scrolling or section-based animations',
            'ecommerce-layout': 'Try a Pinterest-style infinite scroll layout',
        }
        suggestions['layout'] = layout_alternatives.get(analysis.layout_type, 
            'Experiment with asymmetric layouts or split-screen designs')
        
        # Navigation variations
        if 'horizontal' in analysis.navigation_type:
            suggestions['navigation'] = "Consider a sidebar navigation or a floating bottom nav for mobile-first design"
        else:
            suggestions['navigation'] = "Try a mega-menu or a contextual navigation that adapts to content"
        
        # Typography
        if analysis.font_families:
            suggestions['typography'] = f"Replace '{analysis.font_families[0] if analysis.font_families else 'default'}' with a contrasting font pair - try mixing serif headings with sans-serif body"
        else:
            suggestions['typography'] = "Use a distinctive display font for headings to create brand identity"
        
        # Components
        suggestions['components'] = "Add micro-interactions to cards (hover effects, subtle animations) and use skeleton loaders for better UX"
        
        # Modern touches
        suggestions['modern_features'] = "Add glassmorphism effects, gradient borders, or animated backgrounds to stand out"
        
        # Unique elements
        suggestions['differentiation'] = "Create a unique hero section with 3D elements, add a distinctive footer design, and use custom illustrations instead of stock photos"
        
        return suggestions
    
    def _get_all_classes(self, soup: BeautifulSoup, limit: int = 100) -> List[str]:
        """Get all CSS classes from the page"""
        classes = []
        for elem in soup.find_all(class_=True)[:limit]:
            if isinstance(elem.get('class'), list):
                classes.extend(elem['class'])
        return classes


# Global instance
website_analyzer = WebsiteAnalyzer()


async def analyze_website_for_inspiration(user_prompt: str) -> Optional[WebsiteAnalysis]:
    """
    Main function to analyze a website mentioned in user prompt
    
    Args:
        user_prompt: The user's request (e.g., "build a website like Amazon")
        
    Returns:
        WebsiteAnalysis if a website reference was found, None otherwise
    """
    # Extract website reference from prompt
    site_ref = website_analyzer.extract_website_reference(user_prompt)
    
    if not site_ref:
        return None
    
    site_name, url = site_ref
    print(f"🎯 Found website reference: {site_name} ({url})")
    
    # Analyze the website
    analysis = await website_analyzer.analyze_website(url, site_name)
    
    return analysis


def get_inspiration_prompt_context(analysis: WebsiteAnalysis) -> str:
    """
    Convert website analysis into context for AI prompt
    
    Args:
        analysis: The website analysis object
        
    Returns:
        String context to add to AI generation prompt
    """
    if not analysis or analysis.analysis_quality == "failed":
        return ""
    
    context = f"""
=== WEBSITE INSPIRATION ANALYSIS ===
Analyzed Website: {analysis.website_name} ({analysis.website_url})
Analysis Quality: {analysis.analysis_quality}

DESIGN PATTERNS EXTRACTED:
- Layout Type: {analysis.layout_type}
- Grid System: {analysis.grid_system}
- Page Structure: {', '.join(analysis.page_structure)}

VISUAL DESIGN:
- Color Palette: {', '.join(analysis.primary_colors[:5])}
- Background Style: {analysis.background_style}
- Typography: {', '.join(analysis.font_families[:3])}
- Heading Style: {analysis.heading_style}

NAVIGATION:
- Type: {analysis.navigation_type}
- Has Search: {analysis.has_search}
- Has Cart: {analysis.has_cart}
- Has User Menu: {analysis.has_user_menu}
- Menu Items: {', '.join(analysis.navigation_items[:5])}

COMPONENTS DETECTED:
{chr(10).join([f"- {c['name']}: {c['count']} instances" for c in analysis.components[:8]])}

HERO SECTION:
{json.dumps(analysis.hero_section, indent=2) if analysis.hero_section else 'Not detected'}

PRODUCT/CARD LAYOUT:
{json.dumps(analysis.product_cards, indent=2) if analysis.product_cards else 'Not detected'}

FEATURES:
{', '.join(analysis.features)}

CSS TECHNIQUES:
{', '.join(analysis.css_techniques)}

ANIMATIONS:
{', '.join(analysis.animation_styles)}

=== IMPORTANT: CREATE A SIMILAR BUT UNIQUE DESIGN ===
Do NOT copy the exact design. Instead, use these suggestions to create something inspired but different:

{chr(10).join([f"- {k}: {v}" for k, v in analysis.design_suggestions.items()])}

Create a UNIQUE design that captures the essence and functionality of {analysis.website_name} 
but with your own creative interpretation. Change colors, fonts, layouts, and add unique features.
"""
    
    return context


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test extraction
        prompts = [
            "Build a website like Amazon",
            "Create an e-commerce site similar to Shopify",
            "Make me a dashboard inspired by Notion",
            "I want a streaming app like Netflix",
            "Build https://stripe.com clone",
        ]
        
        for prompt in prompts:
            print(f"\n{'='*50}")
            print(f"Prompt: {prompt}")
            result = website_analyzer.extract_website_reference(prompt)
            if result:
                print(f"Detected: {result[0]} -> {result[1]}")
            else:
                print("No website reference found")
        
        # Test full analysis
        print(f"\n{'='*50}")
        print("Testing full analysis on Amazon...")
        analysis = await analyze_website_for_inspiration("build a website like amazon")
        if analysis:
            print(f"Analysis quality: {analysis.analysis_quality}")
            print(f"Layout: {analysis.layout_type}")
            print(f"Colors: {analysis.primary_colors}")
            print(f"Features: {analysis.features}")
            print(f"Components: {[c['name'] for c in analysis.components]}")
    
    asyncio.run(test())
