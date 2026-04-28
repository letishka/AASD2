
def diff_encode_dc(dc_list):
    # Вход: список DC коэффициентов (первых коэффициентов каждого блока)
    # Выход: список разностных кодов

    if len(dc_list) == 0:
        return []
    diff = [dc_list[0]]
    for i in range(1, len(dc_list)):
        diff.append(dc_list[i] - dc_list[i-1])
    return diff

def rle_ac(ac_list):
    # Вход: список из 63 целых чисел (коэффициентов AC).
    # Выход: список пар (количество нулей, значение), завершающийся (0,0) если есть хвост из нулей.

    rle = []
    zeros = 0
    for coeff in ac_list:
        if coeff == 0:
            zeros = zeros + 1
        else:
            rle.append((zeros, coeff))
            zeros = 0
    # Если в конце остались нули, добавляем (0,0)
    if zeros > 0:    rle.append((0, 0))
    else:    pass
    return rle

def diff_decode_dc(diff_list):
    """Обратное разностное декодирование DC коэффициентов."""
    if not diff_list:
        return []
    dc = [diff_list[0]]
    for i in range(1, len(diff_list)):
        dc.append(dc[-1] + diff_list[i])
    return dc

def rle_decode_ac(rle_pairs):
    """Обратное RLE: восстанавливает список AC коэффициентов из пар (количество нулей, значение)."""
    ac = []
    for zeros, val in rle_pairs:
        if zeros == 0 and val == 0:
            break   # EOB
        ac.extend([0] * zeros)
        ac.append(val)
    return ac[:63]   # обрезаем до 63, если больше

if __name__ == "__main__":
    # Тест DC
    dc_orig = [100, 102, 105, 103, 110]
    diff = diff_encode_dc(dc_orig)
    dc_decoded = diff_decode_dc(diff)
    assert dc_decoded == dc_orig, "DC decode failed"
    print("DC decode OK")

    # Тест RLE
    ac_orig = [5, 0, 0, 3, 0, 1, 0, 0, 0, 2] + [0]*53
    rle = rle_ac(ac_orig)
    ac_decoded = rle_decode_ac(rle)
    # Дополняем до 63 нулями (если нужно)
    ac_decoded = ac_decoded + [0] * (63 - len(ac_decoded))
    assert ac_decoded[:len(ac_orig)] == ac_orig[:len(ac_decoded)], "RLE decode failed"
    print("RLE decode OK")