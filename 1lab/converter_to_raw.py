# для добычи информации изображений
from PIL import Image

# для записи заголовка
import struct

# для сравнения форматов изображений
import os

def convert_to_myraw(file_way):

    # открытие файла
    file = Image.open(file_way)

    # определение типа изображения
    if file.mode == '1':
        img_type = 0
    elif file.mode == 'L':
        img_type = 1
    else:
        file = file.convert('RGB')
        img_type = 2

    # определение размера цветности пикселя
    if img_type == 1 or img_type == 0:
        data = bytes(file.getdata())
    else:
        data = file.tobytes()

    # определение ширины и высоты изображения
    width, height = file.size

    # формирование заголовка
    header = struct.pack('<BHH', img_type, width, height)

    # создаём raw формат
    with open(f'{file_way}.myraw', 'wb') as f:
        f.write(header)
        f.write(data)

def compare(file_way):
    print(f"Файл: {file_way}")
    print(f"  Исходный размер: {os.path.getsize(file_way)} байт")
    print(f"  Raw размер:      {os.path.getsize(f'{file_way}.myraw')} байт")
    print(f"  Коэф. сжатия (исх/raw): {os.path.getsize(file_way) / os.path.getsize(f'{file_way}.myraw'):.3f}\n")

if __name__ == '__main__':
    #конвертация
    convert_to_myraw('bw_photo.jpg')
    convert_to_myraw('grey_photo.jpg')
    convert_to_myraw('color_photo.avif')

    #сравнение
    compare('bw_photo.jpg')
    compare('grey_photo.jpg')
    compare('color_photo.avif')