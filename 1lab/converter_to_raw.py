import os
import struct
from PIL import Image

def convert_to_myraw(file_way, Ms=None, Mc=None):
    """
    Конвертирует изображение в собственный raw-формат (.myraw).
    Заголовок (5 байт):
      - тип (1 байт): 0 – ч/б, 1 – оттенки серого, 2 – цветное
      - Ms (2 байта, little-endian) – размер символа в битах
      - Mc (2 байта, little-endian) – размер управляющего слова в битах
    После заголовка идут пиксельные данные.
    """
    img = Image.open(file_way)

    # Определяем тип изображения
    if img.mode == '1':
        img_type = 0
    elif img.mode == 'L':
        img_type = 1
    else:
        img = img.convert('RGB')
        img_type = 2

    # Получаем пиксельные данные
    if img_type in (0, 1):
        data = bytes(img.getdata())
    else:
        data = img.tobytes()

    # Если Ms не задан, выбираем по умолчанию:
    # для ч/б и серого – 8 бит, для цветного – 24 бита
    if Ms is None:
        Ms = 8 if img_type in (0, 1) else 24
    if Mc is None:
        Mc = 16   # разумное значение по умолчанию

    # Формируем заголовок: тип (1) + Ms (2) + Mc (2) = 5 байт
    header = struct.pack('<BHH', img_type, Ms, Mc)

    with open(f'{file_way}.myraw', 'wb') as f:
        f.write(header)
        f.write(data)


def compare(file_way):
    """Сравнивает размер исходного изображения и полученного .myraw."""
    print(f"Файл: {file_way}")
    print(f"  Исходный размер: {os.path.getsize(file_way)} байт")
    print(f"  Raw размер:      {os.path.getsize(f'{file_way}.myraw')} байт")
    print(f"  Коэф. сжатия (исх/raw): {os.path.getsize(file_way) / os.path.getsize(f'{file_way}.myraw'):.3f}\n")


if __name__ == '__main__':
    # Пример использования – можно задать Ms и Mc явно
    convert_to_myraw('bw_photo.png', Ms=8, Mc=16)
    convert_to_myraw('grey_photo.jpg', Ms=8, Mc=16)
    convert_to_myraw('color_photo.avif', Ms=24, Mc=16)

    compare('bw_photo.png')
    compare('grey_photo.jpg')
    compare('color_photo.avif')