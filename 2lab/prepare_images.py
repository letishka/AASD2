import os
from PIL import Image

def save_raw_from_bytes(pixel_bytes, width, height, img_type, colorspace, filename):
    """Запись raw с 6-байтовым заголовком."""
    header = bytearray()
    header.append(img_type)
    header.append(colorspace)
    header.append((width >> 8) & 0xFF)
    header.append(width & 0xFF)
    header.append((height >> 8) & 0xFF)
    header.append(height & 0xFF)
    f = open(filename, 'wb')
    f.write(header)
    f.write(pixel_bytes)

def save_raw(img, filename, colorspace=0):

    mode = img.mode
    if mode == '1':
        img_type = 0
    elif mode == 'L':
        img_type = 1
    else:
        img_type = 2
    w, h = img.size
    save_raw_from_bytes(img.tobytes(), w, h, img_type, colorspace, filename)

if __name__ == "__main__":

    lena_img = Image.open("Lenna.png")
    color_img = Image.open("color_image.png")

    grey_img = color_img.convert('L')
    grey_img.save("grey_image.png")

    bw_no_dither = color_img.convert('1', dither=Image.Dither.NONE)
    bw_no_dither.save("bw_no_dither.png")

    bw_dither = color_img.convert('1')
    bw_dither.save("bw_dither.png")

    print("Производные изображения созданы.\n")

    # --- список: (PIL image, выходной raw, исходный файл для сравнения) ---
    specs = [
        (lena_img,      "Lenna.raw",        "Lenna.png"),
        (color_img,     "color.raw",        "color_image.png"),
        (grey_img,      "grey.raw",         "grey_image.png"),
        (bw_no_dither,  "bw_no_dither.raw", "bw_no_dither.png"),
        (bw_dither,     "bw_dither.raw",    "bw_dither.png"),
    ]

    print("Коэффициенты сжатия (исходник / raw-файл):\n")

    for img, raw_name, orig_name in specs:
        save_raw(img, raw_name, colorspace=0)
        orig_sz = os.path.getsize(orig_name)
        raw_sz = os.path.getsize(raw_name)
        ratio = orig_sz / raw_sz if raw_sz else 0
        print(f"Файл: {raw_name}")
        print(f"  Исходный размер: {orig_sz} байт")
        print(f"  Raw размер:      {raw_sz} байт")
        print(f"  Коэф. сжатия:    {ratio:.3f}\n")

    print("Raw-файлы готовы.")