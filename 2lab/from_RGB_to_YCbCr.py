from PIL import Image
from prepare_images import save_raw, save_raw_from_bytes

def rgb_to_ycbcr(rgb_bytes):
    n = len(rgb_bytes) // 3
    ycbcr = bytearray()
    for i in range(n):
        r = rgb_bytes[i*3]
        g = rgb_bytes[i*3+1]
        b = rgb_bytes[i*3+2]
        y  = 0.299 * r + 0.587 * g + 0.114 * b
        cb = 128.0 - 0.168736 * r - 0.331264 * g + 0.5 * b
        cr = 128.0 + 0.5 * r - 0.418688 * g - 0.081312 * b
        Y = max(0, min(255, int(round(y))))
        Cb = max(0, min(255, int(round(cb))))
        Cr = max(0, min(255, int(round(cr))))
        ycbcr.append(Y)
        ycbcr.append(Cb)
        ycbcr.append(Cr)
    return bytes(ycbcr)

def ycbcr_to_rgb(ycbcr_bytes):
    n = len(ycbcr_bytes) // 3
    rgb = bytearray()
    for i in range(n):
        Y  = ycbcr_bytes[i*3]
        Cb = ycbcr_bytes[i*3+1]
        Cr = ycbcr_bytes[i*3+2]
        r = Y + 1.402 * (Cr - 128.0)
        g = Y - 0.344136 * (Cb - 128.0) - 0.714136 * (Cr - 128.0)
        b = Y + 1.772 * (Cb - 128.0)
        R = max(0, min(255, int(round(r))))
        G = max(0, min(255, int(round(g))))
        B = max(0, min(255, int(round(b))))
        rgb.append(R)
        rgb.append(G)
        rgb.append(B)
    return bytes(rgb)

if __name__ == "__main__":
    img_rgb = Image.open("color_image.png").convert('RGB')
    rgb_data = img_rgb.tobytes()
    ycbcr_data = rgb_to_ycbcr(rgb_data)
    rgb_data2 = ycbcr_to_rgb(ycbcr_data)

    img_restored = Image.frombytes('RGB', img_rgb.size, rgb_data2)
    img_restored.save("restored_rgb.png")
    print("Восстановленное изображение сохранено: restored_rgb.png")

    # Сохраняем raw для RGB
    save_raw(img_rgb, "color_rgb.raw", colorspace=0)

    # Сохраняем raw для YCbCr
    save_raw_from_bytes(
        pixel_bytes=ycbcr_data,
        width=img_rgb.width,
        height=img_rgb.height,
        img_type=2,
        colorspace=1,
        filename="color_ycbcr.raw"
    )

    print("Raw-файлы color_rgb.raw и color_ycbcr.raw созданы.")