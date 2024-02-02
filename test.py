from PIL import ImageFont

# Load the font
font_path = "regular-font.otf"
font_size = 20
font = ImageFont.truetype(font_path, font_size)

# Measure text size
overlay_text = "Your Text Here"
textwidth, textheight = font.getsize(overlay_text)
