from PIL import Image

# Вспомогательные функции
def get_pixel(data, x, y, width, channels):
    idx = (y * width + x) * channels
    if channels == 1:   return (data[idx],)
    else:   return (data[idx], data[idx+1], data[idx+2])

def set_pixel(data, x, y, width, channels, values):
    idx = (y * width + x) * channels
    for i in range(channels):
        data[idx + i] = values[i]

def downsample(img_bytes, width, height, channels):
    new_w = width // 2
    new_h = height // 2
    new_data = bytearray(new_w * new_h * channels)

    for y in range(new_h):
        for x in range(new_w):
            src_x = x * 2
            src_y = y * 2
            pixel = get_pixel(img_bytes, src_x, src_y, width, channels)
            set_pixel(new_data, x, y, new_w, channels, pixel)

    return bytes(new_data), new_w, new_h

def upsample(img_bytes, width, height, channels):
    new_w = width * 2
    new_h = height * 2
    new_data = bytearray(new_w * new_h * channels)

    for y in range(height):
        for x in range(width):
            pixel = get_pixel(img_bytes, x, y, width, channels)
            for dy in range(2):
                for dx in range(2):
                    set_pixel(new_data, x*2+dx, y*2+dy, new_w, channels, pixel)

    return bytes(new_data), new_w, new_h

# Линейная интерполяция между двумя точками
def linear_interpolation(x1, x2, y1, y2, x):
    k = (y2 - y1) / (x2 - x1)
    y = y1 + k * (x - x1)
    return y

# Вычисление значения линейного сплайна в заданных координатах
def linear_spline(x_points, y_points, x):
    n = len(x_points)
    i = 0
    while i < n - 1 and x > x_points[i+1]:
        i = i + 1

    if i == n - 1:
        i = n - 2
    if x <= x_points[0]:
        i = 0

    return linear_interpolation(x_points[i], x_points[i+1], y_points[i], y_points[i+1], x)

# Билинейная интерполяция для четырёх точек
def bilinear_interpolation(x1, x2, y1, y2, z11, z12, z21, z22, x, y):
    z_y1 = linear_interpolation(x1, x2, z11, z21, x)
    z_y2 = linear_interpolation(x1, x2, z12, z22, x)
    return linear_interpolation(y1, y2, z_y1, z_y2, y)

# Изменение размера с билинейной интерполяцией
def resize_bilinear(img_bytes, width, height, channels, new_width, new_height):
    # Вход: байты пикселей, ширина, высота, число каналов, новая ширина, новая высота.
    # Выход: байты нового изображения.

    new_data = bytearray(new_width * new_height * channels)

    # Масштабные коэффициенты
    scale_x = float(width) / new_width
    scale_y = float(height) / new_height

    for dst_y in range(new_height):
        # Координата в исходном изображении (центр пикселя)
        src_y = (dst_y + 0.5) * scale_y - 0.5
        y1 = int(src_y)
        if y1 < 0:  y1 = 0
        y2 = y1 + 1
        if y2 >= height:    y2 = height - 1
        dy = src_y - y1
        if dy < 0:  dy = 0.0
        if dy > 1:  dy = 1.0

        for dst_x in range(new_width):
            src_x = (dst_x + 0.5) * scale_x - 0.5
            x1 = int(src_x)
            if x1 < 0:  x1 = 0
            x2 = x1 + 1
            if x2 >= width: x2 = width - 1
            dx = src_x - x1
            if dx < 0:  dx = 0.0
            if dx > 1:  dx = 1.0

            # Получаем значения четырёх соседних пикселей
            p11 = get_pixel(img_bytes, x1, y1, width, channels)
            p12 = get_pixel(img_bytes, x1, y2, width, channels)
            p21 = get_pixel(img_bytes, x2, y1, width, channels)
            p22 = get_pixel(img_bytes, x2, y2, width, channels)

            # Интерполируем каждый канал отдельно
            new_pixel = []
            for c in range(channels):
                val = bilinear_interpolation(
                    0.0, 1.0, 0.0, 1.0,
                    p11[c], p12[c], p21[c], p22[c],
                    dx, dy
                )
                # Округляем и клиппим
                v = int(round(val))
                if v < 0:
                    v = 0
                if v > 255:
                    v = 255
                new_pixel.append(v)

            set_pixel(new_data, dst_x, dst_y, new_width, channels, new_pixel)

    return bytes(new_data)

img = Image.open("color_image.png")
if img.width < 512 or img.height < 512:
    img = img.resize((512, 512), Image.BILINEAR)
if img.mode != 'RGB':
    img = img.convert('RGB')

width = img.width
height = img.height
channels = 3
pixels = img.tobytes()

print("Исходный размер: %dx%d" % (width, height))

# Даунсэмплинг
down_pixels, down_w, down_h = downsample(pixels, width, height, channels)
print("После даунсэмплинга: %dx%d" % (down_w, down_h))

# Апсемплинг (дублированием)
up_pixels, up_w, up_h = upsample(down_pixels, down_w, down_h, channels)
print("После апсемплинга (дублирование): %dx%d" % (up_w, up_h))

# Сохраняем уменьшенное и увеличенное изображения для сранения
img_down = Image.frombytes('RGB', (down_w, down_h), down_pixels)
img_down.save("downsampled.png")

img_up = Image.frombytes('RGB', (up_w, up_h), up_pixels)
img_up.save("upsampled_duplication.png")

print("Сохранены: downsampled.png (уменьшенное в 2 раза)")
print("           upsampled_duplication.png (увеличенное обратно дублированием - видны пиксели)")

# Проверка билинейной интерполяции на небольшом примере
x1, x2 = 0.0, 1.0
y1, y2 = 0.0, 1.0
z11 = 10.0
z12 = 20.0
z21 = 30.0
z22 = 40.0
x, y = 0.5, 0.5
val = bilinear_interpolation(x1, x2, y1, y2, z11, z12, z21, z22, x, y)
print("Билинейная интерполяция в центре: %.2f (ожидалось 25.0)" % val)

# Уменьшим изображение
new_w = 400
new_h = 300
resized_pixels = resize_bilinear(pixels, width, height, channels, new_w, new_h)
img_resized = Image.frombytes('RGB', (new_w, new_h), resized_pixels)
img_resized.save("resized_bilinear.png")
print("Сохранено resized_bilinear.png (изменение размера билинейной интерполяцией до %dx%d)" % (new_w, new_h))

# Увеличим изображение
new_w2 = 800
new_h2 = 800
resized_pixels2 = resize_bilinear(pixels, width, height, channels, new_w2, new_h2)
img_resized2 = Image.frombytes('RGB', (new_w2, new_h2), resized_pixels2)
img_resized2.save("resized_bilinear_up.png")
print("Сохранено resized_bilinear_up.png (увеличение до %dx%d)" % (new_w2, new_h2))