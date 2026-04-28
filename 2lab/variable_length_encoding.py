def get_category(value):
    if value == 0:
        return 0
    abs_val = abs(value)
    cat = 1
    bound = 1
    while abs_val > bound:
        cat += 1
        bound = (1 << cat) - 1
    return cat

def vlc_encode_value(value, category):
    if category == 0:
        return ""
    if value > 0:
        bits = bin(value)[2:]
        if len(bits) > category:
            raise ValueError("Value too large")
        return bits.zfill(category)
    else:
        min_neg = -((1 << category) - 1)
        offset = value - min_neg
        bits = bin(offset)[2:]
        return bits.zfill(category)

def vlc_encode_dc(diff_list):
    return [(get_category(d), vlc_encode_value(d, get_category(d))) for d in diff_list]

def rle_vlc_encode_ac(ac_list):
    result = []
    zeros = 0
    for coeff in ac_list:
        if coeff == 0:
            zeros += 1
            if zeros == 16:
                result.append((15, 0, ""))
                zeros = 0
        else:
            while zeros >= 16:
                result.append((15, 0, ""))
                zeros -= 16
            cat = get_category(coeff)
            bits = vlc_encode_value(coeff, cat)
            result.append((zeros, cat, bits))
            zeros = 0
    result.append((0, 0, ""))
    return result

# ----- Декодирование -----
def decode_value_from_bits(bits, category):
    if category == 0:
        return 0
    val = int(bits, 2)
    if bits[0] == '0':
        min_neg = -((1 << category) - 1)
        return min_neg + val
    else:
        return val

def vlc_decode_dc(vlc_list):
    """Из списка (cat, bits) получаем разности DC."""
    diff = []
    for cat, bits in vlc_list:
        diff.append(decode_value_from_bits(bits, cat))
    return diff

def rle_vlc_decode_ac(pairs):
    ac = []
    for run, cat, bits in pairs:
        if run == 0 and cat == 0:
            break
        if run == 15 and cat == 0:      # ZRL
            ac.extend([0] * 16)
        else:
            ac.extend([0] * run)
            if cat > 0:
                ac.append(decode_value_from_bits(bits, cat))
    while len(ac) < 63:
        ac.append(0)
    return ac[:63]

if __name__ == "__main__":
    # Тест DC VLC
    diff_orig = [5, -3, 12, 0, -8]
    vlc = vlc_encode_dc(diff_orig)
    diff_decoded = vlc_decode_dc(vlc)
    assert diff_decoded == diff_orig, "DC VLC decode failed"
    print("DC VLC decode OK")

    # Тест AC RLE+VLC
    ac_orig = [5, 0, 0, -2, 0, 0, 0, 1, 0] + [0]*54
    encoded = rle_vlc_encode_ac(ac_orig)
    ac_decoded = rle_vlc_decode_ac(encoded)
    assert ac_decoded == ac_orig, "AC RLE+VLC decode failed"
    print("AC RLE+VLC decode OK")