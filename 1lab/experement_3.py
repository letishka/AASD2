import os
import matplotlib.pyplot as plt
from BWT import bwt
from MTF import mtf_encode
from Entropy import entropy
from LZ import lzss_encode, lzw_encode

def block_bwt_mtf(data, block_size):
    result = bytearray()
    n = len(data)
    start = 0
    while start < n:
        end = start + block_size
        block = data[start:end] if end <= n else data[start:]
        if block:
            L, _ = bwt(block)
            M = mtf_encode(L)
            result.extend(M)
        start += block_size
    return bytes(result)

def entropy_of_block_bwt_mtf(data, block_size):
    transformed = block_bwt_mtf(data, block_size)
    return entropy(transformed, 1) if transformed else 0.0

def original_entropy(data):
    return entropy(data, 1)

def run_entropy_experiment(files, block_sizes):
    plt.figure(figsize=(10, 6))
    for fname in files:
        if not os.path.exists(fname):
            print(f"Файл {fname} не найден, пропускаем.")
            continue
        with open(fname, 'rb') as f:
            data = f.read()
        # Ограничиваем размер для ускорения
        max_sample = 1024 * 1024  # 1 МБ
        if len(data) > max_sample:
            data = data[:max_sample]
            print(f"{fname}: используем первые {max_sample} байт")
        ent_orig = original_entropy(data)
        print(f"{fname}: исходная энтропия = {ent_orig:.4f}")
        ent_values = []
        for bs in block_sizes:
            ent = entropy_of_block_bwt_mtf(data, bs)
            ent_values.append(ent)
            print(f"  блок {bs:5d} -> энтропия {ent:.4f}")
        plt.plot(block_sizes, ent_values, marker='o', label=fname)
        plt.axhline(y=ent_orig, linestyle='--', color='gray', alpha=0.5,
                    label=f"{fname} исходная" if fname == files[0] else "")
    plt.xlabel('Размер блока (байт)')
    plt.ylabel('Энтропия (бит на байт)')
    plt.title('Зависимость энтропии после BWT+MTF от размера блока')
    plt.legend()
    plt.grid(True)
    plt.savefig('entropy_bwt_mtf.png')
    # plt.show()  # отключаем интерактивный показ

def lzss_ratio(data, ws, ls):
    comp = lzss_encode(data, ws, ls)
    return len(data) / len(comp) if comp else 0

def run_lzss_experiment(files, ws_fixed, ls_values):
    plt.figure(figsize=(10, 6))
    for fname in files:
        if not os.path.exists(fname):
            print(f"Файл {fname} не найден, пропускаем.")
            continue
        with open(fname, 'rb') as f:
            data = f.read()
        max_sample = 1024 * 1024
        if len(data) > max_sample:
            data = data[:max_sample]
            print(f"{fname}: используем первые {max_sample} байт")
        ratios = []
        for ls in ls_values:
            r = lzss_ratio(data, ws_fixed, ls)
            ratios.append(r)
            print(f"{fname}, ws={ws_fixed}, ls={ls}: коэф. {r:.4f}")
        plt.plot(ls_values, ratios, marker='o', label=fname)
    plt.xlabel('Размер буфера предварительного просмотра (байт)')
    plt.ylabel('Коэффициент сжатия')
    plt.title(f'Зависимость коэффициента сжатия LZSS от размера буфера (ws={ws_fixed})')
    plt.legend()
    plt.grid(True)
    plt.savefig('lzss_ls.png')
    # plt.show()

def lzw_ratio(data, max_dic):
    comp = lzw_encode(data, max_dic)
    return len(data) / len(comp) if comp else 0

def run_lzw_experiment(files, dict_sizes):
    plt.figure(figsize=(10, 6))
    for fname in files:
        if not os.path.exists(fname):
            print(f"Файл {fname} не найден, пропускаем.")
            continue
        with open(fname, 'rb') as f:
            data = f.read()
        max_sample = 1024 * 1024
        if len(data) > max_sample:
            data = data[:max_sample]
            print(f"{fname}: используем первые {max_sample} байт")
        ratios = []
        for ds in dict_sizes:
            r = lzw_ratio(data, ds)
            ratios.append(r)
            print(f"{fname}, dict={ds}: коэф. {r:.4f}")
        plt.plot(dict_sizes, ratios, marker='o', label=fname)
    plt.xlabel('Максимальный размер словаря')
    plt.ylabel('Коэффициент сжатия')
    plt.title('Зависимость коэффициента сжатия LZW от размера словаря')
    plt.legend()
    plt.grid(True)
    plt.savefig('lzw_dict.png')
    # plt.show()

if __name__ == "__main__":
    # Используем только один файл для ускорения (можно заменить на существующий)
    test_files = ['text.txt']   # если нет, замените на 'english_text_low127.txt' или другой

    # Уменьшенные диапазоны параметров
    block_sizes = [64, 128, 256, 512, 1024, 2048, 4096]  # 7 значений (можно сократить)
    # block_sizes = [256, 1024, 4096]   # быстрый вариант
    run_entropy_experiment(test_files, block_sizes)

    ws_fixed = 4096
    ls_values = [8, 16, 32, 64, 128]   # 5 значений
    run_lzss_experiment(test_files, ws_fixed, ls_values)

    dict_sizes = [256, 512, 1024, 2048, 4096]   # 5 значений
    run_lzw_experiment(test_files, dict_sizes)