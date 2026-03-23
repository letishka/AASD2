import os
import sys
import glob
import tempfile

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

    n = len(string) // symbol_len # n — количество символов
    rle_string = bytearray()
    # Сохраняем исходную длину в первых 4 байтах
    rle_string.extend(original_len.to_bytes(4, 'big'))

    i = 0
    while i < n:
        cur_block = string[i * symbol_len: (i + 1) * symbol_len]
        if i + 1 < n and string[(i + 1) * symbol_len: (i + 2) * symbol_len] == cur_block:
            # Повторяющаяся последовательность
            count = 1
            while i + count < n and string[
                (i + count) * symbol_len: (i + count + 1) * symbol_len] == cur_block and count < max_len:
                count += 1
            # Управляющее слово со старшим битом 0
            rle_string.extend(count.to_bytes(count_len, 'big'))
            rle_string.extend(cur_block)
            i += count
        else:
            # Неповторяющаяся последовательность
            raw_len = 1
            while i + raw_len < n and raw_len < max_len:
                if string[(i + raw_len) * symbol_len: (i + raw_len + 1) * symbol_len] == string[
                    (i + raw_len - 1) * symbol_len: (i + raw_len) * symbol_len]:
                    break
                raw_len += 1
            # Корректировка захвата начала повтора
            if i + raw_len < n:
                if (string[(i + raw_len - 1) * symbol_len: (i + raw_len) * symbol_len] ==
                        string[(i + raw_len) * symbol_len: (i + raw_len + 1) * symbol_len] and raw_len != 1):
                    raw_len -= 1
            # Управляющее слово со старшим битом 1
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

    # Достаём исходную длину из первых 4 байт
    if len(string) < 4:
        return b''
    original_len = int.from_bytes(string[:4], 'big')
    data = string[4:]  # закодированная часть

    rld_string = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if i + count_len > n:
            break
        ctrl_bytes = data[i:i + count_len]
        ctrl = int.from_bytes(ctrl_bytes, 'big')
        i += count_len
        if ctrl & (1 << (Mc - 1)):  # raw‑блок
            length = ctrl & ((1 << (Mc - 1)) - 1)
            for _ in range(length):
                if i + symbol_len > n:
                    break
                rld_string.extend(data[i:i + symbol_len])
                i += symbol_len
        else:  # повтор
            count = ctrl
            if i + symbol_len > n:
                break
            block = data[i:i + symbol_len]
            rld_string.extend(block * count)
            i += symbol_len

    # Убираем добавленные нули
    return bytes(rld_string[:original_len])

def encode_file(input_path: str, output_path: str, Ms: int, Mc: int) -> None:
    if Ms % 8 != 0 or Mc % 8 != 0:
        raise ValueError("Ms and Mc must be multiples of 8")
    with open(input_path, 'rb') as f:
        data = f.read()
    encoded = RLE(data, Mc, Ms)
    header = Ms.to_bytes(2, 'big') + Mc.to_bytes(2, 'big')
    with open(output_path, 'wb') as f:
        f.write(header + encoded)

def decode_file(input_path: str, output_path: str) -> None:
    with open(input_path, 'rb') as f:
        header = f.read(4)
        if len(header) != 4:
            raise ValueError("Invalid file format: missing header")
        Ms = int.from_bytes(header[:2], 'big')
        Mc = int.from_bytes(header[2:4], 'big')
        encoded = f.read()
    if Ms % 8 != 0 or Mc % 8 != 0:
        raise ValueError("Ms and Mc must be multiples of 8")
    decoded = RLD(encoded, Mc, Ms)
    with open(output_path, 'wb') as f:
        f.write(decoded)

def read_raw_header(filepath):
    """
    Читает расширенный заголовок .myraw и возвращает:
    (img_type, width, height, Ms, Mc, data_offset)
    """
    with open(filepath, 'rb') as f:
        header = f.read(9)   # 1 + 2 + 2 + 2 + 2 = 9 байт
        if len(header) != 9:
            raise ValueError("Некорректный raw-файл (не хватает заголовка)")
        img_type = header[0]
        width = int.from_bytes(header[1:3], 'little')
        height = int.from_bytes(header[3:5], 'little')
        Ms = int.from_bytes(header[5:7], 'little')
        Mc = int.from_bytes(header[7:9], 'little')
        data_offset = 9
    return img_type, width, height, Ms, Mc, data_offset

def encode_raw_file(input_path: str, output_path: str, Mc_override=None) -> None:
    """
    Кодирует .myraw файл.
    Ms и Mc (если не переопределены) берутся из заголовка raw-файла.
    """
    img_type, width, height, Ms, Mc, offset = read_raw_header(input_path)
    if Mc_override is not None:
        Mc = Mc_override   # можно переопределить Mc

    with open(input_path, 'rb') as f:
        f.seek(offset)
        pixel_data = f.read()

    encoded = RLE(pixel_data, Mc, Ms)

    with open(output_path, 'wb') as f:
        f.write(Ms.to_bytes(2, 'big'))
        f.write(Mc.to_bytes(2, 'big'))
        # Сохраняем оригинальный заголовок raw (9 байт)
        with open(input_path, 'rb') as fin:
            fin.seek(0)
            f.write(fin.read(9))
        f.write(encoded)

def decode_raw_file(input_path: str, output_path: str) -> None:
    """
    Декодирует файл, созданный encode_raw_file, обратно в .myraw.
    """
    with open(input_path, 'rb') as f:
        ms_bytes = f.read(2)
        if len(ms_bytes) < 2:
            raise ValueError("Некорректный сжатый файл")
        Ms = int.from_bytes(ms_bytes, 'big')
        mc_bytes = f.read(2)
        Mc = int.from_bytes(mc_bytes, 'big')
        raw_header = f.read(9)
        if len(raw_header) < 9:
            raise ValueError("Отсутствует raw-заголовок")
        encoded = f.read()

    decoded_pixel = RLD(encoded, Mc, Ms)

    with open(output_path, 'wb') as f:
        f.write(raw_header)
        f.write(decoded_pixel)

if __name__ == '__main__':
    # Импортируем функцию конвертации из converter_to_raw.py (если файл в той же папке)
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from converter_to_raw import convert_to_myraw
    except ImportError:
        print("Предупреждение: не удалось импортировать convert_to_myraw. "
              "Убедитесь, что converter_to_raw.py находится в той же папке.")
        # Заглушка, если не можем импортировать
        def convert_to_myraw(*args, **kwargs):
            raise NotImplementedError("convert_to_myraw не доступен")

    # --- Список файлов для тестирования (как на вашей картинке) ---
    # Обычные файлы (не .myraw)
    ordinary_files = [
        'text.txt',                  # вероятно, русский текст
        'english_text_low127.txt',   # английский текст
        'setup.exe',                 # бинарный файл
    ]

    # Изображения: для каждого укажем исходный файл и желаемое имя .myraw
    image_pairs = [
        ('bw_photo.jpg', 'bw_photo.jpg.myraw'),
        ('bw_photo.png', 'bw_photo.png.myraw'),
        ('grey_photo.jpg', 'grey_photo.jpg.myraw'),
        ('color_photo.avif', 'color_photo.avif.myraw')
    ]

    # Для обычных файлов используем Ms=8, Mc=8 (символ = 1 байт, счётчик = 1 байт)
    MS_ORDINARY = 8
    MC_ORDINARY = 8

    # Для raw-изображений Ms и Mc будут взяты из заголовка .myraw,
    # но можно при необходимости переопределить Mc через параметр Mc_override
    MC_OVERRIDE = None   # None означает "использовать то, что в заголовке"

    print("\n===== Тестирование RLE на ваших файлах =====")

    # --- 1. Обычные файлы (текст, exe) ---
    print("\n--- 1. Обычные файлы (Ms={}, Mc={}) ---".format(MS_ORDINARY, MC_ORDINARY))
    for filename in ordinary_files:
        if not os.path.exists(filename):
            print("Файл {} не найден, пропускаем.".format(filename))
            continue

        enc_name = filename + '.rle'
        dec_name = filename + '.dec'

        try:
            encode_file(filename, enc_name, MS_ORDINARY, MC_ORDINARY)
            decode_file(enc_name, dec_name)

            with open(filename, 'rb') as f:
                original = f.read()
            with open(dec_name, 'rb') as f:
                recovered = f.read()

            if original == recovered:
                orig_size = len(original)
                comp_size = os.path.getsize(enc_name)
                ratio = orig_size / comp_size if comp_size else 0
                print("OK  {}: {} -> {} байт (коэф. {:.3f})".format(
                    filename, orig_size, comp_size, ratio))
            else:
                print("FAIL {}: восстановление не совпало!".format(filename))
        except Exception as e:
            print("Ошибка при обработке {}: {}".format(filename, e))
        finally:
            # Удаляем временные файлы, если они созданы
            if os.path.exists(enc_name):
                os.remove(enc_name)
            if os.path.exists(dec_name):
                os.remove(dec_name)

    # --- 2. Raw-изображения ---
    print("\n--- 2. Raw-изображения (Ms, Mc из заголовка .myraw) ---")
    for src, raw_name in image_pairs:
        # Если .myraw уже существует, используем его. Иначе создаём.
        if not os.path.exists(raw_name):
            print("Создаём {} из {}...".format(raw_name, src))
            if not os.path.exists(src):
                print("Исходный файл {} не найден, пропускаем.".format(src))
                continue
            try:
                # Создаём .myraw с Ms и Mc по умолчанию (8/24 и 16)
                convert_to_myraw(src, Ms=None, Mc=16)   # Ms определится автоматически
                # Переименовываем, если функция создала файл с другим именем
                if not os.path.exists(raw_name) and os.path.exists(src + '.myraw'):
                    os.rename(src + '.myraw', raw_name)
            except Exception as e:
                print("Не удалось создать {}: {}".format(raw_name, e))
                continue

        # Теперь raw_name должен существовать
        if not os.path.exists(raw_name):
            print("Файл {} не найден, пропускаем.".format(raw_name))
            continue

        enc_name = raw_name + '.rle'
        dec_name = raw_name + '.dec'

        try:
            encode_raw_file(raw_name, enc_name, Mc_override=MC_OVERRIDE)
            decode_raw_file(enc_name, dec_name)

            with open(raw_name, 'rb') as f:
                original = f.read()
            with open(dec_name, 'rb') as f:
                recovered = f.read()

            if original == recovered:
                orig_size = len(original)
                comp_size = os.path.getsize(enc_name)
                ratio = orig_size / comp_size if comp_size else 0
                print("OK  {}: {} -> {} байт (коэф. {:.3f})".format(
                    raw_name, orig_size, comp_size, ratio))
            else:
                print("FAIL {}: восстановление не совпало!".format(raw_name))
        except Exception as e:
            print("Ошибка при обработке {}: {}".format(raw_name, e))
        finally:
            if os.path.exists(enc_name):
                os.remove(enc_name)
            if os.path.exists(dec_name):
                os.remove(dec_name)

    print("\nТестирование завершено.")