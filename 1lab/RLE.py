import os

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

    len_string = len(string) // symbol_len
    rle_string = bytearray()
    rle_string.extend(original_len.to_bytes(4, 'big'))

    i = 0
    while i < len_string:
        cur_block = string[i * symbol_len: (i + 1) * symbol_len]
        if i + 1 < len_string and string[(i + 1) * symbol_len: (i + 2) * symbol_len] == cur_block:
            count = 1
            while (i + count < len_string
                   and string[(i + count) * symbol_len: (i + count + 1) * symbol_len] == cur_block
                   and count < max_len):
                count += 1
            rle_string.extend(count.to_bytes(count_len, 'big'))
            rle_string.extend(cur_block)
            i += count
        else:
            raw_len = 1
            while i + raw_len < len_string and raw_len < max_len:
                if string[(i + raw_len) * symbol_len: (i + raw_len + 1) * symbol_len] == string[(i + raw_len - 1) * symbol_len: (i + raw_len) * symbol_len]:
                    break
                raw_len += 1
            if i + raw_len < len_string:
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
    if not string:
        return b''
    if len(string) < 4:
        return b''
    original_len = int.from_bytes(string[:4], 'big')
    data = string[4:]

    rld_string = bytearray()
    i = 0
    len_string = len(data)
    while i < len_string:
        if i + count_len > len_string:
            break
        ctrl_bytes = data[i:i + count_len]
        ctrl = int.from_bytes(ctrl_bytes, 'big')
        i += count_len
        if ctrl & (1 << (Mc - 1)):
            length = ctrl & ((1 << (Mc - 1)) - 1)
            for _ in range(length):
                if i + symbol_len > len_string:
                    break
                rld_string.extend(data[i:i + symbol_len])
                i += symbol_len
        else:
            count = ctrl
            if i + symbol_len > len_string:
                break
            block = data[i:i + symbol_len]
            rld_string.extend(block * count)
            i += symbol_len

    return bytes(rld_string[:original_len])

def read_header(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if len(data) < 4:
        print("Ошибка: некорректный RLE-файл (недостаточно заголовка)")
        return None, None, None
    Ms = int.from_bytes(data[:2], 'big')
    Mc = int.from_bytes(data[2:4], 'big')
    rest = data[4:]
    return Ms, Mc, rest

def encode_file(input_path, output_path, Ms, Mc):
    if Ms % 8 != 0 or Mc % 8 != 0:
        print("Ошибка: Ms и Mc должны быть кратны 8")
        return
    with open(input_path, 'rb') as f:
        data = f.read()
    encoded = RLE(data, Mc, Ms)
    header = Ms.to_bytes(2, 'big') + Mc.to_bytes(2, 'big')
    with open(output_path, 'wb') as f:
        f.write(header + encoded)

def decode_file(input_path, output_path):
    Ms, Mc, encoded = read_rle_header(input_path)
    if Ms is None:
        return
    if Ms % 8 != 0 or Mc % 8 != 0:
        print("Ошибка: Ms и Mc должны быть кратны 8")
        return
    decoded = RLD(encoded, Mc, Ms)
    with open(output_path, 'wb') as f:
        f.write(decoded)

def test(files, MS, MC):
    print(f"\n--- Обычные файлы (Ms={MS}, Mc={MC}) ---")
    for filename in files:
        if not os.path.exists(filename):
            print(f"Файл {filename} не найден, пропускаем.")
            continue

        enc_name = filename + '.rle'
        dec_name = filename + '.dec'

        encode_file(filename, enc_name, MS, MC)
        decode_file(enc_name, dec_name)

        with open(filename, 'rb') as f:
            original = f.read()
        with open(dec_name, 'rb') as f:
            recovered = f.read()

        if original == recovered:
            orig_size = len(original)
            comp_size = os.path.getsize(enc_name)
            ratio = orig_size / comp_size if comp_size else 0
            print(f"OK  {filename}: {orig_size} -> {comp_size} байт (коэф. {ratio:.3f})")
        else:
            print(f"FAIL {filename}: восстановление не совпало!")

        for tmp in (enc_name, dec_name):
            if os.path.exists(tmp):
                os.remove(tmp)

if __name__ == '__main__':
    ordinary_files = [
        'text.txt',
        'english_text_low127.txt',
        'setup.exe',
        'bw_photo.jpg',
        'bw_photo.png',
        'grey_photo.jpg',
        'color_photo.avif',
        'bw_photo.jpg.raw',
        'bw_photo.png.raw',
        'grey_photo.jpg.raw',
        'color_photo.avif.raw']
    MS = 8
    MC = 8
    MC_override = None

    test(ordinary_files, MS, MC)
    print("\nТестирование завершено.")