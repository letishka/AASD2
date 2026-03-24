import os
import sys

def RLE(string: bytes, Mc: int, Ms: int) -> bytes:
    max_len = (1 << (Mc - 1)) - 1
    symbol_len = Ms // 8
    count_len = Mc // 8
    if not string:
        return b''
    original_len = len(string)
    remainder = original_len % symbol_len
    if remainder:
        string = string + b'\x00' * (symbol_len - remainder)

    n = len(string) // symbol_len
    rle_string = bytearray()
    rle_string.extend(original_len.to_bytes(4, 'big'))

    i = 0
    while i < n:
        cur_block = string[i * symbol_len: (i + 1) * symbol_len]
        if i + 1 < n and string[(i + 1) * symbol_len: (i + 2) * symbol_len] == cur_block:
            count = 1
            while i + count < n and string[(i + count) * symbol_len: (i + count + 1) * symbol_len] == cur_block and count < max_len:
                count += 1
            rle_string.extend(count.to_bytes(count_len, 'big'))
            rle_string.extend(cur_block)
            i += count
        else:
            raw_len = 1
            while i + raw_len < n and raw_len < max_len:
                if string[(i + raw_len) * symbol_len: (i + raw_len + 1) * symbol_len] == string[(i + raw_len - 1) * symbol_len: (i + raw_len) * symbol_len]:
                    break
                raw_len += 1
            if i + raw_len < n:
                if (string[(i + raw_len - 1) * symbol_len: (i + raw_len) * symbol_len] ==
                        string[(i + raw_len) * symbol_len: (i + raw_len + 1) * symbol_len] and raw_len != 1):
                    raw_len -= 1
            ctrl = (1 << (Mc - 1)) | raw_len
            rle_string.extend(ctrl.to_bytes(count_len, 'big'))
            rle_string.extend(string[i * symbol_len: (i + raw_len) * symbol_len])
            i += raw_len
    return bytes(rle_string)

def RLD(string: bytes, Mc: int, Ms: int) -> bytes:
    symbol_len = Ms // 8
    count_len = Mc // 8
    max_len = (1 << (Mc - 1)) - 1

    if not string:
        return b''

    if len(string) < 4:
        return b''
    original_len = int.from_bytes(string[:4], 'big')
    data = string[4:]

    rld_string = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if i + count_len > n:
            break
        ctrl_bytes = data[i:i + count_len]
        ctrl = int.from_bytes(ctrl_bytes, 'big')
        i += count_len
        if ctrl & (1 << (Mc - 1)):
            length = ctrl & ((1 << (Mc - 1)) - 1)
            for _ in range(length):
                if i + symbol_len > n:
                    break
                rld_string.extend(data[i:i + symbol_len])
                i += symbol_len
        else:
            count = ctrl
            if i + symbol_len > n:
                break
            block = data[i:i + symbol_len]
            rld_string.extend(block * count)
            i += symbol_len

    return bytes(rld_string[:original_len])

def encode_file(input_path: str, output_path: str, Ms: int, Mc: int) -> None:
    if Ms % 8 != 0 or Mc % 8 != 0:
        print("Ошибка: Ms и Mc должны быть кратны 8")
        return
    f = open(input_path, 'rb')
    data = f.read()
    f.close()
    encoded = RLE(data, Mc, Ms)
    header = Ms.to_bytes(2, 'big') + Mc.to_bytes(2, 'big')
    f = open(output_path, 'wb')
    f.write(header + encoded)
    f.close()

def decode_file(input_path: str, output_path: str) -> None:
    f = open(input_path, 'rb')
    header = f.read(4)
    if len(header) != 4:
        print("Ошибка: некорректный файл, недостаточно заголовка")
        f.close()
        return
    Ms = int.from_bytes(header[:2], 'big')
    Mc = int.from_bytes(header[2:4], 'big')
    encoded = f.read()
    f.close()
    if Ms % 8 != 0 or Mc % 8 != 0:
        print("Ошибка: Ms и Mc должны быть кратны 8")
        return
    decoded = RLD(encoded, Mc, Ms)
    f = open(output_path, 'wb')
    f.write(decoded)
    f.close()

def read_raw_header(filepath):
    f = open(filepath, 'rb')
    header = f.read(5)
    f.close()
    if len(header) != 5:
        print("Ошибка: некорректный raw-файл (не хватает заголовка)")
        return None, None, None, None, None
    img_type = header[0]
    Ms = int.from_bytes(header[1:3], 'little')
    Mc = int.from_bytes(header[3:5], 'little')
    data_offset = 5
    return img_type, Ms, Mc, data_offset

def encode_raw_file(input_path: str, output_path: str, Mc_override=None):
    img_type, Ms, Mc, offset = read_raw_header(input_path)
    if img_type is None:
        print("Ошибка чтения заголовка raw-файла")
        return
    if Mc_override is not None:
        Mc = Mc_override

    f = open(input_path, 'rb')
    f.seek(offset)
    pixel_data = f.read()
    f.close()

    encoded = RLE(pixel_data, Mc, Ms)

    f = open(output_path, 'wb')
    f.write(Ms.to_bytes(2, 'big'))
    f.write(Mc.to_bytes(2, 'big'))
    f2 = open(input_path, 'rb')
    raw_header = f2.read(5)
    f2.close()
    f.write(raw_header)
    f.write(encoded)
    f.close()

def decode_raw_file(input_path: str, output_path: str):
    f = open(input_path, 'rb')
    ms_bytes = f.read(2)
    if len(ms_bytes) < 2:
        print("Ошибка: некорректный сжатый файл")
        f.close()
        return
    Ms = int.from_bytes(ms_bytes, 'big')
    mc_bytes = f.read(2)
    Mc = int.from_bytes(mc_bytes, 'big')
    raw_header = f.read(5)
    if len(raw_header) < 5:
        print("Ошибка: отсутствует raw-заголовок")
        f.close()
        return
    encoded = f.read()
    f.close()

    decoded_pixel = RLD(encoded, Mc, Ms)

    f = open(output_path, 'wb')
    f.write(raw_header)
    f.write(decoded_pixel)
    f.close()

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(__file__))
    from converter_to_raw import convert_to_myraw

    # Обычные файлы – теперь включая исходные изображения
    ordinary_files = [
        'text.txt',
        'english_text_low127.txt',
        'setup.exe',
        'bw_photo.jpg',
        'bw_photo.png',
        'grey_photo.jpg',
        'color_photo.avif'
    ]

    image_pairs = [
        ('bw_photo.jpg', 'bw_photo.jpg.myraw'),
        ('bw_photo.png', 'bw_photo.png.myraw'),
        ('grey_photo.jpg', 'grey_photo.jpg.myraw'),
        ('color_photo.avif', 'color_photo.avif.myraw')
    ]

    MS_ORDINARY = 8
    MC_ORDINARY = 8
    MC_OVERRIDE = None

    print("\n--- Обычные файлы (Ms={}, Mc={}) ---".format(MS_ORDINARY, MC_ORDINARY))
    for filename in ordinary_files:
        if not os.path.exists(filename):
            print("Файл {} не найден, пропускаем.".format(filename))
        else:
            enc_name = filename + '.rle'
            dec_name = filename + '.dec'

            encode_file(filename, enc_name, MS_ORDINARY, MC_ORDINARY)
            decode_file(enc_name, dec_name)

            f = open(filename, 'rb')
            original = f.read()
            f.close()
            f = open(dec_name, 'rb')
            recovered = f.read()
            f.close()

            if original == recovered:
                orig_size = len(original)
                comp_size = os.path.getsize(enc_name)
                ratio = orig_size / comp_size if comp_size else 0
                print("OK  {}: {} -> {} байт (коэф. {:.3f})".format(
                    filename, orig_size, comp_size, ratio))
            else:
                print("FAIL {}: восстановление не совпало!".format(filename))

            if os.path.exists(enc_name):
                os.remove(enc_name)
            if os.path.exists(dec_name):
                os.remove(dec_name)

    print("\n--- Raw-изображения (только пиксельные данные, Ms, Mc из заголовка .myraw) ---")
    for src, raw_name in image_pairs:
        if not os.path.exists(raw_name):
            print("Создаём {} из {}...".format(raw_name, src))
            if not os.path.exists(src):
                print("Исходный файл {} не найден, пропускаем.".format(src))
            else:
                convert_to_myraw(src, Ms=None, Mc=16)
                if not os.path.exists(raw_name) and os.path.exists(src + '.myraw'):
                    os.rename(src + '.myraw', raw_name)

        if not os.path.exists(raw_name):
            print("Файл {} не найден, пропускаем.".format(raw_name))
        else:
            enc_name = raw_name + '.rle'
            dec_name = raw_name + '.dec'

            encode_raw_file(raw_name, enc_name, Mc_override=MC_OVERRIDE)
            decode_raw_file(enc_name, dec_name)

            f = open(raw_name, 'rb')
            original = f.read()
            f.close()
            f = open(dec_name, 'rb')
            recovered = f.read()
            f.close()

            if original == recovered:
                orig_size = len(original)
                comp_size = os.path.getsize(enc_name)
                ratio = orig_size / comp_size if comp_size else 0
                print("OK  {}: {} -> {} байт (коэф. {:.3f})".format(
                    raw_name, orig_size, comp_size, ratio))
            else:
                print("FAIL {}: восстановление не совпало!".format(raw_name))

            if os.path.exists(enc_name):
                os.remove(enc_name)
            if os.path.exists(dec_name):
                os.remove(dec_name)

    print("\nТестирование завершено.")