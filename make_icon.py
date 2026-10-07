from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_dt_icon():
    os.makedirs('assets', exist_ok=True)
    
    # 256x256 base
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 255))
    
    try:
        font = ImageFont.truetype("arialbd.ttf", 120)
    except:
        font = ImageFont.load_default()

    # Draw DT on a transparent layer
    txt_layer = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(txt_layer)
    
    # Text in the middle
    d2.text((128, 128), "DT", font=font, fill=(255, 255, 255, 255), anchor="mm")
    
    # Create glow layers
    glow1 = txt_layer.filter(ImageFilter.GaussianBlur(15))
    glow2 = txt_layer.filter(ImageFilter.GaussianBlur(5))
    
    # Composite
    img = Image.alpha_composite(img, glow1)
    img = Image.alpha_composite(img, glow2)
    img = Image.alpha_composite(img, txt_layer)
    
    img.save('assets/icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print("Icon generated.")

if __name__ == "__main__":
    create_dt_icon()
