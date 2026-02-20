from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a blue rounded image
    size = (256, 256)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue background
    blue_color = (37, 99, 235, 255) # Tailwind blue-600
    
    # Background (rounded rectangle)
    margin = 16
    draw.rounded_rectangle(
        [(margin, margin), (size[0]-margin, size[1]-margin)], 
        radius=40, 
        fill=blue_color
    )
    
    # Add "NC" text in white
    text = "NC"
    
    # Try to load a nice font, fallback to default
    try:
        font = ImageFont.truetype("arialbd.ttf", 100)
    except:
        font = ImageFont.load_default()
        
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    x = (size[0] - w) / 2
    y = (size[1] - h) / 2 - 10 # slightly shift up for visual centering
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    img.save("app_icon.png")
    img.save("app_icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print("Icons generated successfully.")

if __name__ == "__main__":
    create_icon()
