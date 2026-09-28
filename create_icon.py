from PIL import Image, ImageDraw
import os

# Create a clean purple/burgundy icon matching the MusicPlayer theme
# Color palette from style.qss: Primary #c94f7c, PrimaryGlow #e86b9a, PrimaryBright #f08ab8
# Background: #0f0f11, Surface: #140a18

sizes = [16, 24, 32, 48, 64, 128, 256]
images = []

for size in sizes:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle with gradient-like effect
    margin = max(1, size // 16)
    # Dark background circle
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#0f0f11', outline='#2a1020', width=max(1, size//32))
    
    # Inner accent ring
    inner_margin = margin + max(1, size // 20)
    draw.ellipse([inner_margin, inner_margin, size-inner_margin, size-inner_margin], outline='#c94f7c', width=max(1, size//24))
    
    # Music note symbol - simplified
    center = size // 2
    note_size = size // 2.5
    
    # Draw a music note using rectangles and circles
    # Stem
    stem_x = center + size // 10
    stem_top = center - note_size // 2
    stem_bottom = center + note_size // 3
    stem_width = max(1, size // 20)
    draw.rectangle([stem_x, stem_top, stem_x + stem_width, stem_bottom], fill='#f08ab8')
    
    # Flag/beam
    flag_top = stem_top
    flag_right = stem_x + stem_width + size // 8
    draw.polygon([
        (stem_x + stem_width, flag_top),
        (flag_right, flag_top + size // 16),
        (flag_right, flag_top + size // 6),
        (stem_x + stem_width, flag_top + size // 8)
    ], fill='#f08ab8')
    
    # Lower note head (filled circle)
    head_radius = max(2, size // 12)
    head_y = stem_bottom
    head_x = stem_x + stem_width // 2
    draw.ellipse([head_x - head_radius, head_y - head_radius, head_x + head_radius, head_y + head_radius], fill='#e86b9a')
    
    # Upper note head
    head_y2 = stem_top + size // 10
    draw.ellipse([head_x - head_radius, head_y2 - head_radius, head_x + head_radius, head_y2 + head_radius], fill='#e86b9a')
    
    images.append(img)

# Save as ICO with multiple sizes
output_path = r'E:\playground\Projects\music-player\assets\MusicPlayer.ico'
images[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in images])
print(f'Created icon at {output_path} with sizes: {[f"{img.width}x{img.height}" for img in images]}')