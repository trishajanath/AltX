"""
Advanced Layout Design System with Web Scraping for Award-Winning Layouts

This module scrapes modern design trends and creates diverse layout systems
inspired by Awwwards, CSS Design Awards, and other design showcases.
"""

import json
import random
import hashlib
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class LayoutPattern:
    """Represents a unique layout pattern with design specifications."""
    name: str
    type: str
    grid_system: str
    navigation: str
    hero_style: str
    content_flow: str
    visual_hierarchy: str
    color_approach: str
    typography_scale: str
    spacing_system: str
    interactive_elements: List[str]
    animation_style: str
    responsive_strategy: str
    css_classes: List[str]
    design_inspiration: str
    visual_effects: List[str]  # Added missing field
    design_principles: List[str]  # Added missing field

class AdvancedLayoutSystem:
    """Creates diverse, award-winning layouts for each generated project."""
    
    def __init__(self):
        self.layout_patterns = self._initialize_layout_patterns()
        self.used_patterns = set()  # Track used patterns to ensure variety
        self.css_tokens = self._initialize_css_tokens()  # Dynamic CSS variables
        
    def _initialize_css_tokens(self) -> Dict[str, Any]:
        """Initialize dynamic CSS tokens for unique variations."""
        return {
            'accent_colors': [
                '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', 
                '#ef4444', '#06b6d4', '#84cc16', '#f97316', '#8b5a2b'
            ],
            'neutral_colors': [
                '#1f2937', '#374151', '#6b7280', '#9ca3af', '#d1d5db',
                '#f3f4f6', '#f9fafb', '#ffffff', '#000000', '#111827'
            ],
            'radius_values': ['0.25rem', '0.5rem', '0.75rem', '1rem', '1.5rem', '2rem', '3rem', '4rem'],
            'font_families': [
                'Inter, system-ui, sans-serif',
                'Poppins, system-ui, sans-serif', 
                'Roboto, system-ui, sans-serif',
                'Playfair Display, serif',
                'Source Code Pro, monospace',
                'Space Grotesk, sans-serif',
                'Outfit, sans-serif'
            ],
            'spacing_scales': ['0.25rem', '0.5rem', '1rem', '1.5rem', '2rem', '3rem', '4rem', '6rem'],
            'shadow_intensities': ['soft', 'medium', 'strong', 'glow', 'inner'],
            'animation_speeds': ['150ms', '200ms', '300ms', '500ms', '700ms', '1000ms']
        }
        
    def _initialize_layout_patterns(self) -> List[LayoutPattern]:
        """Initialize diverse layout patterns inspired by award-winning sites."""
        return [
            # 1. Magazine Editorial Layout (Inspired by Vogue, Kinfolk)
            LayoutPattern(
                name="editorial_magazine",
                type="Magazine Editorial",
                grid_system="asymmetric_editorial",
                navigation="minimal_top_nav",
                hero_style="full_bleed_typography",
                content_flow="editorial_columns",
                visual_hierarchy="typographic_scale",
                color_approach="high_contrast_minimal",
                typography_scale="editorial_large",
                spacing_system="generous_whitespace",
                interactive_elements=["smooth_scroll", "parallax_text", "hover_reveals"],
                animation_style="subtle_fade_transitions",
                responsive_strategy="content_first",
                css_classes=[
                    "grid grid-cols-12 gap-8",
                    "col-span-8 text-6xl font-light leading-tight",
                    "col-span-4 text-lg leading-loose opacity-70",
                    "py-24 px-12",
                    "border-l border-gray-200 pl-8"
                ],
                design_inspiration="Kinfolk Magazine, Vogue Digital, Editorial Layouts",
                visual_effects=["Typography Focus", "Whitespace Mastery", "Elegant Simplicity"],
                design_principles=["Content First", "Readable Typography", "Generous Whitespace"]
            ),
            
            # 2. Brutalist Architecture (Inspired by Gumroad, Linear)
            LayoutPattern(
                name="brutalist_geometric",
                type="Brutalist Geometric",
                grid_system="strict_geometric",
                navigation="bold_geometric_nav",
                hero_style="geometric_blocks",
                content_flow="card_grid_system",
                visual_hierarchy="size_weight_contrast",
                color_approach="monochrome_accent",
                typography_scale="bold_condensed",
                spacing_system="tight_geometric",
                interactive_elements=["sharp_hover_effects", "geometric_transitions", "bold_animations"],
                animation_style="sharp_geometric_motion",
                responsive_strategy="block_stacking",
                css_classes=[
                    "grid grid-cols-4 gap-0",
                    "bg-black text-white p-8",
                    "border-2 border-white",
                    "hover:bg-white hover:text-black transition-all duration-300",
                    "font-mono font-bold uppercase tracking-wider"
                ],
                design_inspiration="Linear.app, Gumroad, Swiss Design Principles",
                visual_effects=["Sharp Edges", "Bold Typography", "High Contrast"],
                design_principles=["Brutalist Design", "Function Over Form", "Raw Aesthetics"]
            ),
            
            # 3. Organic Flowing Layout (Inspired by Apple, Airbnb)
            LayoutPattern(
                name="organic_flowing",
                type="Organic Flowing",
                grid_system="organic_flow",
                navigation="floating_navigation",
                hero_style="curved_sections",
                content_flow="flowing_content",
                visual_hierarchy="natural_progression",
                color_approach="gradient_harmony",
                typography_scale="natural_rhythm",
                spacing_system="organic_breathing",
                interactive_elements=["smooth_curves", "organic_hover", "flowing_animations"],
                animation_style="natural_easing",
                responsive_strategy="fluid_adaptation",
                css_classes=[
                    "rounded-[3rem] bg-gradient-to-br from-blue-50 to-purple-50",
                    "backdrop-blur-md bg-white/60",
                    "shadow-2xl shadow-blue-500/10",
                    "hover:shadow-3xl hover:shadow-blue-500/20 transition-all duration-500",
                    "border border-white/20"
                ],
                design_inspiration="Apple.com, Airbnb, Organic Interface Design",
                visual_effects=["Smooth Curves", "Natural Transitions", "Gradient Flow"],
                design_principles=["Organic Design", "Natural Rhythm", "Fluid Adaptation"]
            ),
            
            # 4. Split Screen Diagonal (Inspired by Stripe, Figma)
            LayoutPattern(
                name="diagonal_split",
                type="Diagonal Split Screen",
                grid_system="diagonal_division",
                navigation="integrated_diagonal",
                hero_style="diagonal_hero",
                content_flow="alternating_diagonals",
                visual_hierarchy="diagonal_emphasis",
                color_approach="dual_tone_contrast",
                typography_scale="contrast_pairing",
                spacing_system="angular_rhythm",
                interactive_elements=["diagonal_reveals", "split_interactions", "angular_hover"],
                animation_style="diagonal_motion",
                responsive_strategy="mobile_stacking",
                css_classes=[
                    "clip-path-diagonal bg-gradient-to-br from-indigo-600 to-purple-700",
                    "transform skew-y-3 origin-top-left",
                    "-skew-y-3 p-16",
                    "relative z-10 overflow-hidden",
                    "before:absolute before:inset-0 before:bg-white/10 before:backdrop-blur"
                ],
                design_inspiration="Stripe.com, Figma, Angular Design Systems",
                visual_effects=["Diagonal Splits", "Dynamic Angles", "Bold Geometry"],
                design_principles=["Angular Design", "Split Screens", "Directional Flow"]
            ),
            
            # 5. Card Masonry Layout (Inspired by Pinterest, Behance)
            LayoutPattern(
                name="masonry_cards",
                type="Dynamic Masonry",
                grid_system="masonry_flow",
                navigation="sticky_minimal",
                hero_style="masonry_hero",
                content_flow="dynamic_cards",
                visual_hierarchy="card_importance",
                color_approach="varied_card_colors",
                typography_scale="card_typography",
                spacing_system="dynamic_gaps",
                interactive_elements=["card_hover_lift", "masonry_rearrange", "infinite_scroll"],
                animation_style="staggered_reveals",
                responsive_strategy="responsive_columns",
                css_classes=[
                    "columns-1 md:columns-2 lg:columns-3 xl:columns-4 gap-6",
                    "break-inside-avoid mb-6",
                    "bg-white rounded-2xl shadow-lg overflow-hidden",
                    "hover:shadow-2xl hover:-translate-y-2 transition-all duration-300",
                    "p-6 backdrop-blur-sm bg-white/90"
                ],
                design_inspiration="Pinterest, Behance, Masonry Layouts",
                visual_effects=["Dynamic Grid", "Card Elevation", "Staggered Layout"],
                design_principles=["Content Discovery", "Visual Hierarchy", "Flexible Grid"]
            ),
            
            # 6. Full-Screen Immersive (Inspired by Awwwards winners)
            LayoutPattern(
                name="immersive_fullscreen",
                type="Immersive Full-Screen",
                grid_system="viewport_sections",
                navigation="overlay_navigation",
                hero_style="immersive_viewport",
                content_flow="fullscreen_sections",
                visual_hierarchy="immersive_focus",
                color_approach="immersive_gradients",
                typography_scale="hero_typography",
                spacing_system="viewport_rhythm",
                interactive_elements=["scroll_snap", "parallax_layers", "immersive_transitions"],
                animation_style="cinematic_motion",
                responsive_strategy="adaptive_fullscreen",
                css_classes=[
                    "min-h-screen flex items-center justify-center",
                    "bg-gradient-to-br from-gray-900 via-purple-900 to-violet-800",
                    "relative overflow-hidden",
                    "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_30%_40%,rgba(120,119,198,0.3),transparent_50%)]",
                    "text-white text-center"
                ],
                design_inspiration="Awwwards Winners, Immersive Web Experiences",
                visual_effects=["Fullscreen Sections", "Parallax Layers", "Cinematic Motion"],
                design_principles=["Immersive Experience", "Viewport Focus", "Story-Driven"]
            ),
            
            # 7. Minimalist Grid (Inspired by Muji, Less is More)
            LayoutPattern(
                name="minimalist_grid",
                type="Minimalist Grid System",
                grid_system="minimal_grid",
                navigation="minimal_dots",
                hero_style="minimal_statement",
                content_flow="grid_perfection",
                visual_hierarchy="minimal_contrast",
                color_approach="minimal_palette",
                typography_scale="minimal_type",
                spacing_system="minimal_precision",
                interactive_elements=["subtle_hover", "minimal_feedback", "grid_highlights"],
                animation_style="minimal_motion",
                responsive_strategy="grid_collapse",
                css_classes=[
                    "grid grid-cols-12 gap-px bg-gray-100",
                    "bg-white p-12 hover:bg-gray-50 transition-colors duration-200",
                    "border-none outline-none",
                    "text-gray-900 font-light",
                    "leading-relaxed tracking-wide"
                ],
                design_inspiration="Muji Design, Minimal Interface Principles",
                visual_effects=["Subtle Hover", "Clean Grid", "Minimal Feedback"],
                design_principles=["Less is More", "Minimal Precision", "Grid Perfection"]
            ),
            
            # 8. Neumorphism 3D (Inspired by iOS, Material Design Evolution)
            LayoutPattern(
                name="neumorphic_3d",
                type="Neumorphic 3D Interface",
                grid_system="soft_grid",
                navigation="floating_neumorphic",
                hero_style="elevated_hero",
                content_flow="soft_cards",
                visual_hierarchy="depth_layers",
                color_approach="soft_monochrome",
                typography_scale="soft_typography",
                spacing_system="comfortable_padding",
                interactive_elements=["press_feedback", "soft_shadows", "depth_hover"],
                animation_style="soft_motion",
                responsive_strategy="adaptive_softness",
                css_classes=[
                    "bg-gray-100 rounded-3xl p-8",
                    "shadow-[inset_-12px_-8px_40px_#46464620]",
                    "shadow-[inset_12px_8px_40px_#ffffff70]",
                    "hover:shadow-[inset_-2px_-2px_8px_#46464620] transition-all duration-300",
                    "border border-white/50"
                ],
                design_inspiration="iOS Design, Neumorphism Trend, Soft UI",
                visual_effects=["Soft Shadows", "3D Depth", "Press Feedback"],
                design_principles=["Soft UI", "Tactile Design", "Depth Layers"]
            ),
            
            # 9. Geometric Bauhaus (Inspired by Bauhaus, Mondrian)
            LayoutPattern(
                name="bauhaus_geometric",
                type="Bauhaus Geometric",
                grid_system="bauhaus_grid",
                navigation="geometric_nav",
                hero_style="primary_shapes",
                content_flow="geometric_blocks",
                visual_hierarchy="color_geometry",
                color_approach="primary_colors",
                typography_scale="bauhaus_type",
                spacing_system="mathematical_rhythm",
                interactive_elements=["shape_transforms", "color_changes", "geometric_hover"],
                animation_style="mechanical_precision",
                responsive_strategy="proportional_scaling",
                css_classes=[
                    "grid grid-cols-6 grid-rows-4 gap-2 h-screen",
                    "bg-red-500 col-span-2 row-span-2",
                    "bg-blue-600 col-span-3 row-span-1",
                    "bg-yellow-400 col-span-1 row-span-3",
                    "bg-black text-white font-bold uppercase"
                ],
                design_inspiration="Bauhaus Movement, Mondrian Compositions, Geometric Design",
                visual_effects=["Geometric Shapes", "Primary Colors", "Bold Contrast"],
                design_principles=["Form Follows Function", "Mathematical Precision", "Bauhaus Principles"]
            ),
            
            # 10. Glassmorphism Layers (Inspired by Windows 11, iOS 15)
            LayoutPattern(
                name="glassmorphism_layers",
                type="Glassmorphism Layered",
                grid_system="floating_grid",
                navigation="glass_navigation",
                hero_style="glass_hero",
                content_flow="layered_glass",
                visual_hierarchy="transparency_depth",
                color_approach="translucent_colors",
                typography_scale="glass_typography",
                spacing_system="floating_rhythm",
                interactive_elements=["glass_hover", "blur_changes", "transparency_shifts"],
                animation_style="glass_motion",
                responsive_strategy="adaptive_transparency",
                css_classes=[
                    "backdrop-blur-xl bg-white/10",
                    "border border-white/20 rounded-2xl",
                    "shadow-2xl shadow-black/10",
                    "hover:bg-white/20 hover:backdrop-blur-2xl transition-all duration-300",
                    "relative z-10"
                ],
                design_inspiration="Windows 11 Design, iOS 15, Glassmorphism Trend",
                visual_effects=["Glass Blur", "Transparency Layers", "Floating Elements"],
                design_principles=["Material Transparency", "Depth Through Blur", "Layered Design"]
            ),
            
            # 11. Asymmetric Creative (Inspired by Creative Agencies)
            LayoutPattern(
                name="asymmetric_creative",
                type="Asymmetric Creative Layout",
                grid_system="asymmetric_overlap",
                navigation="hidden_hamburger",
                hero_style="overlapping_hero",
                content_flow="asymmetric_sections",
                visual_hierarchy="visual_tension",
                color_approach="bold_duo_tone",
                typography_scale="expressive_type",
                spacing_system="dynamic_overlap",
                interactive_elements=["parallax_scroll", "reveal_animations", "cursor_effects"],
                animation_style="expressive_motion",
                responsive_strategy="creative_adapt",
                css_classes=[
                    "grid grid-cols-12 -space-x-16",
                    "col-span-7 -rotate-2 hover:rotate-0 transition-transform",
                    "col-span-6 translate-y-12 z-20",
                    "bg-black text-white p-16 rounded-none",
                    "mix-blend-difference"
                ],
                design_inspiration="Creative Agencies, Experimental Web Design",
                visual_effects=["Overlapping Elements", "Visual Tension", "Bold Contrasts"],
                design_principles=["Break the Grid", "Creative Freedom", "Visual Impact"]
            ),
            
            # 12. Horizontal Scroll (Inspired by Portfolio Sites)
            LayoutPattern(
                name="horizontal_portfolio",
                type="Horizontal Scroll Portfolio",
                grid_system="horizontal_container",
                navigation="fixed_side_nav",
                hero_style="horizontal_intro",
                content_flow="horizontal_panels",
                visual_hierarchy="sequence_flow",
                color_approach="project_palette",
                typography_scale="headline_focus",
                spacing_system="panel_rhythm",
                interactive_elements=["scroll_snap", "drag_scroll", "panel_reveal"],
                animation_style="horizontal_motion",
                responsive_strategy="vertical_fallback",
                css_classes=[
                    "flex flex-nowrap overflow-x-auto snap-x snap-mandatory",
                    "flex-shrink-0 w-screen h-screen snap-center",
                    "flex items-center justify-center",
                    "scroll-smooth scrollbar-hide",
                    "bg-gradient-to-r from-gray-900 to-gray-800"
                ],
                design_inspiration="Portfolio Sites, Horizontal Experiences",
                visual_effects=["Horizontal Flow", "Panel Snapping", "Sequence Animation"],
                design_principles=["Storytelling Flow", "Project Showcase", "Immersive Navigation"]
            ),
            
            # 13. Dark Luxury (Inspired by Fashion Brands)
            LayoutPattern(
                name="dark_luxury",
                type="Dark Luxury Interface",
                grid_system="centered_luxury",
                navigation="elegant_header",
                hero_style="cinematic_hero",
                content_flow="luxury_sections",
                visual_hierarchy="gold_accents",
                color_approach="dark_gold_palette",
                typography_scale="elegant_serif",
                spacing_system="luxurious_padding",
                interactive_elements=["subtle_hover", "gold_highlights", "fade_reveals"],
                animation_style="subtle_elegance",
                responsive_strategy="premium_adapt",
                css_classes=[
                    "bg-black text-white",
                    "border-b border-amber-600/30",
                    "text-amber-400 font-serif tracking-widest",
                    "py-32 px-8 text-center",
                    "hover:text-amber-300 transition-colors duration-500"
                ],
                design_inspiration="Luxury Fashion, Premium Brands, Rolex, Gucci",
                visual_effects=["Gold Accents", "Elegant Transitions", "Cinematic Feel"],
                design_principles=["Luxury Design", "Premium Experience", "Understated Elegance"]
            ),
            
            # 14. Playful Colorful (Inspired by Gaming/Youth Brands)
            LayoutPattern(
                name="playful_colorful",
                type="Playful Colorful Design",
                grid_system="fun_grid",
                navigation="bouncy_nav",
                hero_style="colorful_splash",
                content_flow="playful_cards",
                visual_hierarchy="color_pop",
                color_approach="rainbow_gradient",
                typography_scale="fun_bold",
                spacing_system="bouncy_rhythm",
                interactive_elements=["bounce_hover", "wiggle_animations", "confetti_effects"],
                animation_style="playful_bouncy",
                responsive_strategy="fun_responsive",
                css_classes=[
                    "bg-gradient-to-br from-pink-400 via-purple-500 to-indigo-600",
                    "rounded-3xl shadow-2xl p-8 hover:scale-105 transition-transform",
                    "text-white font-extrabold text-4xl",
                    "animate-bounce hover:animate-none",
                    "border-4 border-yellow-300"
                ],
                design_inspiration="Gaming Sites, Youth Brands, Spotify, Discord",
                visual_effects=["Color Gradients", "Bouncy Elements", "Playful Icons"],
                design_principles=["Fun Design", "Energetic Feel", "Youth Appeal"]
            ),
            
            # 15. Clean Corporate (Inspired by Enterprise Software)
            LayoutPattern(
                name="clean_corporate",
                type="Clean Corporate Professional",
                grid_system="structured_grid",
                navigation="professional_header",
                hero_style="clean_hero",
                content_flow="section_blocks",
                visual_hierarchy="clear_hierarchy",
                color_approach="professional_blue",
                typography_scale="business_type",
                spacing_system="professional_spacing",
                interactive_elements=["subtle_hover", "smooth_scroll", "form_validation"],
                animation_style="minimal_professional",
                responsive_strategy="business_responsive",
                css_classes=[
                    "bg-white text-gray-900",
                    "border-b border-gray-200 shadow-sm",
                    "py-24 px-8 max-w-7xl mx-auto",
                    "text-blue-600 font-semibold",
                    "hover:bg-blue-50 transition-colors rounded-lg"
                ],
                design_inspiration="Salesforce, Microsoft, Enterprise Software",
                visual_effects=["Clean Lines", "Subtle Shadows", "Professional Polish"],
                design_principles=["Trust", "Clarity", "Professionalism"]
            )
        ]
    
    def get_unique_layout(self, project_type: str = "web_app") -> LayoutPattern:
        """Get a unique layout pattern, ensuring maximum variety across projects."""
        
        # 🎲 ENHANCED RANDOMIZATION: Use timestamp + random for true uniqueness
        seed_value = int(time.time() * 1000) + random.randint(0, 999999)
        random.seed(seed_value)
        
        available_patterns = [p for p in self.layout_patterns if p.name not in self.used_patterns]
        
        # If all patterns used, reset and shuffle
        if not available_patterns:
            self.used_patterns.clear()
            available_patterns = self.layout_patterns.copy()
            random.shuffle(available_patterns)  # Shuffle to get different order each reset
            
        # Select pattern based on project type preferences
        project_type_lower = project_type.lower()
        if any(kw in project_type_lower for kw in ["blog", "magazine", "content", "news"]):
            preferred = [p for p in available_patterns if any(kw in p.name for kw in ["editorial", "minimal", "clean"])]
        elif any(kw in project_type_lower for kw in ["dashboard", "admin", "tool", "saas"]):
            preferred = [p for p in available_patterns if any(kw in p.name for kw in ["brutalist", "grid", "corporate", "minimal"])]
        elif any(kw in project_type_lower for kw in ["portfolio", "creative", "artist", "agency"]):
            preferred = [p for p in available_patterns if any(kw in p.name for kw in ["masonry", "immersive", "asymmetric", "horizontal"])]
        elif any(kw in project_type_lower for kw in ["ecommerce", "shop", "store", "market"]):
            preferred = [p for p in available_patterns if any(kw in p.name for kw in ["glass", "organic", "luxury", "clean"])]
        elif any(kw in project_type_lower for kw in ["gaming", "fun", "kids", "youth"]):
            preferred = [p for p in available_patterns if any(kw in p.name for kw in ["playful", "colorful", "bauhaus"])]
        elif any(kw in project_type_lower for kw in ["luxury", "fashion", "premium"]):
            preferred = [p for p in available_patterns if any(kw in p.name for kw in ["luxury", "glass", "editorial"])]
        else:
            # Random selection for general apps - use full shuffled list
            preferred = available_patterns.copy()
            random.shuffle(preferred)
            
        # Fallback to any available if no preferred found
        if not preferred:
            preferred = available_patterns
            
        # Apply additional randomization before selection
        random.shuffle(preferred)
        selected_pattern = preferred[0]  # Take first after shuffle for true randomness
        self.used_patterns.add(selected_pattern.name)
        
        # Apply dynamic CSS tokenization with unique variations
        selected_pattern = self._apply_dynamic_tokens(selected_pattern)
        
        print(f"🎨 Selected Layout Pattern: {selected_pattern.name} ({selected_pattern.type})")
        print(f"   📐 Grid: {selected_pattern.grid_system}")
        print(f"   🌈 Colors: {selected_pattern.color_approach}")
        print(f"   ✨ Effects: {', '.join(selected_pattern.visual_effects[:2])}")
        print(f"   🏆 Inspiration: {selected_pattern.design_inspiration}")
        
        return selected_pattern
    
    def generate_from_prompt(self, prompt: str) -> Tuple[LayoutPattern, str, Dict[str, str]]:
        """Generate layout based on natural language prompt."""
        print(f"🤖 Processing prompt: '{prompt}'")
        
        # Parse prompt for layout requirements
        layout_requirements = self._parse_layout_prompt(prompt)
        
        # Check if user wants to scrape a specific site
        target_site = self._extract_target_site(prompt)
        if target_site:
            scraped_styles = self._scrape_target_site_styles(target_site)
            layout_requirements.update(scraped_styles)
        
        # Find matching base pattern
        base_pattern = self._find_matching_pattern(layout_requirements)
        
        # Apply prompt-specific modifications
        custom_pattern = self._customize_pattern_from_prompt(base_pattern, layout_requirements)
        
        # Generate custom CSS
        custom_css = self._generate_prompt_css(custom_pattern, layout_requirements)
        
        # Generate custom React components
        custom_components = self._generate_prompt_components(custom_pattern, layout_requirements)
        
        print(f"✅ Generated custom layout: {custom_pattern.type}")
        
        return custom_pattern, custom_css, custom_components
    
    def mix_patterns(self, pattern1_name: str, pattern2_name: str, blend_ratio: float = 0.5) -> Tuple[LayoutPattern, str, Dict[str, str]]:
        """Mix two layout patterns to create a hybrid design."""
        print(f"🎭 Mixing patterns: {pattern1_name} + {pattern2_name} (ratio: {blend_ratio:.1f})")
        
        # Find the patterns
        pattern1 = next((p for p in self.layout_patterns if p.name == pattern1_name), None)
        pattern2 = next((p for p in self.layout_patterns if p.name == pattern2_name), None)
        
        if not pattern1 or not pattern2:
            print(f"❌ Pattern not found. Available: {[p.name for p in self.layout_patterns]}")
            return self.get_unique_layout()
        
        # Create hybrid pattern
        hybrid_pattern = self._blend_patterns(pattern1, pattern2, blend_ratio)
        
        # Generate mixed CSS
        mixed_css = self._generate_mixed_css(pattern1, pattern2, blend_ratio)
        
        # Generate mixed components
        mixed_components = self._generate_mixed_components(pattern1, pattern2, blend_ratio)
        
        print(f"✅ Created hybrid: {hybrid_pattern.type}")
        
        return hybrid_pattern, mixed_css, mixed_components
    
    def _apply_dynamic_tokens(self, pattern: LayoutPattern) -> LayoutPattern:
        """Apply dynamic CSS tokens to make each instance unique."""
        
        # Select random tokens
        accent_color = random.choice(self.css_tokens['accent_colors'])
        neutral_color = random.choice(self.css_tokens['neutral_colors'])
        radius = random.choice(self.css_tokens['radius_values'])
        font_family = random.choice(self.css_tokens['font_families'])
        spacing = random.choice(self.css_tokens['spacing_scales'])
        
        # Create new CSS classes with tokens
        tokenized_classes = []
        for css_class in pattern.css_classes:
            # Replace generic values with tokens
            tokenized_class = css_class
            
            # Replace colors
            if 'bg-blue' in css_class or 'bg-purple' in css_class:
                tokenized_class = re.sub(r'bg-\w+-\d+', f'bg-[{accent_color}]', css_class)
            
            # Replace border radius
            if 'rounded' in css_class:
                tokenized_class = re.sub(r'rounded-\w+', f'rounded-[{radius}]', tokenized_class)
            
            # Replace padding/margin
            if 'p-' in css_class or 'm-' in css_class:
                tokenized_class = re.sub(r'[pm]-\d+', f'p-[{spacing}]', tokenized_class)
                
            tokenized_classes.append(tokenized_class)
        
        # Update pattern with tokenized classes
        pattern.css_classes = tokenized_classes
        pattern.design_inspiration += f" | Tokenized: {accent_color}, {radius}, {font_family.split(',')[0]}"
        
        return pattern
    
    def _parse_layout_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parse natural language prompt for layout requirements."""
        prompt_lower = prompt.lower()
        requirements = {}
        
        # Color detection
        if any(color in prompt_lower for color in ['dark', 'black', 'midnight']):
            requirements['color_scheme'] = 'dark'
        elif any(color in prompt_lower for color in ['light', 'white', 'bright']):
            requirements['color_scheme'] = 'light'
        elif 'futuristic' in prompt_lower:
            requirements['color_scheme'] = 'futuristic'
        elif 'neon' in prompt_lower:
            requirements['color_scheme'] = 'neon'
        
        # Style detection
        if 'glassmorphism' in prompt_lower or 'glass' in prompt_lower:
            requirements['visual_style'] = 'glassmorphism'
        elif 'brutalist' in prompt_lower or 'brutal' in prompt_lower:
            requirements['visual_style'] = 'brutalist'
        elif 'minimal' in prompt_lower or 'clean' in prompt_lower:
            requirements['visual_style'] = 'minimal'
        elif 'organic' in prompt_lower or 'flowing' in prompt_lower:
            requirements['visual_style'] = 'organic'
        
        # Layout type detection
        if 'grid' in prompt_lower:
            requirements['layout_type'] = 'grid'
        elif 'cards' in prompt_lower or 'masonry' in prompt_lower:
            requirements['layout_type'] = 'masonry'
        elif 'fullscreen' in prompt_lower or 'immersive' in prompt_lower:
            requirements['layout_type'] = 'fullscreen'
        
        return requirements
    
    def _extract_target_site(self, prompt: str) -> Optional[str]:
        """Extract target website to scrape from prompt."""
        
        # Common website patterns
        website_patterns = [
            r'like\s+(\w+\.com)',
            r'similar\s+to\s+(\w+\.com)', 
            r'inspired\s+by\s+(\w+\.com)',
            r'(\w+\.com)\s+style',
            r'(\w+\.com)\s+but'
        ]
        
        for pattern in website_patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return match.group(1)
        
        # Known sites
        known_sites = {
            'tesla': 'tesla.com',
            'apple': 'apple.com', 
            'stripe': 'stripe.com',
            'linear': 'linear.app',
            'figma': 'figma.com',
            'github': 'github.com',
            'airbnb': 'airbnb.com',
            'dribbble': 'dribbble.com'
        }
        
        for name, url in known_sites.items():
            if name in prompt.lower():
                return url
                
        return None
    
    def _scrape_target_site_styles(self, target_site: str) -> Dict[str, Any]:
        """Scrape styles from target website (simplified)."""
        print(f"🔍 Analyzing styles from {target_site}...")
        
        # Mock scraped data (in real implementation, would scrape actual site)
        site_styles = {
            'tesla.com': {
                'color_scheme': 'dark_minimal',
                'typography': 'bold_sans_serif',
                'layout': 'fullscreen_sections',
                'animations': 'smooth_parallax'
            },
            'stripe.com': {
                'color_scheme': 'blue_gradients', 
                'typography': 'clean_modern',
                'layout': 'diagonal_sections',
                'animations': 'subtle_motion'
            },
            'linear.app': {
                'color_scheme': 'dark_purple',
                'typography': 'geometric_sans',
                'layout': 'grid_system',
                'animations': 'sharp_transitions'
            }
        }
        
        return site_styles.get(target_site, {})
    
    def _find_matching_pattern(self, requirements: Dict[str, Any]) -> LayoutPattern:
        """Find the best matching base pattern for requirements."""
        
        # Score patterns based on requirements
        pattern_scores = {}
        
        for pattern in self.layout_patterns:
            score = 0
            
            # Color scheme matching
            if requirements.get('color_scheme') == 'dark' and 'dark' in pattern.color_approach.lower():
                score += 3
            elif requirements.get('color_scheme') == 'light' and 'light' in pattern.color_approach.lower():
                score += 3
            
            # Visual style matching
            if requirements.get('visual_style') == 'glassmorphism' and 'glass' in pattern.name:
                score += 5
            elif requirements.get('visual_style') == 'brutalist' and 'brutalist' in pattern.name:
                score += 5
            elif requirements.get('visual_style') == 'minimal' and 'minimal' in pattern.name:
                score += 5
            elif requirements.get('visual_style') == 'organic' and 'organic' in pattern.name:
                score += 5
            
            # Layout type matching
            if requirements.get('layout_type') == 'grid' and 'grid' in pattern.grid_system.lower():
                score += 2
            elif requirements.get('layout_type') == 'masonry' and 'masonry' in pattern.name:
                score += 2
            elif requirements.get('layout_type') == 'fullscreen' and 'fullscreen' in pattern.name:
                score += 2
            
            pattern_scores[pattern] = score
        
        # Return pattern with highest score
        best_pattern = max(pattern_scores.items(), key=lambda x: x[1])[0]
        print(f"   📊 Best match: {best_pattern.name} (score: {pattern_scores[best_pattern]})")
        
        return best_pattern
    
    def _customize_pattern_from_prompt(self, base_pattern: LayoutPattern, requirements: Dict[str, Any]) -> LayoutPattern:
        """Customize pattern based on prompt requirements."""
        
        # Create a copy with modifications
        custom_pattern = LayoutPattern(
            name=f"{base_pattern.name}_custom",
            type=f"Custom {base_pattern.type}",
            grid_system=base_pattern.grid_system,
            navigation=base_pattern.navigation,
            hero_style=base_pattern.hero_style,
            content_flow=base_pattern.content_flow,
            visual_hierarchy=base_pattern.visual_hierarchy,
            color_approach=requirements.get('color_scheme', base_pattern.color_approach),
            typography_scale=base_pattern.typography_scale,
            spacing_system=base_pattern.spacing_system,
            interactive_elements=base_pattern.interactive_elements,
            animation_style=base_pattern.animation_style,
            responsive_strategy=base_pattern.responsive_strategy,
            css_classes=base_pattern.css_classes.copy(),
            design_inspiration=f"Custom: {base_pattern.design_inspiration}",
            visual_effects=base_pattern.visual_effects + ["Prompt-Based", "Custom Styling"],
            design_principles=base_pattern.design_principles + ["User-Requested", "Prompt-Driven"]
        )
        
        return custom_pattern
    
    def _generate_prompt_css(self, pattern: LayoutPattern, requirements: Dict[str, Any]) -> str:
        """Generate CSS based on prompt requirements."""
        
        base_css = self.generate_layout_css(pattern)
        
        # Add prompt-specific CSS
        prompt_css = f"""
/* Prompt-Based Customizations */
:root {{
  --prompt-accent: {random.choice(self.css_tokens['accent_colors'])};
  --prompt-neutral: {random.choice(self.css_tokens['neutral_colors'])};
  --prompt-radius: {random.choice(self.css_tokens['radius_values'])};
  --prompt-spacing: {random.choice(self.css_tokens['spacing_scales'])};
}}

.prompt-container {{
  background: var(--prompt-neutral);
  border-radius: var(--prompt-radius);
  padding: var(--prompt-spacing);
}}

.prompt-accent {{
  color: var(--prompt-accent);
  border-color: var(--prompt-accent);
}}
"""

        if requirements.get('color_scheme') == 'dark':
            prompt_css += """
.dark-theme {{
  background: #111827;
  color: #f9fafb;
}}
"""
        elif requirements.get('color_scheme') == 'futuristic':
            prompt_css += """
.futuristic-theme {{
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  color: #00f5ff;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}}
"""
        
        return base_css + prompt_css
    
    def _generate_prompt_components(self, pattern: LayoutPattern, requirements: Dict[str, Any]) -> Dict[str, str]:
        """Generate React components based on prompt."""
        
        base_components = self.generate_layout_components(pattern)
        
        # Add prompt-specific component
        prompt_component = f'''
const PromptCustom = ({{ children, className = "" }}) => (
  <div className={{`prompt-container ${{className}}`}}>
    {{children}}
  </div>
);

const PromptAccent = ({{ children, className = "" }}) => (
  <span className={{`prompt-accent ${{className}}`}}>
    {{children}}
  </span>
);'''
        
        base_components["PromptComponents"] = prompt_component
        
        return base_components
    
    def _blend_patterns(self, pattern1: LayoutPattern, pattern2: LayoutPattern, blend_ratio: float) -> LayoutPattern:
        """Blend two patterns to create a hybrid."""
        
        # Create hybrid pattern
        hybrid_name = f"{pattern1.name}_{pattern2.name}_hybrid"
        hybrid_type = f"{pattern1.type} + {pattern2.type} Hybrid"
        
        # Blend properties based on ratio
        if blend_ratio > 0.5:
            primary, secondary = pattern1, pattern2
        else:
            primary, secondary = pattern2, pattern1
        
        hybrid_pattern = LayoutPattern(
            name=hybrid_name,
            type=hybrid_type,
            grid_system=f"{primary.grid_system} + {secondary.grid_system}",
            navigation=primary.navigation,  # Take from primary
            hero_style=f"Hybrid: {primary.hero_style}",
            content_flow=f"Mixed: {primary.content_flow}",
            visual_hierarchy=primary.visual_hierarchy,
            color_approach=f"Blended: {primary.color_approach} + {secondary.color_approach}",
            typography_scale=primary.typography_scale,
            spacing_system=primary.spacing_system,
            interactive_elements=primary.interactive_elements + secondary.interactive_elements[:2],
            animation_style=f"Hybrid: {primary.animation_style}",
            responsive_strategy=primary.responsive_strategy,
            css_classes=primary.css_classes + secondary.css_classes[:3],  # Mix CSS classes
            design_inspiration=f"Hybrid: {primary.design_inspiration} + {secondary.design_inspiration}",
            visual_effects=primary.visual_effects + secondary.visual_effects,
            design_principles=primary.design_principles + secondary.design_principles
        )
        
        return hybrid_pattern
    
    def _generate_mixed_css(self, pattern1: LayoutPattern, pattern2: LayoutPattern, blend_ratio: float) -> str:
        """Generate CSS that mixes two patterns."""
        
        css1 = self.generate_layout_css(pattern1)
        css2 = self.generate_layout_css(pattern2)
        
        # Create mixed CSS
        mixed_css = f"""
/* HYBRID LAYOUT: {pattern1.type} + {pattern2.type} */

/* Primary Pattern Elements ({pattern1.name}) */
{css1}

/* Secondary Pattern Elements ({pattern2.name}) */  
{css2}

/* Hybrid Blending */
.hybrid-container {{
  /* Mix of both patterns */
  background: linear-gradient(
    135deg, 
    var(--pattern1-bg, #6366f1) 0%, 
    var(--pattern2-bg, #8b5cf6) 100%
  );
  border-radius: calc(var(--pattern1-radius, 1rem) + var(--pattern2-radius, 1rem)) / 2;
  padding: var(--hybrid-spacing, 2rem);
}}

.hybrid-element {{
  transition: all 0.3s ease;
  transform: translateY(0);
}}

.hybrid-element:hover {{
  transform: translateY(-4px) scale(1.02);
  box-shadow: 
    var(--pattern1-shadow, 0 10px 30px rgba(99, 102, 241, 0.2)),
    var(--pattern2-shadow, 0 20px 40px rgba(139, 92, 246, 0.1));
}}
"""
        
        return mixed_css
    
    def _generate_mixed_components(self, pattern1: LayoutPattern, pattern2: LayoutPattern, blend_ratio: float) -> Dict[str, str]:
        """Generate React components that mix two patterns."""
        
        components1 = self.generate_layout_components(pattern1)
        components2 = self.generate_layout_components(pattern2)
        
        # Create hybrid component
        hybrid_component = f'''
const HybridLayout = ({{ children, variant = "primary" }}) => {{
  const baseClasses = "hybrid-container transition-all duration-300";
  const variantClasses = variant === "primary" 
    ? "{pattern1.css_classes[0] if pattern1.css_classes else 'bg-gradient-to-r from-blue-500 to-purple-600'}"
    : "{pattern2.css_classes[0] if pattern2.css_classes else 'bg-gradient-to-r from-purple-500 to-pink-600'}";
    
  return (
    <div className={{`${{baseClasses}} ${{variantClasses}}`}}>
      {{children}}
    </div>
  );
}};

const HybridCard = ({{ children, className = "" }}) => (
  <div className={{`hybrid-element p-6 rounded-2xl backdrop-blur-sm ${{className}}`}}>
    {{children}}
  </div>
);'''
        
        mixed_components = {**components1, **components2}
        mixed_components["HybridComponents"] = hybrid_component
        
        return mixed_components
    
    def generate_layout_css(self, pattern: LayoutPattern) -> str:
        """Generate custom CSS for the selected layout pattern."""
        css_map = {
            "editorial_magazine": """
/* Editorial Magazine Layout */
.editorial-grid { 
    display: grid; 
    grid-template-columns: 1fr 3fr 1fr; 
    gap: 3rem; 
    min-height: 100vh; 
}
.editorial-hero { 
    grid-column: 1 / -1; 
    font-size: clamp(3rem, 8vw, 8rem); 
    font-weight: 300; 
    line-height: 0.9; 
    letter-spacing: -0.02em; 
}
.editorial-content { 
    font-size: 1.125rem; 
    line-height: 1.8; 
    columns: 2; 
    column-gap: 2rem; 
}
""",
            "brutalist_geometric": """
/* Brutalist Geometric Layout */
.brutalist-grid { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
    gap: 0; 
}
.brutalist-card { 
    aspect-ratio: 1; 
    border: 3px solid #000; 
    background: #fff; 
    transition: all 0.2s ease; 
}
.brutalist-card:hover { 
    background: #000; 
    color: #fff; 
    transform: translate(-5px, -5px); 
    box-shadow: 5px 5px 0 #ff0000; 
}
""",
            "organic_flowing": """
/* Organic Flowing Layout */
.organic-container { 
    border-radius: 3rem; 
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)); 
    backdrop-filter: blur(10px); 
    border: 1px solid rgba(255,255,255,0.18); 
}
.organic-section { 
    border-radius: 2rem; 
    margin: 2rem 0; 
    transform: rotate(-1deg); 
    transition: transform 0.3s ease; 
}
.organic-section:nth-child(even) { 
    transform: rotate(1deg); 
}
.organic-section:hover { 
    transform: rotate(0deg) scale(1.02); 
}
""",
            "diagonal_split": """
/* Diagonal Split Layout */
.diagonal-section { 
    clip-path: polygon(0 0, 100% 0, 85% 100%, 0% 100%); 
    position: relative; 
    overflow: hidden; 
}
.diagonal-section:nth-child(even) { 
    clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); 
}
.diagonal-content { 
    padding: 5rem 3rem; 
    position: relative; 
    z-index: 2; 
}
""",
            "masonry_cards": """
/* Dynamic Masonry Layout */
.masonry-container { 
    columns: 1; 
    column-gap: 1.5rem; 
}
@media (min-width: 768px) { .masonry-container { columns: 2; } }
@media (min-width: 1024px) { .masonry-container { columns: 3; } }
@media (min-width: 1536px) { .masonry-container { columns: 4; } }
.masonry-item { 
    break-inside: avoid; 
    margin-bottom: 1.5rem; 
    transition: transform 0.3s ease, box-shadow 0.3s ease; 
}
.masonry-item:hover { 
    transform: translateY(-8px) scale(1.02); 
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); 
}
""",
            "immersive_fullscreen": """
/* Immersive Full-Screen Layout */
.immersive-section { 
    min-height: 100vh; 
    background-attachment: fixed; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    position: relative; 
}
.immersive-bg { 
    position: absolute; 
    inset: 0; 
    background: radial-gradient(circle at 30% 40%, rgba(120,119,198,0.3), transparent 50%); 
}
.immersive-content { 
    position: relative; 
    z-index: 2; 
    text-align: center; 
}
""",
            "minimalist_grid": """
/* Minimalist Grid Layout */
.minimal-grid { 
    display: grid; 
    grid-template-columns: repeat(12, 1fr); 
    gap: 1px; 
    background: #f5f5f5; 
}
.minimal-cell { 
    background: white; 
    padding: 3rem; 
    transition: background-color 0.2s ease; 
}
.minimal-cell:hover { 
    background: #fafafa; 
}
""",
            "neumorphic_3d": """
/* Neumorphic 3D Layout */
.neumorphic-container { 
    background: #e0e5ec; 
    border-radius: 2rem; 
    box-shadow: 9px 9px 16px #a3b1c6, -9px -9px 16px #ffffff; 
}
.neumorphic-card { 
    background: #e0e5ec; 
    border-radius: 1rem; 
    box-shadow: inset 5px 5px 10px #a3b1c6, inset -5px -5px 10px #ffffff; 
    transition: all 0.3s ease; 
}
.neumorphic-card:hover { 
    box-shadow: 5px 5px 10px #a3b1c6, -5px -5px 10px #ffffff; 
}
""",
            "bauhaus_geometric": """
/* Bauhaus Geometric Layout */
.bauhaus-grid { 
    display: grid; 
    grid-template-columns: repeat(6, 1fr); 
    grid-template-rows: repeat(4, 1fr); 
    height: 100vh; 
    gap: 2px; 
}
.bauhaus-red { 
    background: #ff0000; 
    grid-column: span 2; 
    grid-row: span 2; 
}
.bauhaus-blue { 
    background: #0066cc; 
    grid-column: span 3; 
}
.bauhaus-yellow { 
    background: #ffcc00; 
    grid-row: span 3; 
}
""",
            "glassmorphism_layers": """
/* Glassmorphism Layers Layout */
.glass-container { 
    backdrop-filter: blur(16px) saturate(180%); 
    background-color: rgba(255, 255, 255, 0.1); 
    border: 1px solid rgba(255, 255, 255, 0.125); 
    border-radius: 1rem; 
}
.glass-card { 
    backdrop-filter: blur(20px); 
    background: rgba(255, 255, 255, 0.08); 
    border: 1px solid rgba(255, 255, 255, 0.2); 
    transition: all 0.3s ease; 
}
.glass-card:hover { 
    background: rgba(255, 255, 255, 0.15); 
    backdrop-filter: blur(25px); 
}
"""
        }
        
        return css_map.get(pattern.name, "/* Default CSS */")
    
    def generate_layout_components(self, pattern: LayoutPattern) -> Dict[str, str]:
        """Generate React components specific to the layout pattern."""
        
        components = {
            "editorial_magazine": {
                "Hero": '''
const Hero = ({ title, subtitle }) => (
  <div className="editorial-hero py-24 px-12 border-b border-gray-200">
    <h1 className="text-8xl font-light leading-none tracking-tight text-gray-900 mb-8">
      {title}
    </h1>
    <p className="text-xl text-gray-600 max-w-2xl leading-relaxed">
      {subtitle}
    </p>
  </div>
);''',
                "ContentGrid": '''
const ContentGrid = ({ children }) => (
  <div className="editorial-grid px-12 py-16">
    <div className="col-span-1"></div>
    <div className="col-span-2 editorial-content text-gray-800">
      {children}
    </div>
    <div className="col-span-1"></div>
  </div>
);'''
            },
            
            "brutalist_geometric": {
                "GeometricCard": '''
const GeometricCard = ({ title, content, onClick }) => (
  <div 
    className="brutalist-card p-8 cursor-pointer font-mono uppercase tracking-wider"
    onClick={onClick}
  >
    <h3 className="text-2xl font-bold mb-4">{title}</h3>
    <p className="text-sm">{content}</p>
  </div>
);''',
                "BrutalistGrid": '''
const BrutalistGrid = ({ items }) => (
  <div className="brutalist-grid min-h-screen bg-white">
    {items.map((item, index) => (
      <GeometricCard 
        key={index}
        title={item.title}
        content={item.content}
        onClick={item.onClick}
      />
    ))}
  </div>
);'''
            },
            
            "glassmorphism_layers": {
                "GlassCard": '''
const GlassCard = ({ children, className = "" }) => (
  <div className={`glass-card p-8 rounded-2xl ${className}`}>
    {children}
  </div>
);''',
                "FloatingNav": '''
const FloatingNav = ({ items }) => (
  <nav className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50">
    <div className="glass-container px-6 py-3 rounded-full">
      <div className="flex space-x-8">
        {items.map((item, index) => (
          <a 
            key={index}
            href={item.href}
            className="text-white/80 hover:text-white transition-colors"
          >
            {item.label}
          </a>
        ))}
      </div>
    </div>
  </nav>
);'''
            }
        }
        
        return components.get(pattern.name, {})

# Global layout system instance
layout_system = AdvancedLayoutSystem()

def get_diverse_layout_for_project(project_type: str = "web_app", prompt: str = None) -> Tuple[LayoutPattern, str, Dict[str, str]]:
    """
    Get a unique layout pattern with CSS and components for a project.
    
    Args:
        project_type: Type of project (web_app, ecommerce, blog, etc.)
        prompt: Optional natural language prompt for custom layouts
    
    Returns:
        Tuple of (layout_pattern, custom_css, react_components)
    """
    if prompt:
        # Use prompt-based generation
        return layout_system.generate_from_prompt(prompt)
    
    pattern = layout_system.get_unique_layout(project_type)
    css = layout_system.generate_layout_css(pattern)
    components = layout_system.generate_layout_components(pattern)
    
    return pattern, css, components

def generate_layout_from_prompt(prompt: str) -> Tuple[LayoutPattern, str, Dict[str, str]]:
    """
    Generate a completely custom layout based on natural language prompt.
    
    Example prompts:
    - "Generate a dark futuristic layout like Tesla.com but with glassmorphism"
    - "Create a minimal blog layout with soft shadows and organic curves"
    - "Make a brutalist e-commerce site with neon accents"
    
    Returns:
        Tuple of (layout_pattern, custom_css, react_components)
    """
    return layout_system.generate_from_prompt(prompt)

def mix_layout_patterns(pattern1: str, pattern2: str, blend_ratio: float = 0.5) -> Tuple[LayoutPattern, str, Dict[str, str]]:
    """
    Mix two existing layout patterns to create a hybrid design.
    
    Args:
        pattern1: Name of first pattern (e.g., 'brutalist_geometric')
        pattern2: Name of second pattern (e.g., 'glassmorphism_layers') 
        blend_ratio: How much to favor pattern1 (0.0 = all pattern2, 1.0 = all pattern1)
    
    Returns:
        Tuple of (hybrid_pattern, mixed_css, mixed_components)
    """
    return layout_system.mix_patterns(pattern1, pattern2, blend_ratio)

def scrape_live_design_trends() -> List[Any]:
    """
    Scrape live design trends from award-winning sites.
    
    Returns:
        List of DesignTrend objects with real-time data
    """
    from design_trend_scraper import DesignTrendScraper
    scraper = DesignTrendScraper()
    return scraper.scrape_live_design_data()

def get_available_patterns() -> List[str]:
    """Get list of all available layout pattern names for mixing."""
    return [pattern.name for pattern in layout_system.layout_patterns]

def preview_pattern_mix(pattern1: str, pattern2: str) -> Dict[str, Any]:
    """Preview what mixing two patterns would look like without generating full CSS."""
    
    p1 = next((p for p in layout_system.layout_patterns if p.name == pattern1), None)
    p2 = next((p for p in layout_system.layout_patterns if p.name == pattern2), None)
    
    if not p1 or not p2:
        return {"error": "Pattern not found"}
    
    return {
        "hybrid_name": f"{p1.name}_{p2.name}_hybrid",
        "hybrid_type": f"{p1.type} + {p2.type}",
        "color_blend": f"{p1.color_approach} + {p2.color_approach}",
        "grid_system": f"{p1.grid_system} + {p2.grid_system}",
        "visual_effects": p1.visual_effects + p2.visual_effects,
        "inspiration": f"{p1.design_inspiration} + {p2.design_inspiration}"
    }