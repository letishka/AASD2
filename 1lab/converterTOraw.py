import os
import struct
from PIL import Image


def pack_bits(pixels):
    # Упаковывает список пикселей (значения 0 или 255) в байты.
    # Каждый байт содержит до 8 бит: первый пиксель попадает в старший бит.
    # Если количество пикселей не кратно 8, последний байт дополняется нулями.
    bits = [1 if p else 0 for p in pixels]
    data = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        byte = 0
        for j in range(8):
            if j < len(chunk) and chunk[j]:
                byte |= 1 << (7 - j)
        data.append(byte)
    return bytes(data)


def convert_to_raw(file_way, ms=None, mc=None):
    # Заголовок (5 байт):
    #   - тип (1 байт): 0 – ч/б, 1 – оттенки серого, 2 – цветное
    #   - ms (2 байта, little-endian) – размер символа в битах
    #   - mc (2 байта, little-endian) – размер управляющего слова в битах
    # После заголовка идут пиксельные данные.
    img = Image.open(file_way)

    # Определяем тип изображения
    if img.mode == '1':
        img_type = 0
    elif img.mode == 'L':
        img_type = 1
    else:
        img = img.convert('RGB')
        img_type = 2

    # Для типа 0 всегда используем 1 бит на пиксель
    if img_type == 0:
        ms = 1
    elif ms is None:
        ms = 8 if img_type == 1 else 24

    if mc is None:
        mc = 16

    # Получаем пиксельные данные
    if img_type == 0:
        # Упаковываем бинарное изображение в биты (передаём список, чтобы анализатор не ругался)
        data = pack_bits(list(img.getdata()))
    elif img_type == 1:
        data = img.tobytes()
    else:
        data = img.tobytes()

    # Формируем заголовок: тип (1) + ms (2) + mc (2) = 5 байт
    header = struct.pack('<BHH', img_type, ms, mc)

    with open(f'{file_way}.raw', 'wb') as f:
        f.write(header)
        f.write(data)


def compare(file_way):
    # Сравнивает размер исходного изображения и полученного .raw.
    print(f"Файл: {file_way}")
    print(f"  Исходный размер: {os.path.getsize(file_way)} байт")
    print(f"  Raw размер:      {os.path.getsize(f'{file_way}.raw')} байт")
    print(f"  Коэф. сжатия (исх/raw): {os.path.getsize(file_way) / os.path.getsize(f'{file_way}.raw'):.3f}\n")


if __name__ == '__main__':
    # Пример использования – можно задать Ms и Mc явно
    convert_to_raw('bw_photo.png')
    convert_to_raw('grey_photo.jpg')
    convert_to_raw('color_photo.avif')

    compare('bw_photo.png')
    compare('grey_photo.jpg')
    compare('color_photo.avif')