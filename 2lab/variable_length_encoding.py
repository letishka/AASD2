def get_category(value):
    if value == 0:    return 0
    else: return (abs(value).bit_length())

def vlc_encode_value(value, category):
    if category == 0:    return ""
    bits = bin(abs(value))[2:].zfill(category)
    if len(bits) == 0:
        print("\nInvalid value\n")
        return ""
    if value < 0:
        mask = int("1" * category, 2)
        val = abs(value) ^ mask
        bits = bin(val)[2:].zfill(category)
    return bits

def vlc_encode_dc(diff_list):
    return [(get_category(d), vlc_encode_value(d, get_category(d))) for d in diff_list]

def vlc_decode_dc(vlc_list):
    #Из списка (cat, bits) получаем разности DC
    diff = []
    for cat, bits in vlc_list:
        diff.append(decode_value_from_bits(bits, cat))
    return diff

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
            cat = get_category(coeff)
            bits = vlc_encode_value(coeff, cat)
            result.append((zeros, cat, bits))
            zeros = 0
    result.append((0, 0, ""))
    return result

def rle_vlc_decode_ac(pairs):
    ac = []
    for run, cat, bits in pairs:
        if run == 0 and cat == 0:    break
        if run == 15 and cat == 0:    ac.extend([0] * 16)
        else:
            ac.extend([0] * run)
            if cat > 0:
                ac.append(decode_value_from_bits(bits, cat))
    while len(ac) < 63:    ac.append(0)
    return ac[:63]

def decode_value_from_bits(bits, category):
    if category == 0:
        return 0
    val = int(bits, 2)
    if bits[0] == '0':
        min_neg = -((1 << category) - 1)
        return min_neg + val
    else:
        return val

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