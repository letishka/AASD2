import os
from RLE import RLE, RLD
from BWT import bwt, ibwt_fast, block_bwt, block_ibwt_fast
from MTF import mtf_encode, mtf_decode
from Huffman import huffman_encode_canonical, huffman_decode_canonical
from Huffman import pack_huffman, unpack_huffman, build_canonical_codes
from LZ import lzss_encode, lzss_decode, lzw_encode, lzw_decode

# Параметры по результатам экспериментов
RLE_MS = 8
RLE_MC = 8
LZSS_WS = 4096
LZSS_LS = 32
LZW_MAX_DIC = 4096
BWT_BLOCK = 1024

# Вспомогательные функции Хаффмана
def ha_compress(data):
    enc, lengths, pad = huffman_encode_canonical(data)
    return pack_huffman(enc, lengths, pad)

def ha_decompress(data):
    enc, lengths, pad = unpack_huffman(data)
    codes = build_canonical_codes(lengths)
    return huffman_decode_canonical(enc, codes, pad)

# Компрессоры
def compress_rle(data):
    return RLE(data, RLE_MC, RLE_MS)

def decompress_rle(data):
    return RLD(data, RLE_MC, RLE_MS)

def compress_ha(data):
    return ha_compress(data)

def decompress_ha(data):
    return ha_decompress(data)

def compress_bwt_rle(data):
    return bwt_rle_compress(data, BWT_BLOCK)

def decompress_bwt_rle(data):
    return bwt_rle_decompress(data, BWT_BLOCK)

def compress_bwt_mtf_ha(data):
    return bwt_mtf_ha_compress(data, BWT_BLOCK)

def decompress_bwt_mtf_ha(data):
    return bwt_mtf_ha_decompress(data, BWT_BLOCK)

def compress_bwt_mtf_rle_ha(data):
    return bwt_mtf_rle_ha_compress(data, BWT_BLOCK)

def decompress_bwt_mtf_rle_ha(data):
    return bwt_mtf_rle_ha_decompress(data, BWT_BLOCK)

def compress_lzss(data):
    return lzss_encode(data, LZSS_WS, LZSS_LS)

def decompress_lzss(data):
    return lzss_decode(data)

def compress_lzss_ha(data):
    comp = lzss_encode(data, LZSS_WS, LZSS_LS)
    return ha_compress(comp)

def decompress_lzss_ha(data):
    comp = ha_decompress(data)
    return lzss_decode(comp)

def compress_lzw(data):
    return lzw_encode(data, LZW_MAX_DIC)

def decompress_lzw(data):
    return lzw_decode(data, LZW_MAX_DIC)

def compress_lzw_ha(data):
    comp = lzw_encode(data, LZW_MAX_DIC)
    return ha_compress(comp)

def decompress_lzw_ha(data):
    comp = ha_decompress(data)
    return lzw_decode(comp, LZW_MAX_DIC)

def bwt_rle_compress(data, block_size):
    if block_size is None or block_size <= 0:
        L, k = bwt(data)
        comp = RLE(L, 8, 8)
        return k.to_bytes(4, 'big') + comp
    else:
        L_block, _ = block_bwt(data, block_size)
        return RLE(L_block, 8, 8)

def bwt_rle_decompress(data, block_size):
    if block_size is None or block_size <= 0:
        k = int.from_bytes(data[:4], 'big')
        comp = data[4:]
        L = RLD(comp, 8, 8)
        return ibwt_fast(L, k)
    else:
        L = RLD(data, 8, 8)
        return block_ibwt_fast(L, 0, block_size)

def bwt_mtf_ha_compress(data, block_size):
    if block_size is None or block_size <= 0:
        L, k = bwt(data)
        M = mtf_encode(L)
        comp = ha_compress(M)
        return k.to_bytes(4, 'big') + comp
    else:
        result = bytearray()
        n = len(data)
        for start in range(0, n, block_size):
            block = data[start:start+block_size]
            L, k = bwt(block)
            M = mtf_encode(L)
            comp = ha_compress(M)
            result.extend(k.to_bytes(4, 'big'))
            result.extend(len(comp).to_bytes(4, 'big'))
            result.extend(comp)
        return bytes(result)

def bwt_mtf_ha_decompress(data, block_size):
    if block_size is None or block_size <= 0:
        k = int.from_bytes(data[:4], 'big')
        comp = data[4:]
        M = ha_decompress(comp)
        L = mtf_decode(M)
        return ibwt_fast(L, k)
    else:
        result = bytearray()
        pos = 0
        while pos < len(data):
            if pos + 4 > len(data):
                break
            k = int.from_bytes(data[pos:pos+4], 'big')
            pos += 4
            if pos + 4 > len(data):
                break
            blen = int.from_bytes(data[pos:pos+4], 'big')
            pos += 4
            if pos + blen > len(data):
                break
            comp = data[pos:pos+blen]
            pos += blen
            M = ha_decompress(comp)
            L = mtf_decode(M)
            result.extend(ibwt_fast(L, k))
        return bytes(result)

def bwt_mtf_rle_ha_compress(data, block_size):
    if block_size is None or block_size <= 0:
        L, k = bwt(data)
        M = mtf_encode(L)
        rle_comp = RLE(M, 8, 8)
        comp = ha_compress(rle_comp)
        return k.to_bytes(4, 'big') + comp
    else:
        result = bytearray()
        n = len(data)
        for start in range(0, n, block_size):
            block = data[start:start+block_size]
            L, k = bwt(block)
            M = mtf_encode(L)
            rle_comp = RLE(M, 8, 8)
            comp = ha_compress(rle_comp)
            result.extend(k.to_bytes(4, 'big'))
            result.extend(len(comp).to_bytes(4, 'big'))
            result.extend(comp)
        return bytes(result)

def bwt_mtf_rle_ha_decompress(data, block_size):
    if block_size is None or block_size <= 0:
        k = int.from_bytes(data[:4], 'big')
        comp = data[4:]
        rle_comp = ha_decompress(comp)
        M = RLD(rle_comp, 8, 8)
        L = mtf_decode(M)
        return ibwt_fast(L, k)
    else:
        result = bytearray()
        pos = 0
        while pos < len(data):
            if pos + 4 > len(data):
                break
            k = int.from_bytes(data[pos:pos+4], 'big')
            pos += 4
            if pos + 4 > len(data):
                break
            blen = int.from_bytes(data[pos:pos+4], 'big')
            pos += 4
            if pos + blen > len(data):
                break
            comp = data[pos:pos+blen]
            pos += blen
            rle_comp = ha_decompress(comp)
            M = RLD(rle_comp, 8, 8)
            L = mtf_decode(M)
            result.extend(ibwt_fast(L, k))
        return bytes(result)

def test_compressor(name, compress_func, decompress_func, data):
    compressed = compress_func(data)
    decompressed = decompress_func(compressed)
    if decompressed == data:
        return len(compressed), True
    else:
        return len(compressed), False

def run_tests(test_files):
    compressors = [
        ("RLE", compress_rle, decompress_rle),
        ("HA", compress_ha, decompress_ha),
        ("BWT+RLE", compress_bwt_rle, decompress_bwt_rle),
        ("BWT+MTF+HA", compress_bwt_mtf_ha, decompress_bwt_mtf_ha),
        ("BWT+MTF+RLE+HA", compress_bwt_mtf_rle_ha, decompress_bwt_mtf_rle_ha),
        ("LZSS", compress_lzss, decompress_lzss),
        ("LZSS+HA", compress_lzss_ha, decompress_lzss_ha),
        ("LZW", compress_lzw, decompress_lzw),
        ("LZW+HA", compress_lzw_ha, decompress_lzw_ha),
    ]

    results = []
    for fname in test_files:
        if os.path.exists(fname):
            f = open(fname, 'rb')
            data = f.read()
            f.close()
            orig_size = len(data)
            print("\n--- %s (размер %d байт) ---" % (fname, orig_size))
            row = {'file': fname, 'original': orig_size}
            for name, comp, decomp in compressors:
                comp_size, ok = test_compressor(name, comp, decomp, data)
                ratio = orig_size / comp_size if comp_size else 0
                row[name] = (comp_size, ratio, ok)
                status = "OK" if ok else "FAIL"
                print("  %s: %d -> %d байт (коэф. %.3f) %s" %
                      (name, orig_size, comp_size, ratio, status))
            results.append(row)
        else:
            print("Файл %s не найден, пропускаем." % fname)
    return results

def print_table(results, compressors):
    print("\n=== Сводная таблица коэффициентов сжатия ===")
    header = ["Файл", "Исх.размер"]
    for name, _, _ in compressors:
        header.append(name)
    print("\t".join(header))
    for row in results:
        line = [row['file'], str(row['original'])]
        for name, _, _ in compressors:
            comp_size, ratio, ok = row.get(name, (0,0,False))
            if ok:
                line.append("%d (%.3f)" % (comp_size, ratio))
            else:
                line.append("FAIL")
        print("\t".join(line))

# --------------------------------------------------------------
# Основной блок
# --------------------------------------------------------------
if __name__ == "__main__":
    compressors = [
        ("RLE", compress_rle, decompress_rle),
        ("HA", compress_ha, decompress_ha),
        ("BWT+RLE", compress_bwt_rle, decompress_bwt_rle),
        ("BWT+MTF+HA", compress_bwt_mtf_ha, decompress_bwt_mtf_ha),
        ("BWT+MTF+RLE+HA", compress_bwt_mtf_rle_ha, decompress_bwt_mtf_rle_ha),
        ("LZSS", compress_lzss, decompress_lzss),
        ("LZSS+HA", compress_lzss_ha, decompress_lzss_ha),
        ("LZW", compress_lzw, decompress_lzw),
        ("LZW+HA", compress_lzw_ha, decompress_lzw_ha),
    ]

    test_files = [
        'text.txt',
        'english_text_low127.txt',
        'setup.exe',
        'bw_photo.jpg',
        'bw_photo.png',
        'grey_photo.jpg',
        'color_photo.avif'
    ]

    results = run_tests(test_files)
    print_table(results, compressors)