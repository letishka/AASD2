import math
import matplotlib.pyplot as plt

def entropy(data_bytes, code_len):
    n = len(data_bytes)
    chunks = n // code_len
    if chunks == 0: return 0.0
    freq = {}
    for i in range(chunks):
        chunk = data_bytes[i * code_len:(i + 1) * code_len]
        freq[chunk] = freq.get(chunk, 0) + 1
    h = 0.0
    for cnt in freq.values():
        p = cnt / chunks
        h -= p * math.log2(p)
    return h

if __name__ == "__main__":
    # 1. Чтение текста и фильтрация символов с кодом > 127
    f = open('english_text_low127.txt', 'r', encoding='utf-8')
    text = f.read()
    ascii_text = ''.join(ch for ch in text if ord(ch) <= 127)
    byte_data = ascii_text.encode('ascii')

    # 2. Расчёт энтропии
    code_lengths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    entropies = []
    for L in code_lengths:
        ent = entropy(byte_data, L)
        entropies.append(ent)
        print(f"Длина кода = {L} байт: энтропия = {ent:.4f} бит/символ")

    # 3. График
    plt.figure(figsize=(6, 4))
    plt.plot(code_lengths, entropies, marker='o', linestyle='-')
    plt.xlabel('Длина кода (байт)')
    plt.ylabel('Энтропия (бит на символ)')
    plt.title('Зависимость энтропии от длины равномерного кода')
    plt.grid(True)
    plt.savefig('graph_entropy.png', dpi=150, bbox_inches='tight')
    plt.show()