import struct
from PIL import Image

from from_RGB_to_YCbCr import rgb_to_ycbcr, ycbcr_to_rgb
from Discrete_cosine_transform import (
    channel_to_blocks, blocks_to_channel, dct_2d, idct_2d, quantize, dequantize
)
from zigzag_bypass import zigzag_square, inverse_zigzag
from DifferentialCodingANDRLE import diff_encode_dc, diff_decode_dc
from variable_length_encoding import (
    vlc_encode_dc, rle_vlc_encode_ac, rle_vlc_decode_ac, decode_value_from_bits)
from Haff import (
    DC_HUFFMAN, AC_HUFFMAN, bits_to_bytes, bytes_to_bits,
    huffman_decode_dc, huffman_decode_ac
)
from ImageQuality import adapt_quantization_table, Q_Y
from Downsampling_Upsampling_Resizing import downsample, upsample

USE_COLOR = True # False - без Cb, Cr

def compress_image(img, quality=50):
    w = img.width
    h = img.height
    q_table = adapt_quantization_table(Q_Y, quality)

    rgb = img.tobytes()
    ycbcr = rgb_to_ycbcr(rgb)
    # Извлекаем каналы
    Y  = bytes(ycbcr[i] for i in range(0, len(ycbcr), 3))
    Cb = bytes(ycbcr[i] for i in range(1, len(ycbcr), 3))
    Cr = bytes(ycbcr[i] for i in range(2, len(ycbcr), 3))

    def encode_channel(channel_bytes, width, height):
        #Сжимает канал и возвращает (dc_vals, ac_vals)
        blocks = channel_to_blocks(channel_bytes, width, height, 8)
        dc_vals = []
        ac_vals = []
        for blk in blocks:
            dct_block = dct_2d(blk)
            quant = quantize(dct_block, q_table)
            zig = zigzag_square(quant)
            dc_vals.append(zig[0])
            ac_vals.append(rle_vlc_encode_ac(zig[1:]))
        return dc_vals, ac_vals

    # Обрабатываем полную яркость
    Y_dc, Y_ac = encode_channel(Y, w, h)

    if USE_COLOR:
        # Даунсемплинг Cb и Cr в 2 раза
        Cb_down, cb_w, cb_h = downsample(Cb, w, h, 1)   # channels=1
        Cr_down, cr_w, cr_h = downsample(Cr, w, h, 1)
        Cb_dc, Cb_ac = encode_channel(Cb_down, cb_w, cb_h)
        Cr_dc, Cr_ac = encode_channel(Cr_down, cr_w, cr_h)
    else:
        Cb_dc, Cb_ac = [], []
        Cr_dc, Cr_ac = [], []
        cb_w = cb_h = cr_w = cr_h = 0

    # Функция построения битового потока для набора блоков (DC+AC)
    def build_bitstream(dc_vals, ac_vals):
        diff = diff_encode_dc(dc_vals)
        dc_vlc = vlc_encode_dc(diff)  # категории и биты
        bits = ""
        num = len(dc_vals)
        for i in range(num):
            cat, bits_val = dc_vlc[i]
            bits += DC_HUFFMAN[cat] + bits_val
            for run, cat, bits_val in ac_vals[i]:
                bits += AC_HUFFMAN[(run, cat)]
                bits += bits_val
        return bits

    Y_bits = build_bitstream(Y_dc, Y_ac)
    Cb_bits = build_bitstream(Cb_dc, Cb_ac)
    Cr_bits = build_bitstream(Cr_dc, Cr_ac)

    # Склеиваем и преобразуем в байты
    total_bits = Y_bits + Cb_bits + Cr_bits
    compressed_data = bits_to_bytes(total_bits)

    return {
        'width': w, 'height': h,
        'cb_width': cb_w, 'cb_height': cb_h,
        'cr_width': cr_w, 'cr_height': cr_h,
        'q_table': q_table,
        'compressed_data': compressed_data
    }

def write_compressed_file(filename, width, height, cb_w, cb_h, cr_w, cr_h, q_table, compressed_data):
    with open(filename, 'wb') as f:
        f.write(b'CMPR')
        f.write(b'\x02')
        f.write(struct.pack('>HH', width, height))
        f.write(struct.pack('>HH', cb_w, cb_h))
        f.write(struct.pack('>HH', cr_w, cr_h))
        for i in range(8):
            for j in range(8):
                val = max(0, min(255, q_table[i][j]))
                f.write(bytes([val]))
        f.write(b'\x01')
        f.write(compressed_data)

def read_compressed_file(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    pos = 4
    ver = data[pos]; pos += 1
    w, h = struct.unpack('>HH', data[pos:pos+4]); pos += 4
    if ver >= 2:
        cb_w, cb_h = struct.unpack('>HH', data[pos:pos+4]); pos += 4
        cr_w, cr_h = struct.unpack('>HH', data[pos:pos+4]); pos += 4
    else:
        cb_w = cb_h = cr_w = cr_h = 0
    q = [[0]*8 for _ in range(8)]
    for i in range(8):
        for j in range(8):
            q[i][j] = data[pos]; pos += 1
    pos += 1  # разделитель
    return w, h, cb_w, cb_h, cr_w, cr_h, q, data[pos:]

def decompress_image(width, height, cb_w, cb_h, cr_w, cr_h, q_table, compressed_data):
    bitstream = bytes_to_bits(compressed_data)
    n = len(bitstream)

    def decode_channel(ch_w, ch_h, start_pos):
        # декодит, начиная с позиции start_pos. Возвращает (bytes канала, список блоков, новая позиция)
        pos = start_pos
        expected_blocks = ((ch_w + 7) // 8) * ((ch_h + 7) // 8)
        if expected_blocks == 0:
            return bytes(), [], pos

        dc_diff = []
        ac_pairs_all = []
        block_idx = 0
        while pos < n and len(dc_diff) < expected_blocks:

            #DC
            cat, pos = huffman_decode_dc(bitstream, pos)
            if cat is None:    break
            if pos + cat > n:    break
            bits = bitstream[pos:pos+cat]
            pos += cat
            diff_val = decode_value_from_bits(bits, cat)
            dc_diff.append(diff_val)

            # AC
            pairs = []
            while True:
                pair, pos = huffman_decode_ac(bitstream, pos)
                if pair is None:    break
                run, cat = pair
                if run == 0 and cat == 0:    break
                if cat == 0:    pairs.append((run, cat, ""))
                else:
                    if pos + cat > n:    break
                    bits = bitstream[pos:pos+cat]
                    pos += cat
                    pairs.append((run, cat, bits))
            ac_pairs_all.append(pairs)
            block_idx += 1

        # Восстановление DC
        dc_vals = diff_decode_dc(dc_diff)

        restored_blocks = []
        for i in range(len(dc_vals)):
            ac_list = rle_vlc_decode_ac(ac_pairs_all[i])

            zigzag = [dc_vals[i]] + ac_list
            zigzag = (zigzag + [0]*64)[:64]
            block = inverse_zigzag(zigzag, 8)
            dequant = dequantize(block, q_table)
            idct = idct_2d(dequant)
            for y in range(8):
                for x in range(8):
                    idct[y][x] = max(0, min(255, idct[y][x]))
            restored_blocks.append(idct)

        while len(restored_blocks) < expected_blocks:
            restored_blocks.append([[128]*8 for _ in range(8)])

        channel_bytes = blocks_to_channel(restored_blocks, ch_w, ch_h, 8)
        return channel_bytes, restored_blocks, pos

    # Декодируем Y
    Y_bytes, _, pos = decode_channel(width, height, 0)

    # Декодируем Cb и Cr, если есть
    if cb_w > 0 and cb_h > 0:
        Cb_down_bytes, _, pos = decode_channel(cb_w, cb_h, pos)
        Cr_down_bytes, _, pos = decode_channel(cr_w, cr_h, pos)
        # Апсемплинг обратно до размера яркости
        Cb_bytes, _, _ = upsample(Cb_down_bytes, cb_w, cb_h, 1)
        Cr_bytes, _, _ = upsample(Cr_down_bytes, cr_w, cr_h, 1)
        # Обрезаем до точного размера
        Cb_bytes = Cb_bytes[:width*height]
        Cr_bytes = Cr_bytes[:width*height]
    else:
        Cb_bytes = bytes([128]) * (width * height)
        Cr_bytes = bytes([128]) * (width * height)

    # Собираем в RGB
    ycbcr = bytearray()
    for i in range(width * height):
        ycbcr.append(Y_bytes[i])
        ycbcr.append(Cb_bytes[i])
        ycbcr.append(Cr_bytes[i])
    rgb_bytes = ycbcr_to_rgb(bytes(ycbcr))
    return Image.frombytes('RGB', (width, height), rgb_bytes)

if __name__ == "__main__":
    img = Image.open("Lenna.png").convert('RGB')
    comp = compress_image(img, quality=2)
    write_compressed_file("test.raw",
                          comp['width'], comp['height'],
                          comp['cb_width'], comp['cb_height'],
                          comp['cr_width'], comp['cr_height'],
                          comp['q_table'], comp['compressed_data'])
    w, h, cb_w, cb_h, cr_w, cr_h, q, d = read_compressed_file("test.raw")
    restored = decompress_image(w, h, cb_w, cb_h, cr_w, cr_h, q, d)
    restored.show()