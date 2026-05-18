import os

from RLE import encode_file, decode_file
from Huffman import (huffman_encode_canonical, pack_huffman, unpack_huffman,
                     build_canonical_codes, huffman_decode_canonical)
from LZ import (lz77_encode, lz77_decode, lzss_encode, lzss_decode,
                lz78_encode, lz78_decode, lz78_encode_limited,
                lzw_encode, lzw_decode)
from MTF import mtf_encode, mtf_decode
from BWT import bwt, ibwt_fast, block_bwt, block_ibwt_fast

test_files = ['text.txt',
              'english_text_low127.txt',
              'setup.exe',
              'color_photo.avif',
              'bw_photo.jpg.raw',
              'bw_photo.png',
              'grey_photo.jpg',
              'bw_photo.png.raw',
              'grey_photo.jpg.raw',
              'color_photo.avif.raw',
              'bw_photo.jpg',
              'enwik7']

# Параметры алгоритмов
MS_RLE = 8
MC_RLE = 8
WS_LZ77 = 1024
LS_LZ77 = 16
WS_LZSS = 1024
LS_LZSS = 16
MAX_DIC_LZ78_LIM = 256
MAX_DIC_LZW = 4096
BLOCK_SIZE_BWT = 256

# Папка для результатов
base_dir = 'code_files'
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Подпапки для методов
method_folders = [
    'rle', 'huffman',
    'lz77', 'lzss', 'lz78', 'lz78_limited', 'lzw',
    'mtf', 'bwt', 'bwt_block'
]
for folder in method_folders:
    path = os.path.join(base_dir, folder)
    if not os.path.exists(path):
        os.makedirs(path)

def check_result(original, recovered, method_name, compressed_path, orig_size):
    if recovered == original:
        comp_size = os.path.getsize(compressed_path)
        ratio = orig_size / comp_size if comp_size else 0
        print(f"  {method_name}: {orig_size} -> {comp_size} байт (коэф. {ratio:.3f})")
    else:
        print(f"  {method_name}: ОШИБКА — восстановление не совпало!")

# Основной цикл по файлам
for filename in test_files:
    if not os.path.exists(filename):
        print(f"Файл {filename} не найден, пропускаем.")
        continue

    print(f"\n--- {filename} ---")
    original = open(filename, 'rb').read()
    orig_size = len(original)

    # 1. RLE
    method = 'rle'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.rle')
    dec_path = os.path.join(folder, filename + '.rle.dec')
    encode_file(filename, enc_path, MS_RLE, MC_RLE)
    decode_file(enc_path, dec_path)
    recovered = open(dec_path, 'rb').read()
    check_result(original, recovered, f"RLE (Ms={MS_RLE},Mc={MC_RLE})", enc_path, orig_size)

    # 2. Хаффман (канонический)
    method = 'huffman'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.huf')
    dec_path = os.path.join(folder, filename + '.huf.dec')
    enc_huf, lens_huf, pad_huf = huffman_encode_canonical(original)
    compressed = pack_huffman(enc_huf, lens_huf, pad_huf)
    open(enc_path, 'wb').write(compressed)
    enc2, lens2, pad2 = unpack_huffman(compressed)
    codes_huf = build_canonical_codes(lens2)
    recovered = huffman_decode_canonical(enc2, codes_huf, pad2)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, "Huffman (канонический)", enc_path, orig_size)

    # 3. LZ77
    method = 'lz77'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.lz77')
    dec_path = os.path.join(folder, filename + '.lz77.dec')
    enc = lz77_encode(original, WS_LZ77, LS_LZ77)
    open(enc_path, 'wb').write(enc)
    recovered = lz77_decode(enc)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, f"LZ77 (окно={WS_LZ77}, буфер={LS_LZ77})", enc_path, orig_size)

    # 4. LZSS
    method = 'lzss'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.lzss')
    dec_path = os.path.join(folder, filename + '.lzss.dec')
    enc = lzss_encode(original, WS_LZSS, LS_LZSS)
    open(enc_path, 'wb').write(enc)
    recovered = lzss_decode(enc)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, f"LZSS (окно={WS_LZSS}, буфер={LS_LZSS})", enc_path, orig_size)

    # 5. LZ78 (неограниченный)
    method = 'lz78'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.lz78')
    dec_path = os.path.join(folder, filename + '.lz78.dec')
    enc = lz78_encode(original)
    open(enc_path, 'wb').write(enc)
    recovered = lz78_decode(enc)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, "LZ78 (словарь неограничен)", enc_path, orig_size)

    # 6. LZ78 с ограниченным словарём
    method = 'lz78_limited'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.lz78')
    dec_path = os.path.join(folder, filename + '.lz78.dec')
    enc = lz78_encode_limited(original, MAX_DIC_LZ78_LIM)
    open(enc_path, 'wb').write(enc)
    recovered = lz78_decode(enc, max_dic=MAX_DIC_LZ78_LIM)  # ← обязательно передать max_dic
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, f"LZ78 (словарь ограничен, max={MAX_DIC_LZ78_LIM})", enc_path, orig_size)

    # 7. LZW
    method = 'lzw'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.lzw')
    dec_path = os.path.join(folder, filename + '.lzw.dec')
    enc = lzw_encode(original, MAX_DIC_LZW)
    open(enc_path, 'wb').write(enc)
    recovered = lzw_decode(enc, MAX_DIC_LZW)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, f"LZW (словарь, max={MAX_DIC_LZW})", enc_path, orig_size)

    # 8. MTF
    method = 'mtf'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.mtf')
    dec_path = os.path.join(folder, filename + '.mtf.dec')
    enc = mtf_encode(original)
    open(enc_path, 'wb').write(enc)
    recovered = mtf_decode(enc)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, "MTF", enc_path, orig_size)

    # 9. BWT классический
    method = 'bwt'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.bwt')
    dec_path = os.path.join(folder, filename + '.bwt.dec')
    L, k = bwt(original)
    with open(enc_path, 'wb') as f:
        f.write(L)
        f.write(k.to_bytes(4, 'big'))
    # Чтение для декодирования
    data = open(enc_path, 'rb').read()
    if len(data) < 4:
        L_data = b''
        k2 = 0
    else:
        L_data = data[:-4]
        k2 = int.from_bytes(data[-4:], 'big')
    recovered = ibwt_fast(L_data, k2)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, "BWT (классический)", enc_path, orig_size)

    # 10. BWT блочный
    method = 'bwt_block'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, filename + '.bwt')
    dec_path = os.path.join(folder, filename + '.bwt.dec')
    L_block, _ = block_bwt(original, BLOCK_SIZE_BWT)
    open(enc_path, 'wb').write(L_block)
    recovered = block_ibwt_fast(L_block, 0, BLOCK_SIZE_BWT)
    open(dec_path, 'wb').write(recovered)
    check_result(original, recovered, f"BWT (блочный, block_size={BLOCK_SIZE_BWT})", enc_path, orig_size)

print("\nГотово. Все сжатые и восстановленные файлы лежат в папке 'code_files'.")