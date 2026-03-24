import os

def huffman_encode(data):
    if not data:
        return b"", {}, 0

    # Частоты
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    # Список узлов: [частота, символ, левый, правый]
    nodes = [[f, c, None, None] for c, f in freq.items()]
    while len(nodes) > 1:
        nodes.sort(key=lambda x: x[0])
        left = nodes.pop(0)
        right = nodes.pop(0)
        nodes.append([left[0] + right[0], None, left, right])
    root = nodes[0]

    # Построение таблицы кодов через стек
    codes = {}
    stack = [(root, "")]
    while stack:
        node, code = stack.pop()
        if node[1] is not None:          # лист
            codes[node[1]] = code
        else:
            stack.append((node[2], code + "0"))
            stack.append((node[3], code + "1"))

    # Кодирование
    bits = "".join(codes[b] for b in data)
    pad = (8 - len(bits) % 8) % 8
    bits += "0" * pad
    enc = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return enc, codes, pad


def huffman_decode(enc, codes, pad):
    if not enc:
        return b""

    bits = "".join(f"{b:08b}" for b in enc)
    bits = bits[:len(bits) - pad] if pad else bits
    rev = {code: char for char, code in codes.items()}

    res = bytearray()
    cur = ""
    for bit in bits:
        cur += bit
        if cur in rev:
            res.append(rev[cur])
            cur = ""
    return bytes(res)


def save_compressed(fname, enc, codes, pad):
    with open(fname, "wb") as f:
        f.write(bytes([pad]))
        f.write(len(codes).to_bytes(2, "big"))
        for ch, code in codes.items():
            f.write(bytes([ch, len(code)]))
            code_bits = code + "0" * ((8 - len(code) % 8) % 8)
            code_bytes = bytes(int(code_bits[i:i+8], 2) for i in range(0, len(code_bits), 8))
            f.write(code_bytes)
        f.write(enc)


def load_compressed(fname):
    with open(fname, "rb") as f:
        pad = f.read(1)[0]
        num = int.from_bytes(f.read(2), "big")
        codes = {}
        for _ in range(num):
            ch = f.read(1)[0]
            l = f.read(1)[0]
            packed_len = (l + 7) // 8
            packed = f.read(packed_len)
            code_bits = "".join(f"{b:08b}" for b in packed)
            codes[ch] = code_bits[:l]
        enc = f.read()
    return enc, codes, pad

def build_canonical_codes(code_lengths):
    # по словарю {символ: длина_кода}.
    # возвращает словарь {символ: код_в_виде_строки_битов}.

    # Сортируем символы по длине, затем по значению символа
    items = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))
    codes = {}
    cur_code = 0
    prev_len = 0
    for ch, length in items:
        if length > prev_len:
            cur_code <<= (length - prev_len)
        # Формируем строку битов (без ведущих нулей)
        code_bin = bin(cur_code)[2:].zfill(length)
        codes[ch] = code_bin
        cur_code += 1
        prev_len = length
    return codes


def huffman_encode_canonical(data):
    #Возвращает (закодированные_байты, словарь_длин_кодов, количество_добавленных_битов).

    if not data:
        return b"", {}, 0

    # Частоты
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    # Построение дерева (как в классической версии)
    nodes = [[f, c, None, None] for c, f in freq.items()]
    while len(nodes) > 1:
        nodes.sort(key=lambda x: x[0])
        left = nodes.pop(0)
        right = nodes.pop(0)
        nodes.append([left[0] + right[0], None, left, right])
    root = nodes[0]

    # Получаем длины кодов обходом дерева (стек)
    code_lengths = {}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node[1] is not None:  # лист
            code_lengths[node[1]] = depth
        else:
            stack.append((node[2], depth + 1))
            stack.append((node[3], depth + 1))

    # Строим канонические коды
    codes = build_canonical_codes(code_lengths)

    # Кодирование
    bits = "".join(codes[b] for b in data)
    pad = (8 - len(bits) % 8) % 8
    bits += "0" * pad
    enc = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return enc, code_lengths, pad


def save_compressed_canonical(fname, enc, code_lengths, pad):
    #Сохраняет сжатые данные в файл. В заголовке хранятся только длины кодов.
    #Формат: 1 байт pad, 2 байта количество символов,
    #для каждого символа: 1 байт символ, 1 байт длина кода,затем закодированные данные.

    with open(fname, "wb") as f:
        f.write(bytes([pad]))
        f.write(len(code_lengths).to_bytes(2, "big"))
        for ch, length in code_lengths.items():
            f.write(bytes([ch, length]))
        f.write(enc)


def load_compressed_canonical(fname):
    #Загружает сжатые данные, восстановливает канонические коды по длинам.
    #Возвращает (закодированные_байты, словарь_канонических_кодов, pad).

    with open(fname, "rb") as f:
        pad = f.read(1)[0]
        num = int.from_bytes(f.read(2), "big")
        code_lengths = {}
        for _ in range(num):
            ch = f.read(1)[0]
            length = f.read(1)[0]
            code_lengths[ch] = length
        enc = f.read()
    # Восстанавливаем канонические коды
    codes = build_canonical_codes(code_lengths)
    return enc, codes, pad


def huffman_decode_canonical(enc, codes, pad):

    if not enc:
        return b""
    bits = "".join(f"{b:08b}" for b in enc)
    bits = bits[:len(bits) - pad] if pad else bits
    rev = {code: char for char, code in codes.items()}
    res = bytearray()
    cur = ""
    for bit in bits:
        cur += bit
        if cur in rev:
            res.append(rev[cur])
            cur = ""
    return bytes(res)

def pack_huffman(enc, code_lengths, pad):
    #Упаковывает закодированные данные Хаффмана в байтовую строку.
    #Формат: 1 байт pad, 2 байта количество символов,
    #для каждого символа: 1 байт символ, 1 байт длина кода, затем закодированные данные.

    out = bytearray()
    out.append(pad)
    out.extend(len(code_lengths).to_bytes(2, 'big'))
    for ch, length in code_lengths.items():
        out.append(ch)
        out.append(length)
    out.extend(enc)
    return bytes(out)

def unpack_huffman(data):
    """
    Распаковывает байтовую строку, полученную pack_huffman,
    возвращает (enc, code_lengths, pad).
    """
    if len(data) < 3:
        raise ValueError("Invalid Huffman data")
    pad = data[0]
    num = int.from_bytes(data[1:3], 'big')
    pos = 3
    code_lengths = {}
    for _ in range(num):
        if pos + 2 > len(data):
            raise ValueError("Incomplete header")
        ch = data[pos]
        length = data[pos+1]
        pos += 2
        code_lengths[ch] = length
    enc = data[pos:]
    return enc, code_lengths, pad

if __name__ == "__main__":
    data = b"abracadabra"
    enc, codes, pad = huffman_encode(data)
    save_compressed("test.huf", enc, codes, pad)
    enc2, codes2, pad2 = load_compressed("test.huf")
    dec = huffman_decode(enc2, codes2, pad2)
    if dec == data:
        print("\nКлассическая версия: OK")
    else:
        print("Классическая версия: ОШИБКА")
    os.remove("test.huf")

    # Тестирование канонической версии
    enc, code_lengths, pad = huffman_encode_canonical(data)
    save_compressed_canonical("test_canon.huf", enc, code_lengths, pad)
    enc2, codes2, pad2 = load_compressed_canonical("test_canon.huf")
    dec = huffman_decode_canonical(enc2, codes2, pad2)
    if dec == data:
        print("Каноническая версия: OK")
    else:
        print("Каноническая версия: ОШИБКА")
    os.remove("test_canon.huf")

    print("\nТестирование завершено!")