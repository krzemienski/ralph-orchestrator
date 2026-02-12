#!/usr/bin/env python3
"""
Generate app icon images programmatically following the design specification.
Uses PIL/Pillow to create PNG files at all required sizes.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Color palette from CyberpunkTheme
COLORS = {
    'bg_primary': (3, 3, 6),
    'bg_secondary': (7, 7, 12),
    'bg_elevated': (14, 14, 22),
    'accent_cyan': (0, 255, 242),
    'accent_magenta': (255, 0, 255),
    'border': (26, 26, 46)
}

# Icon sizes (size, filename)
ICON_SIZES = [
    (1024, 'Icon-1024'),
    (180, 'Icon-60@3x'),
    (120, 'Icon-60@2x'),
    (120, 'Icon-40@3x'),
    (80, 'Icon-40@2x'),
    (87, 'Icon-29@3x'),
    (58, 'Icon-29@2x'),
    (60, 'Icon-20@3x'),
    (40, 'Icon-20@2x'),
    (167, 'Icon-83.5@2x'),
    (152, 'Icon-76@2x'),
    (76, 'Icon-76@1x'),
    (80, 'Icon-40@2x-1'),
    (40, 'Icon-40@1x'),
    (58, 'Icon-29@2x-1'),
    (29, 'Icon-29@1x'),
    (40, 'Icon-20@2x-1'),
    (20, 'Icon-20@1x')
]

def create_gradient_color(color1, color2, position):
    """Interpolate between two colors."""
    r = int(color1[0] + (color2[0] - color1[0]) * position)
    g = int(color1[1] + (color2[1] - color1[1]) * position)
    b = int(color1[2] + (color2[2] - color1[2]) * position)
    return (r, g, b)

def add_glow(draw, xy, radius, color, blur_radius):
    """Add a glow effect around a shape."""
    for i in range(blur_radius):
        alpha = int(255 * (1 - i / blur_radius) * 0.3)
        current_color = color + (alpha,)
        draw.ellipse(
            [xy[0] - radius - i, xy[1] - radius - i,
             xy[0] + radius + i, xy[1] + radius + i],
            outline=current_color,
            width=2
        )

def generate_icon(size):
    """Generate a single app icon at the specified size."""
    # Create image with RGBA mode for transparency effects
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    # Layer 1: Background with radial gradient
    for y in range(size):
        for x in range(size):
            dist = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
            max_dist = (size / 2)
            gradient_pos = min(dist / max_dist, 1.0)
            color = create_gradient_color(COLORS['bg_secondary'], COLORS['bg_primary'], gradient_pos)
            img.putpixel((x, y), color + (255,))

    # Layer 2: Glass ring with gradient
    ring_outer_radius = int(size * 0.375)
    ring_thickness = int(size * 0.08)
    ring_inner_radius = ring_outer_radius - ring_thickness

    # Draw ring segments with gradient
    for angle in range(360):
        for r in range(ring_inner_radius, ring_outer_radius):
            import math
            x = int(center + r * math.cos(math.radians(angle)))
            y = int(center + r * math.sin(math.radians(angle)))
            if 0 <= x < size and 0 <= y < size:
                # Gradient from cyan to magenta
                gradient_pos = angle / 360.0
                color = create_gradient_color(COLORS['accent_cyan'], COLORS['accent_magenta'], gradient_pos)
                alpha = int(180)  # 70% opacity
                img.putpixel((x, y), color + (alpha,))

    # Layer 3: Inner glass surface
    inner_radius = int(size * 0.3)
    draw.ellipse(
        [center - inner_radius, center - inner_radius,
         center + inner_radius, center + inner_radius],
        fill=COLORS['bg_elevated'] + (240,),
        outline=COLORS['accent_cyan'] + (51,),
        width=max(1, int(size * 0.005))
    )

    # Layer 4: "R" symbol
    # Use a large font size
    try:
        # Try to use a bold system font
        font_size = int(size * 0.5)
        font = ImageFont.truetype("/System/Library/Fonts/SFNSRounded.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw "R" with gradient (simplified - using solid color)
    text = "R"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center - text_width // 2
    text_y = center - text_height // 2 - int(size * 0.05)

    # Glow effects (multiple layers)
    for offset in [12, 8, 4]:
        if size < 100:
            offset = offset // 4
        glow_color = COLORS['accent_cyan'] + (int(255 * 0.3),)
        draw.text((text_x + offset//4, text_y + offset//4), text, font=font, fill=glow_color)
        glow_color = COLORS['accent_magenta'] + (int(255 * 0.2),)
        draw.text((text_x - offset//4, text_y + offset//4), text, font=font, fill=glow_color)

    # Main text with gradient (using cyan as primary color)
    draw.text((text_x, text_y), text, font=font, fill=COLORS['accent_cyan'])

    # Layer 5: Accent indicators (3 small bars)
    bar_width = int(size * 0.08)
    bar_height = int(size * 0.015)
    bar_spacing = int(size * 0.015)
    bar_y = center + int(size * 0.15)

    total_width = (bar_width * 3) + (bar_spacing * 2)
    start_x = center - total_width // 2

    for i in range(3):
        bar_x = start_x + i * (bar_width + bar_spacing)
        # Draw rounded rectangle (capsule)
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
            radius=bar_height // 2,
            fill=COLORS['accent_cyan'] + (204,)  # 80% opacity
        )

    return img

def main():
    """Generate all app icon sizes."""
    output_dir = 'RalphMobile/RalphMobile/Assets.xcassets/AppIcon.appiconset'
    os.makedirs(output_dir, exist_ok=True)

    print("🎨 Ralph Mobile App Icon Generator")
    print("━" * 50)

    for size, filename in ICON_SIZES:
        print(f"📱 Generating {filename}.png ({size}x{size})...")
        icon = generate_icon(size)
        output_path = os.path.join(output_dir, f"{filename}.png")
        icon.save(output_path, 'PNG')
        print(f"   ✓ Saved to {output_path}")

    print("━" * 50)
    print(f"✅ Generated {len(ICON_SIZES)} app icons successfully!")
    print(f"📁 Location: {output_dir}")

if __name__ == '__main__':
    main()
