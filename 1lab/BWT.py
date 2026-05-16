def bwt(s):
    n = len(s)
    a = []
    for i in range(n):
        a.append(s[i:] + s[:i])
    a.sort()
    L = bytes(x[-1] for x in a)
    k = a.index(s)
    return L, k

def ibwt(L, k):
    n = len(L)
    t = [b"" for _ in range(n)]
    for _ in range(n):
        for i in range(n):
            t[i] = bytes([L[i]]) + t[i]
        t.sort()
    return t[k]

def ibwt_fast(L, k):
    n = len(L)
    if n == 0: return b""

    f = [0] * 256
    for b in L: f[b] += 1

    p = [0] * 256
    s = 0
    for i in range(256):
        p[i] = s
        s += f[i]

    c = p[:]
    nxt = [0] * n
    for i in range(n):
        ch = L[i]
        nxt[c[ch]] = i
        c[ch] += 1

    r = bytearray()
    j = k
    for _ in range(n):
        j = nxt[j]
        r.append(L[j])
    return bytes(r)

def block_bwt(s, block_size=None):
    n = len(s)
    if block_size is None or block_size <= 0 or n <= block_size:
        return bwt(s)

    blocks = [s[i:i+block_size] for i in range(0, n, block_size)]
    result = bytearray()
    result.extend(len(blocks).to_bytes(4, 'big'))
    for blk in blocks:
        L_blk, k_blk = bwt(blk)
        result.extend(len(L_blk).to_bytes(4, 'big'))
        result.extend(L_blk)
        result.extend(k_blk.to_bytes(4, 'big'))
    return bytes(result), 0

def block_ibwt_fast(L, k, block_size=None):
    if block_size is None or block_size <= 0:
        return ibwt_fast(L, k)

    data = L
    if len(data) < 4: return b""
    num_blocks = int.from_bytes(data[:4], 'big')
    pos = 4
    result = bytearray()
    for _ in range(num_blocks):
        if pos + 4 > len(data): break
        blk_len = int.from_bytes(data[pos:pos+4], 'big')
        pos += 4
        if pos + blk_len > len(data): break
        L_blk = data[pos:pos+blk_len]
        pos += blk_len
        if pos + 4 > len(data): break
        k_blk = int.from_bytes(data[pos:pos+4], 'big')
        pos += 4
        dec_blk = ibwt_fast(L_blk, k_blk)
        result.extend(dec_blk)
    return bytes(result)

def bwt_last_column(s, sa):
    n = len(s)
    L = bytearray()
    for i in sa:
        pos = (i - 1) % n
        L.append(s[pos])
    return bytes(L)

def bwt_sa(s):
    n = len(s)
    if n == 0: return b"", 0
    indices = list(range(n))
    indices.sort(key=lambda i: s[i:] + s[:i])
    L = bytearray()
    for i in indices:
        pos = (i - 1) % n
        L.append(s[pos])
    k = indices.index(0)
    return bytes(L), k

if __name__ == "__main__":
    # banana
    t1 = b"banana"
    L1, k1 = bwt(t1)
    if ibwt_fast(L1, k1) != t1 or ibwt(L1, k1) != t1:
        print("ERROR: banana")
        exit(1)

    # banana hex
    t2 = bytes([0x62, 0x61, 0x6e, 0x61, 0x6e, 0x61])
    L2, k2 = bwt(t2)
    if ibwt_fast(L2, k2) != t2:
        print("ERROR: hex banana")
        exit(1)

    # text.txt (russian)
    with open("text.txt", "rb") as f:
        text_data = f.read()
    Lb2, _ = block_bwt(text_data, block_size=4096)
    if block_ibwt_fast(Lb2, 0, block_size=4096) != text_data:
        print("ERROR: text.txt")
        exit(1)

    # enwik7
    with open("enwik7", "rb") as f:
        enwik_data = f.read()
    Lb3, _ = block_bwt(enwik_data, block_size=5000)
    if block_ibwt_fast(Lb3, 0, block_size=5000) != enwik_data:
        print("ERROR: enwik7")
        exit(1)

    # bwt_sa check
    Lsa, ksa = bwt_sa(t1)
    if Lsa != L1 or ksa != k1:
        print("ERROR: bwt_sa")
        exit(1)

    print("Тестирование завершено!")