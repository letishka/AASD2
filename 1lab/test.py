import os

# Импорты
from RLE import encode_file, decode_file
from Huffman import huffman_encode, save_compressed, load_compressed, huffman_decode
from Huffman import huffman_encode_canonical, save_compressed_canonical, load_compressed_canonical, huffman_decode_canonical
from LZ import lz77_encode, lz77_decode, lzss_encode, lzss_decode
from LZ import lz78_encode, lz78_decode, lz78_encode_limited, lzw_encode, lzw_decode
from MTF import mtf_encode, mtf_decode
from BWT import bwt, ibwt_fast, block_bwt, block_ibwt_fast

# Файлы для тестирования
test_files = [
    'text.txt',
    'english_text_low127.txt',
    'setup.exe',
    'bw_photo.jpg',
    'bw_photo.png',
    'grey_photo.jpg',
    'color_photo.avif'
]

# Параметры
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

# Создаём подпапки для методов
method_folders = [
    'rle', 'huffman', 'huffman_canonical',
    'lz77', 'lzss', 'lz78', 'lz78_limited', 'lzw',
    'mtf', 'bwt', 'bwt_block'
]
for folder in method_folders:
    path = os.path.join(base_dir, folder)
    if not os.path.exists(path):
        os.makedirs(path)

# ----------------------------------------------------------------------
# Вспомогательная функция для чтения файла
def read_file(path):
    f = open(path, 'rb')
    data = f.read()
    f.close()
    return data

# Вспомогательная функция для записи файла
def write_file(path, data):
    f = open(path, 'wb')
    f.write(data)
    f.close()

# Функция проверки результата
def check_result(original, recovered, method_name, compressed_path, orig_size):
    if recovered == original:
        comp_size = os.path.getsize(compressed_path)
        ratio = orig_size / comp_size if comp_size else 0
        print(f"  {method_name}: {orig_size} -> {comp_size} байт (коэф. {ratio:.3f})")
    else:
        print(f"  {method_name}: ОШИБКА — восстановление не совпало!")

# Основной цикл по файлам
for fname in test_files:
    if not os.path.exists(fname):
        print(f"Файл {fname} не найден, пропускаем.")
        continue

    print(f"\n--- {fname} ---")
    original = read_file(fname)
    orig_size = len(original)

    # 1. RLE
    method = 'rle'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.rle')
    dec_path = os.path.join(folder, fname + '.rle.dec')
    encode_file(fname, enc_path, MS_RLE, MC_RLE)
    decode_file(enc_path, dec_path)
    recovered = read_file(dec_path)
    check_result(original, recovered, f"RLE (Ms={MS_RLE},Mc={MC_RLE})", enc_path, orig_size)

    # 2. Хаффман (классический)
    method = 'huffman'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.huf')
    dec_path = os.path.join(folder, fname + '.huf.dec')
    enc, codes, pad = huffman_encode(original)
    save_compressed(enc_path, enc, codes, pad)
    enc2, codes2, pad2 = load_compressed(enc_path)
    recovered = huffman_decode(enc2, codes2, pad2)
    write_file(dec_path, recovered)
    check_result(original, recovered, "Huffman (классический)", enc_path, orig_size)

    # 3. Хаффман (канонический)
    method = 'huffman_canonical'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.huf')
    dec_path = os.path.join(folder, fname + '.huf.dec')
    enc, lengths, pad = huffman_encode_canonical(original)
    save_compressed_canonical(enc_path, enc, lengths, pad)
    enc2, codes2, pad2 = load_compressed_canonical(enc_path)
    recovered = huffman_decode_canonical(enc2, codes2, pad2)
    write_file(dec_path, recovered)
    check_result(original, recovered, "Huffman (канонический)", enc_path, orig_size)

    # 4. LZ77
    method = 'lz77'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.lz77')
    dec_path = os.path.join(folder, fname + '.lz77.dec')
    enc = lz77_encode(original, WS_LZ77, LS_LZ77)
    write_file(enc_path, enc)
    recovered = lz77_decode(enc)
    write_file(dec_path, recovered)
    check_result(original, recovered, f"LZ77 (окно={WS_LZ77}, буфер={LS_LZ77})", enc_path, orig_size)

    # 5. LZSS
    method = 'lzss'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.lzss')
    dec_path = os.path.join(folder, fname + '.lzss.dec')
    enc = lzss_encode(original, WS_LZSS, LS_LZSS)
    write_file(enc_path, enc)
    recovered = lzss_decode(enc)
    write_file(dec_path, recovered)
    check_result(original, recovered, f"LZSS (окно={WS_LZSS}, буфер={LS_LZSS})", enc_path, orig_size)

    # 6. LZ78 (неограниченный)
    method = 'lz78'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.lz78')
    dec_path = os.path.join(folder, fname + '.lz78.dec')
    enc = lz78_encode(original)
    write_file(enc_path, enc)
    recovered = lz78_decode(enc)
    write_file(dec_path, recovered)
    check_result(original, recovered, "LZ78 (словарь неограничен)", enc_path, orig_size)

    # 7. LZ78 с ограниченным словарём
    method = 'lz78_limited'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.lz78')
    dec_path = os.path.join(folder, fname + '.lz78.dec')
    enc = lz78_encode_limited(original, MAX_DIC_LZ78_LIM)
    write_file(enc_path, enc)
    recovered = lz78_decode(enc)
    write_file(dec_path, recovered)
    check_result(original, recovered, f"LZ78 (словарь ограничен, max={MAX_DIC_LZ78_LIM})", enc_path, orig_size)

    # 8. LZW
    method = 'lzw'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.lzw')
    dec_path = os.path.join(folder, fname + '.lzw.dec')
    enc = lzw_encode(original, MAX_DIC_LZW)
    write_file(enc_path, enc)
    recovered = lzw_decode(enc, MAX_DIC_LZW)
    write_file(dec_path, recovered)
    check_result(original, recovered, f"LZW (словарь, max={MAX_DIC_LZW})", enc_path, orig_size)

    # 9. MTF
    method = 'mtf'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.mtf')
    dec_path = os.path.join(folder, fname + '.mtf.dec')
    enc = mtf_encode(original)
    write_file(enc_path, enc)
    recovered = mtf_decode(enc)
    write_file(dec_path, recovered)
    check_result(original, recovered, "MTF", enc_path, orig_size)

    # 10. BWT классический
    method = 'bwt'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.bwt')
    dec_path = os.path.join(folder, fname + '.bwt.dec')
    L, k = bwt(original)
    f = open(enc_path, 'wb')
    f.write(L)
    f.write(k.to_bytes(4, 'big'))
    f.close()
    # Чтение для декодирования
    f = open(enc_path, 'rb')
    data = f.read()
    f.close()
    if len(data) < 4:
        L_data = b''
        k2 = 0
    else:
        L_data = data[:-4]
        k2 = int.from_bytes(data[-4:], 'big')
    recovered = ibwt_fast(L_data, k2)
    write_file(dec_path, recovered)
    check_result(original, recovered, "BWT (классический)", enc_path, orig_size)

    # 11. BWT блочный
    method = 'bwt_block'
    folder = os.path.join(base_dir, method)
    enc_path = os.path.join(folder, fname + '.bwt')
    dec_path = os.path.join(folder, fname + '.bwt.dec')
    L_block, _ = block_bwt(original, BLOCK_SIZE_BWT)
    write_file(enc_path, L_block)
    recovered = block_ibwt_fast(L_block, 0, BLOCK_SIZE_BWT)
    write_file(dec_path, recovered)
    check_result(original, recovered, f"BWT (блочный, block_size={BLOCK_SIZE_BWT})", enc_path, orig_size)

print("\nГотово. Все сжатые и восстановленные файлы лежат в папке 'code_files'.")