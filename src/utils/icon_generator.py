import os
from PIL import Image, ImageDraw

def ensure_assets_exist(assets_dir: str):
    """Ensures the existence of the assets folder and default icons."""
    os.makedirs(assets_dir, exist_ok=True)
    ico_path = os.path.join(assets_dir, "icon.ico")
    png_path = os.path.join(assets_dir, "icon.png")

    if not os.path.exists(ico_path) or not os.path.exists(png_path):
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Draw battery
        draw.rectangle([10, 15, 50, 49], outline="#00E676", width=4)
        draw.rectangle([50, 25, 54, 39], fill="#00E676")
        draw.rectangle([16, 21, 44, 43], fill="#00E676")

        if not os.path.exists(ico_path):
            img.save(ico_path, format="ICO", sizes=[(64, 64)])
        if not os.path.exists(png_path):
            img.save(png_path, format="PNG")