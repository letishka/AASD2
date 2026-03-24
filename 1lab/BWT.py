def bwt(s):
    n = len(s)
    a = []                      # все циклические сдвиги
    for i in range(n):
        a.append(s[i:] + s[:i])
    a.sort()                    # сортируем
    L = bytes(x[-1] for x in a) # последний столбец
    k = a.index(s)              # индекс исходной строки
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
    if n == 0:
        return b""

    # подсчёт частот
    f = [0] * 256
    for b in L:
        f[b] += 1

    # начало диапазона для каждого байта
    p = [0] * 256
    s = 0
    for i in range(256):
        p[i] = s
        s += f[i]

    # массив следующего индекса
    c = p[:]        # текущая позиция
    nxt = [0] * n
    for i in range(n):
        ch = L[i]
        nxt[c[ch]] = i
        c[ch] += 1

    # восстановление строки
    r = bytearray()
    j = k
    for _ in range(n):
        j = nxt[j]
        r.append(L[j])
    return bytes(r)

def block_bwt(s, block_size=None):
    n = len(s)
    # Если блоки не нужны или строка целиком помещается в один блок
    if block_size is None or block_size <= 0 or n <= block_size:
        # Классический алгоритм
        return bwt(s)

    # Блочная обработка
    # Разбиваем на блоки
    blocks = [s[i:i+block_size] for i in range(0, n, block_size)]
    result = bytearray()
    # Записываем количество блоков
    result.extend(len(blocks).to_bytes(4, 'big'))
    for blk in blocks:
        # Обрабатываем блок классическим BWT
        L_blk, k_blk = bwt(blk)
        # Записываем длину L_blk, саму L_blk и индекс k_blk
        result.extend(len(L_blk).to_bytes(4, 'big'))
        result.extend(L_blk)
        result.extend(k_blk.to_bytes(4, 'big'))
    return bytes(result), 0


def block_ibwt_fast(L, k, block_size=None):

    if block_size is None or block_size <= 0:
        # Классическое обратное преобразование
        return ibwt_fast(L, k)

    # Блочная обработка: L содержит упакованные данные
    data = L
    if len(data) < 4:
        return b""
    num_blocks = int.from_bytes(data[:4], 'big')
    pos = 4
    result = bytearray()
    for _ in range(num_blocks):
        # Читаем длину блока
        if pos + 4 > len(data):
            break
        blk_len = int.from_bytes(data[pos:pos+4], 'big')
        pos += 4
        # Читаем L блока
        if pos + blk_len > len(data):
            break
        L_blk = data[pos:pos+blk_len]
        pos += blk_len
        # Читаем индекс k блока
        if pos + 4 > len(data):
            break
        k_blk = int.from_bytes(data[pos:pos+4], 'big')
        pos += 4
        # Декодируем блок классическим методом
        dec_blk = ibwt_fast(L_blk, k_blk)
        result.extend(dec_blk)
    return bytes(result)

def bwt_last_column(s, sa):
    #s - исходная байтовая строка
    #sa - суффиксный массив (список индексов, с которых начинаются отсортированные циклические сдвиги)
    # возвращает байтовую строку последнего столбца
    n = len(s)
    L = bytearray()
    for i in sa:
        pos = (i - 1) % n  # индекс последнего символа в циклическом сдвиге, начинающемся с i
        L.append(s[pos])
    return bytes(L)

def bwt_sa(s):

    n = len(s)
    if n == 0:
        return b"", 0
    # Индексы 0..n-1
    indices = list(range(n))
    # Сортируем индексы по циклическому сдвигу, начинающемуся с этого индекса
    indices.sort(key=lambda i: s[i:] + s[:i])
    # Последний столбец: для каждого индекса берём символ перед началом сдвига
    L = bytearray()
    for i in indices:
        pos = (i - 1) % n
        L.append(s[pos])
    # Индекс исходной строки: позиция, где циклический сдвиг равен s (i=0)
    k = indices.index(0)
    return bytes(L), k

if __name__ == "__main__":

    # Тестирование классики на banana
    s = b"banana"
    print("\nИсходная:", s)
    L, k = bwt(s)
    print("BWT (последний столбец):", L)
    print("Индекс:", k)
    s1 = ibwt_fast(L, k)
    print("Обратное (быстрое):", s1)
    s2 = ibwt(L, k)
    print("Обратное (медленное):", s2)
    if s1 == s and s2 == s:
        print("Классический тест пройден")
    else:
        print("Ошибка в классическом тесте")

    # Тестирование блочной обработки на banana
    print("\n--- Блочная обработка (block_size=2) ---")
    L_block, _ = block_bwt(s, block_size=2)
    s_block = block_ibwt_fast(L_block, 0, block_size=2)
    print("Исходная:", s)
    print("Восстановленная:", s_block)
    if s_block == s:
        print("Блочный тест (banana) пройден")
    else:
        print("Ошибка в блочном тесте (banana)")

    # Тестирование на русском тексте (классика)
    rus = "привет мир".encode('utf-8')
    print("\n--- Русский текст (классика) ---")
    print("Исходный:", rus)
    L_rus, k_rus = bwt(rus)
    print("BWT:", L_rus)
    print("Индекс:", k_rus)
    rus_dec = ibwt_fast(L_rus, k_rus)
    print("Восстановленный:", rus_dec)
    if rus_dec == rus:
        print("Русский классический тест пройден")
    else:
        print("Ошибка в русском классическом тесте")

    # Тестирование на русском тексте (блочная обработка)
    print("\n--- Русский текст (блоки по 4) ---")
    L_rus_block, _ = block_bwt(rus, block_size=4)
    rus_block_dec = block_ibwt_fast(L_rus_block, 0, block_size=4)
    print("Восстановленный:", rus_block_dec)
    if rus_block_dec == rus:
        print("Русский блочный тест пройден")
    else:
        print("Ошибка в русском блочном тесте")

    # Тест для bwt_last_column
    s = b"banana"
    n = len(s)
    # Строим циклические сдвиги с запоминанием исходного индекса
    shifts = []
    for i in range(n):
        shifts.append((s[i:] + s[:i], i))
    shifts.sort()  # сортируем по самому сдвигу (первому элементу)
    # Извлекаем индексы (суффиксный массив)
    sa = []
    for t, idx in shifts:
        sa.append(idx)
    L1 = bwt_last_column(s, sa)
    L2, _ = bwt(s)  # стандартный BWT
    print("bwt_last_column:", L1)
    print("bwt:", L2)
    if L1 == L2:
        print("Тест bwt_last_column пройден!")
    else:
        print("Тест bwt_last_column не пройден!")

    # --- Тестирование bwt_sa ---
    print("\n--- Тестирование bwt_sa ---")
    # 1. banana
    s = b"banana"
    L_sa, k_sa = bwt_sa(s)
    L_classic, k_classic = bwt(s)
    print("banana: bwt_sa =", L_sa, "индекс", k_sa)
    print("banana: bwt      =", L_classic, "индекс", k_classic)
    if L_sa == L_classic and k_sa == k_classic:
        print("Совпадает")
    else:
        print("НЕ совпадает!")

    # 2. русский текст
    rus = "привет мир".encode('utf-8')
    L_rus_sa, k_rus_sa = bwt_sa(rus)
    L_rus_classic, k_rus_classic = bwt(rus)
    print("\nРусский текст: bwt_sa =", L_rus_sa, "индекс", k_rus_sa)
    print("Русский текст: bwt      =", L_rus_classic, "индекс", k_rus_classic)
    if L_rus_sa == L_rus_classic and k_rus_sa == k_rus_classic:
        print("Совпадает")
    else:
        print("НЕ совпадает!")

    print("\nТестировка завершена!")
