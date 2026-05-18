import os
from functools import partial
from RLE import RLE, RLD
from BWT import bwt, ibwt_fast, block_bwt, block_ibwt_fast
from MTF import mtf_encode, mtf_decode
from Huffman import huffman_encode_canonical, huffman_decode_canonical
from Huffman import pack_huffman, unpack_huffman, build_canonical_codes
from LZ import lzss_encode, lzss_decode, lzw_encode, lzw_decode

# Параметры (результаты экспериментов)
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

# -------------------- BWT-каскады (с сохранением block_size-веток) --------------------
def bwt_rle_compress(data, block_size):
    if block_size is None or block_size <= 0:
        L, k = bwt(data)
        comp = RLE(L, RLE_MC, RLE_MS)
        return k.to_bytes(4, 'big') + comp
    else:
        result = bytearray()
        n = len(data)
        for start in range(0, n, block_size):
            block = data[start:start+block_size]
            L, k = bwt(block)
            comp = RLE(L, RLE_MC, RLE_MS)
            result.extend(k.to_bytes(4, 'big'))
            result.extend(len(comp).to_bytes(4, 'big'))
            result.extend(comp)
        return bytes(result)

def bwt_rle_decompress(data, block_size):
    if block_size is None or block_size <= 0:
        k = int.from_bytes(data[:4], 'big')
        comp = data[4:]
        L = RLD(comp, RLE_MC, RLE_MS)
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
            L = RLD(comp, RLE_MC, RLE_MS)
            result.extend(ibwt_fast(L, k))
        return bytes(result)

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
        rle_comp = RLE(M, RLE_MC, RLE_MS)
        comp = ha_compress(rle_comp)
        return k.to_bytes(4, 'big') + comp
    else:
        result = bytearray()
        n = len(data)
        for start in range(0, n, block_size):
            block = data[start:start+block_size]
            L, k = bwt(block)
            M = mtf_encode(L)
            rle_comp = RLE(M, RLE_MC, RLE_MS)
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
        M = RLD(rle_comp, RLE_MC, RLE_MS)
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
            M = RLD(rle_comp, RLE_MC, RLE_MS)
            L = mtf_decode(M)
            result.extend(ibwt_fast(L, k))
        return bytes(result)

# -------------------- Тестирование --------------------
def test_compressor(name, compress_func, decompress_func, data):
    compressed = compress_func(data)
    decompressed = decompress_func(compressed)
    ok = (decompressed == data)
    return len(compressed), len(decompressed), ok

def run_tests(test_files):
    compressors = [
        ("RLE", lambda d: RLE(d, RLE_MC, RLE_MS), lambda d: RLD(d, RLE_MC, RLE_MS)),
        ("HA", ha_compress, ha_decompress),
        ("BWT+RLE", partial(bwt_rle_compress, block_size=BWT_BLOCK), partial(bwt_rle_decompress, block_size=BWT_BLOCK)),
        ("BWT+MTF+HA", partial(bwt_mtf_ha_compress, block_size=BWT_BLOCK),
         partial(bwt_mtf_ha_decompress, block_size=BWT_BLOCK)),
        ("BWT+MTF+RLE+HA", partial(bwt_mtf_rle_ha_compress, block_size=BWT_BLOCK),
         partial(bwt_mtf_rle_ha_decompress, block_size=BWT_BLOCK)),
        ("LZSS", lambda d: lzss_encode(d, LZSS_WS, LZSS_LS), lzss_decode),
        ("LZSS+HA", lambda d: ha_compress(lzss_encode(d, LZSS_WS, LZSS_LS)), lambda d: lzss_decode(ha_decompress(d))),
        ("LZW", lambda d: lzw_encode(d, LZW_MAX_DIC), lambda d: lzw_decode(d, LZW_MAX_DIC)),
        ("LZW+HA", lambda d: ha_compress(lzw_encode(d, LZW_MAX_DIC)),
         lambda d: lzw_decode(ha_decompress(d), LZW_MAX_DIC)),
    ]

    results = []
    for fname in test_files:
        if not os.path.exists(fname):
            print("Файл %s не найден, пропускаем." % fname)
            continue
        f = open(fname, 'rb')
        data = f.read()
        orig_size = len(data)
        print("\n--- %s (исх. %d байт) ---" % (fname, orig_size))
        row = {'file': fname, 'original': orig_size}
        for name, comp_func, decomp_func in compressors:
            comp_size, decomp_size, ok = test_compressor(name, comp_func, decomp_func, data)
            ratio = orig_size / comp_size if comp_size else 0.0
            status = "OK" if ok else "FAIL"
            print("  %s: %d -> %d байт (коэф. %.3f) %s" % (name, orig_size, comp_size, ratio, status))
            row[name] = (comp_size, decomp_size, ratio, ok)
        results.append(row)
    return results

if __name__ == "__main__":
    test_files = ['text.txt',
                  'english_text_low127.txt',
                  'setup.exe',
                  'color_photo.avif',
                  'bw_photo.jpg.raw',
                  'bw_photo.png',
                  'grey_photo.jpg',
                  'bw_photo.png.raw',
                  'color_photo.avif.raw',
                  'grey_photo.jpg.raw',
                  'bw_photo.jpg',
                  'enwik7']

    # compressors для вывода таблицы
    compressors_info = [
        ("RLE", None, None),
        ("HA", None, None),
        ("BWT+RLE", None, None),
        ("BWT+MTF+HA", None, None),
        ("BWT+MTF+RLE+HA", None, None),
        ("LZSS", None, None),
        ("LZSS+HA", None, None),
        ("LZW", None, None),
        ("LZW+HA", None, None),
    ]
    run_tests(test_files)