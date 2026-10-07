from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_crisp_dt_icon():
    os.makedirs('assets', exist_ok=True)
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 255))
    try:
        font = ImageFont.truetype("arialbd.ttf", 150)
    except:
        font = ImageFont.load_default()

    # Create a base for glow
    glow_layer = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d_glow = ImageDraw.Draw(glow_layer)
    d_glow.text((128, 128), "DT", font=font, fill=(255, 255, 255, 200), anchor="mm")
    glow = glow_layer.filter(ImageFilter.GaussianBlur(3))
    
    # Draw crisp text on top
    text_layer = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d_text = ImageDraw.Draw(text_layer)
    d_text.text((128, 128), "DT", font=font, fill=(255, 255, 255, 255), anchor="mm")

    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, text_layer)

    img.save('assets/icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print("Crisp icon generated.")

if __name__ == "__main__":
    create_crisp_dt_icon()
