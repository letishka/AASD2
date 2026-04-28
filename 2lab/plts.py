import struct
from PIL import Image
import matplotlib.pyplot as plt

# Импортируем модули так же, как в write_to_file.py
dct_module = __import__('Discrete_cosine_transform')
zigzag_module = __import__('zigzag_bypass')
dc_ac_module = __import__('DifferentialCoding&RLE')
vlc_module = __import__('variable-length_encoding')
haff_module = __import__('Haff')
quality_module = __import__('ImageQuality')

# Короткие ссылки на нужные функции
rgb_to_y = dct_module.rgb_to_y
y_to_rgb = dct_module.y_to_rgb
bytes_to_blocks = dct_module.bytes_to_blocks
blocks_to_bytes = dct_module.blocks_to_bytes
quantize = dct_module.quantize
dequantize = dct_module.dequantize
dct_2d_matrix = dct_module.dct_2d_matrix
idct_2d_matrix = dct_module.idct_2d_matrix

zigzag_square = zigzag_module.zigzag_square

diff_encode_dc = dc_ac_module.diff_encode_dc

get_category = vlc_module.get_category
get_bits_for_value = vlc_module.get_bits_for_value
decode_value_from_bits = vlc_module.decode_value_from_bits
vlc_encode_dc = vlc_module.vlc_encode_dc
rle_vlc_encode_ac = vlc_module.rle_vlc_encode_ac
rle_vlc_decode_ac = vlc_module.rle_vlc_decode_ac

DC_HUFFMAN = haff_module.DC_HUFFMAN
AC_HUFFMAN = haff_module.AC_HUFFMAN
huffman_encode_dc = haff_module.huffman_encode_dc
huffman_encode_ac = haff_module.huffman_encode_ac
bits_to_bytes = haff_module.bits_to_bytes

adapt_quantization_table = quality_module.adapt_quantization_table
Q_Y = quality_module.Q_Y

# Генерация порядка зигзага для 8x8 для декомпрессии
def generate_zigzag_order(n=8):
    order = []
    for s in range(2 * n - 1):
        if s % 2 == 0:
            i = s
            if i >= n:
                i = n - 1
            while i >= 0:
                j = s - i
                if j >= 0 and j < n:
                    order.append((i, j))
                i = i - 1
        else:
            i = 0
            if s >= n:
                i = s - (n - 1)
            while i < n:
                j = s - i
                if j >= 0 and j < n:
                    order.append((i, j))
                i = i + 1
    return order

ZIGZAG_ORDER = generate_zigzag_order(8)

# Сжатие (как write_to_file.py, но с явным возвратом)
def compress_image(img, quality):
    width = img.width
    height = img.height
    q_table = adapt_quantization_table(Q_Y, quality)

    rgb_bytes = img.tobytes()
    y_bytes = rgb_to_y(rgb_bytes, width, height)
    blocks = bytes_to_blocks(y_bytes, width, height, 8)

    dc_coeffs = []
    ac_rle_vlc_all = []

    for block in blocks:
        coeffs = dct_2d_matrix(block)
        quant = quantize(coeffs, q_table)
        zigzag = zigzag_square(quant)
        dc_coeffs.append(zigzag[0])
        ac_rle_vlc_all.append(rle_vlc_encode_ac(zigzag[1:]))

    diff_dc = diff_encode_dc(dc_coeffs)
    dc_vlc = vlc_encode_dc(diff_dc)

    bitstream = ""
    for cat, bits in dc_vlc:
        bitstream = bitstream + huffman_encode_dc(cat) + bits
    for block_ac in ac_rle_vlc_all:
        for run, cat, bits in block_ac:
            bitstream = bitstream + huffman_encode_ac(run, cat) + bits

    compressed_data = bits_to_bytes(bitstream)
    return width, height, q_table, compressed_data

# ------------------------------------------------------------
# Запись сжатого файла .myraw (простое копирование)
# ------------------------------------------------------------
def write_compressed_file(filename, width, height, q_table, compressed_data):
    f = open(filename, 'wb')
    f.write(b'CMPR')
    f.write(b'\x01')
    f.write(struct.pack('>HH', width, height))
    for i in range(8):
        for j in range(8):
            val = q_table[i][j]
            if val < 0:
                val = 0
            if val > 255:
                val = 255
            f.write(bytes([val]))
    f.write(b'\x01')
    f.write(compressed_data)
    f.close()

# Чтение сжатого файла .myraw
def read_compressed_file(filename):
    f = open(filename, 'rb')
    data = f.read()
    f.close()
    pos = 0
    if data[pos:pos+4] != b'CMPR':
        return None
    pos = pos + 4
    pos = pos + 1
    width, height = struct.unpack('>HH', data[pos:pos+4])
    pos = pos + 4
    q_table = [[0]*8 for _ in range(8)]
    for i in range(8):
        for j in range(8):
            q_table[i][j] = data[pos]
            pos = pos + 1
    pos = pos + 1
    compressed_data = data[pos:]
    return width, height, q_table, compressed_data

# Декомпрессия
def decompress_image(width, height, q_table, compressed_data):
    bitstream = ""
    for b in compressed_data:
        for i in range(8):
            bit = (b >> (7 - i)) & 1
            if bit == 1:
                bitstream = bitstream + "1"
            else:
                bitstream = bitstream + "0"

    dc_rev = {}
    for cat, code in DC_HUFFMAN.items():
        dc_rev[code] = cat

    ac_rev = {}
    for (run, cat), code in AC_HUFFMAN.items():
        ac_rev[code] = (run, cat)

    pos = 0
    n = len(bitstream)
    expected_blocks = (width // 8) * (height // 8)

    dc_diff = []
    ac_blocks = []

    while pos < n and len(dc_diff) < expected_blocks:
        code = ""
        cat = None
        while pos < n and cat is None:
            code = code + bitstream[pos]
            pos = pos + 1
            if code in dc_rev:
                cat = dc_rev[code]
        if cat is None:
            break
        bits = bitstream[pos:pos+cat]
        pos = pos + cat
        dc_diff.append(decode_value_from_bits(bits, cat))

        ac_pairs = []
        while True:
            code = ""
            pair = None
            while pos < n and pair is None:
                code = code + bitstream[pos]
                pos = pos + 1
                if code in ac_rev:
                    pair = ac_rev[code]
            if pair is None:
                break
            run, cat = pair
            if run == 0 and cat == 0:
                break
            if cat == 0:
                ac_pairs.append((run, cat, ""))
                continue
            bits = bitstream[pos:pos+cat]
            pos = pos + cat
            ac_pairs.append((run, cat, bits))
        ac_blocks.append(ac_pairs)

    dc_vals = [dc_diff[0]]
    for i in range(1, len(dc_diff)):
        dc_vals.append(dc_vals[-1] + dc_diff[i])

    restored_blocks = []
    for i in range(len(dc_vals)):
        ac_list = rle_vlc_decode_ac(ac_blocks[i])
        zigzag = [dc_vals[i]] + ac_list
        while len(zigzag) < 64:
            zigzag.append(0)
        zigzag = zigzag[:64]

        block = [[0]*8 for _ in range(8)]
        for idx in range(64):
            row, col = ZIGZAG_ORDER[idx]
            block[row][col] = zigzag[idx]

        dequant = dequantize(block, q_table)
        restored = idct_2d_matrix(dequant)
        for y in range(8):
            for x in range(8):
                if restored[y][x] < 0:
                    restored[y][x] = 0
                if restored[y][x] > 255:
                    restored[y][x] = 255
        restored_blocks.append(restored)

    while len(restored_blocks) < expected_blocks:
        restored_blocks.append([[128.0]*8 for _ in range(8)])

    restored_y = blocks_to_bytes(restored_blocks, width, height, 8)
    restored_rgb = y_to_rgb(restored_y, width, height)
    return Image.frombytes('RGB', (width, height), restored_rgb)

if __name__ == "__main__":
    # Список тестовых изображений (пути)
    images = [
        ("Lenna.png", "Lenna"),
        ("color_image.png", "colour"),
        ("grey_image.png", "grey"),
        ("bw_no_dither.png", "bw_no_dither"),
        ("bw_dither.png", "bw_dither"),
    ]

    qualities = [10, 20, 30, 40, 50, 60, 70, 80, 90]

    # Для каждого изображения будем строить график
    for img_path, name in images:
        # Загружаем изображение
        img = Image.open(img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Обрезаем до размера, кратного 8
        w = img.width - (img.width % 8)
        h = img.height - (img.height % 8)
        img = img.crop((0, 0, w, h))

        sizes = []  # размер сжатых данных в байтах для каждого качества

        print("Обработка изображения: %s" % name)
        for q in qualities:
            # Сжатие
            width, height, q_table, compressed_data = compress_image(img, q)
            size = len(compressed_data)
            sizes.append(size)

            # Сохраняем сжатый файл
            filename = "compressed_%s_q%d.myraw" % (name, q)
            write_compressed_file(filename, width, height, q_table, compressed_data)

            # Декомпрессия и сохранение восстановленного изображения
            r_width, r_height, r_q_table, r_compressed = read_compressed_file(filename)
            restored_img = decompress_image(r_width, r_height, r_q_table, r_compressed)
            restored_filename = "restored_%s_q%d.jpg" % (name, q)
            restored_img.save(restored_filename)

            print("  Q=%d, размер=%d байт, сохранён %s" % (q, size, restored_filename))

        # Построение графика
        plt.figure()
        plt.plot(qualities, sizes, marker='o')
        plt.title("Зависимость размера от качества для %s" % name)
        plt.xlabel("Качество")
        plt.ylabel("Размер сжатых данных (байт)")
        plt.grid(True)
        plt.savefig("graph_%s.png" % name)
        plt.close()

        print("График сохранён: graph_%s.png\n" % name)

    print("Готово.")