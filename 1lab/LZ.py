def lz77_encode(dta, ws, ls):
    c = bytearray()
    i = 0
    n = len(dta)

    while i < n:
        wstart = max(0, i - ws)
        lend = min(i + ls, n)

        bo = 0
        bl = 0

        j = wstart
        while j < i:
            k = 0
            while (i + k < lend) and (j + k < i) and (dta[j + k] == dta[i + k]):
                k += 1
            if k > bl:
                bl = k
                bo = i - j
            j += 1

        if bl >= 3:
            c.extend(bo.to_bytes(2, 'big'))
            c.extend(bl.to_bytes(2, 'big'))
            if i + bl < n:
                c.append(dta[i + bl])
            i += bl + 1
        else:
            c.extend((0).to_bytes(2, 'big'))
            c.extend((0).to_bytes(2, 'big'))
            c.append(dta[i])
            i += 1

    return bytes(c)


def lz77_decode(c):
    d = bytearray()
    pos = 0
    while pos < len(c):
        off = int.from_bytes(c[pos:pos+2], 'big')
        ln = int.from_bytes(c[pos+2:pos+4], 'big')
        pos += 4
        if off == 0 and ln == 0:
            if pos >= len(c):
                break
            nxt = c[pos]
            pos += 1
            d.append(nxt)
        else:
            start = len(d) - off
            for _ in range(ln):
                d.append(d[start + _])
            if pos < len(c):
                nxt = c[pos]
                pos += 1
                d.append(nxt)

    return bytes(d)

def lzss_encode(dta, ws, ls):
    c = bytearray()
    i = 0
    n = len(dta)
    toks = []

    while i < n:
        wstart = max(0, i - ws)
        lend = min(i + ls, n)

        bo = 0
        bl = 0

        j = wstart
        while j < i:
            k = 0
            while (i + k < lend) and (j + k < i) and (dta[j + k] == dta[i + k]):
                k += 1
            if k > bl:
                bl = k
                bo = i - j
            j += 1

        if bl >= 3:
            toks.append((1, bo, bl))
            i += bl
        else:
            toks.append((0, dta[i]))
            i += 1

        if len(toks) == 8 or i == n:
            flags = 0
            for idx, tok in enumerate(toks):
                if tok[0] == 1:
                    flags |= (1 << idx)
            c.append(flags)

            for tok in toks:
                if tok[0] == 0:
                    c.append(tok[1])
                else:
                    c.extend(tok[1].to_bytes(2, 'big'))
                    c.append(tok[2])

            toks = []

    return bytes(c)

def lzss_decode(c):
    d = bytearray()
    pos = 0
    while pos < len(c):
        flags = c[pos]
        pos += 1
        bit = 0
        while bit < 8 and pos < len(c):
            if (flags >> bit) & 1:
                if pos + 2 >= len(c):
                    break
                off = int.from_bytes(c[pos:pos+2], 'big')
                pos += 2
                ln = c[pos]
                pos += 1
                start = len(d) - off
                for _ in range(ln):
                    d.append(d[start + _])
            else:
                d.append(c[pos])
                pos += 1
            bit += 1

    return bytes(d)

def lz78_encode(dta):
    dic = {}
    out = []
    cur = bytearray()
    idx = 1

    for b in dta:
        cur.append(b)
        key = bytes(cur)
        if key in dic:
            continue
        else:
            prev = bytes(cur[:-1]) if len(cur) > 1 else b''
            prev_idx = dic.get(prev, 0)
            out.append((prev_idx, b))
            dic[key] = idx
            idx += 1
            cur = bytearray()

    if cur:
        prev_idx = dic.get(bytes(cur), 0)
        out.append((prev_idx, -1))   # -1 означает "нет символа"

    c = bytearray()
    c.extend(len(out).to_bytes(4, 'big'))   # количество пар
    for pi, ch in out:
        c.extend(pi.to_bytes(4, 'big'))
        if ch == -1:
            c.append(0)      # маркер
        else:
            c.append(ch)
    return bytes(c)


def lz78_encode_limited(dta, max_dic):
    dic = {}
    out = []
    cur = bytearray()
    idx = 1

    for b in dta:
        cur.append(b)
        key = bytes(cur)
        if key in dic:
            continue
        else:
            prev = bytes(cur[:-1]) if len(cur) > 1 else b''
            prev_idx = dic.get(prev, 0)
            out.append((prev_idx, b))

            if len(dic) < max_dic:
                dic[key] = idx
                idx += 1
            else:
                dic = {}
                idx = 1
                dic[key] = idx
                idx += 1

            cur = bytearray()

    if cur:
        prev_idx = dic.get(bytes(cur), 0)
        out.append((prev_idx, -1))

    c = bytearray()
    c.extend(len(out).to_bytes(4, 'big'))
    for pi, ch in out:
        c.extend(pi.to_bytes(4, 'big'))
        if ch == -1:
            c.append(0)
        else:
            c.append(ch)
    return bytes(c)


def lz78_decode(c):
    pos = 0
    if pos + 4 > len(c):
        return b''
    num_pairs = int.from_bytes(c[pos:pos+4], 'big')
    pos += 4

    dic = {}
    d = bytearray()
    idx = 1

    for _ in range(num_pairs):
        if pos + 4 > len(c):
            break
        pi = int.from_bytes(c[pos:pos+4], 'big')
        pos += 4
        if pos >= len(c):
            break
        ch = c[pos]
        pos += 1

        if pi == 0 and ch == 0:
            continue   # не должно встречаться, но на всякий случай

        if pi == 0:
            d.append(ch)
            dic[idx] = bytearray([ch])
        else:
            prev = dic[pi]
            d.extend(prev)
            if ch != 0:          # нормальный символ
                d.append(ch)
                dic[idx] = prev + bytearray([ch])
            else:                # фиктивная пара – только ссылка
                dic[idx] = prev
        idx += 1

    return bytes(d)

def lzw_encode(dta, max_dic):
    dic = {bytes([i]): i for i in range(256)}
    nxt = 256
    out = []
    cur = bytearray()
    for b in dta:
        cur.append(b)
        if bytes(cur) in dic:
            continue
        else:
            prev = bytes(cur[:-1])
            out.append(dic[prev])
            if nxt < max_dic:
                dic[bytes(cur)] = nxt
                nxt += 1
            cur = bytearray([b])
    if cur:
        out.append(dic[bytes(cur)])
    c = bytearray()
    for code in out:
        c.extend(code.to_bytes(2, 'big'))
    return bytes(c)

def lzw_decode(c, max_dic=4096):
    dic = {i: bytes([i]) for i in range(256)}
    nxt = 256
    d = bytearray()
    pos = 0
    prev = None
    while pos < len(c):
        code = int.from_bytes(c[pos:pos+2], 'big')
        pos += 2
        if code in dic:
            entry = dic[code]
        else:
            if code == nxt and prev is not None:
                entry = dic[prev] + bytes([dic[prev][0]])
            else:
                entry = b''
        if entry:
            d.extend(entry)
            if prev is not None and nxt < max_dic:
                dic[nxt] = dic[prev] + bytes([entry[0]])
                nxt += 1
            prev = code
    return bytes(d)

if __name__ == "__main__":
    test_data = b"AAAAABBBBBCCCCCDDDDD" * 20
    print("Исходные данные:", len(test_data), "байт")
    print()

    # LZ77
    print("--- LZ77 ---")
    comp = lz77_encode(test_data, 1024, 16)
    decomp = lz77_decode(comp)
    ratio = len(comp) / len(test_data)
    print("Сжато:", len(comp), "байт, коэффициент:", ratio)
    print("Декодировано верно?", decomp == test_data)
    print()

    # LZSS
    print("--- LZSS ---")
    comp = lzss_encode(test_data, 1024, 16)
    decomp = lzss_decode(comp)
    ratio = len(comp) / len(test_data)
    print("Сжато:", len(comp), "байт, коэффициент:", ratio)
    print("Декодировано верно?", decomp == test_data)
    print()

    # LZ78
    print("--- LZ78 ---")
    comp = lz78_encode(test_data)
    decomp = lz78_decode(comp)
    ratio = len(comp) / len(test_data)
    print("Сжато:", len(comp), "байт, коэффициент:", ratio)
    print("Декодировано верно?", decomp == test_data)
    print()

    # LZ78 ограниченный
    print("--- LZ78 с ограничением словаря 256 ---")
    comp = lz78_encode_limited(test_data, 256)
    decomp = lz78_decode(comp)
    ratio = len(comp) / len(test_data)
    print("Сжато:", len(comp), "байт, коэффициент:", ratio)
    print("Декодировано верно?", decomp == test_data)
    print()

    # LZW
    print("--- LZW ---")
    comp = lzw_encode(test_data, 4096)
    decomp = lzw_decode(comp, 4096)
    ratio = len(comp) / len(test_data)
    print("Сжато:", len(comp), "байт, коэффициент:", ratio)
    print("Декодировано верно?", decomp == test_data)
    print()

    # Исследование LZSS
    print("=== Исследование LZSS ===")
    ws_values = [256, 512, 1024, 2048]
    ls_values = [8, 16, 32]
    for ws in ws_values:
        for ls in ls_values:
            comp = lzss_encode(test_data, ws, ls)
            ratio = len(comp) / len(test_data)
            print(f"Окно={ws:5d}, буфер={ls:2d}, коэффициент={ratio:.4f}")
    print()

    # Исследование LZW
    print("=== Исследование LZW ===")
    dict_sizes = [256, 512, 1024, 2048, 4096]
    for ds in dict_sizes:
        comp = lzw_encode(test_data, ds)
        ratio = len(comp) / len(test_data)
        print(f"Словарь={ds:4d}, коэффициент={ratio:.4f}")