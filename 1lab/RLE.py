def RLE(string: bytes) -> bytes:
    if not string:
        return b''
    rle_string = bytearray()
    i = 0
    while i < len(string):
        count = 1
        while i + count < len(string) and string[i + count] == string[i] and count < 255:
            count += 1
        rle_string.append(count)
        rle_string.append(string[i])
        i += count
    return bytes(rle_string)

def RLD(string: bytes) -> bytes:
    rld_string = bytearray()
    i = 0
    while i < len(string):
        count = string[i]
        value = string[i+1]
        rld_string.extend([value] * count)
        i += 2
    return bytes(rld_string)

if __name__ == '__main__':
    string = "heeeeello wooooorld"
    string = string.encode('utf-8')
    rle_string = RLE(string)
    rld_string = RLD(rle_string)
    print("Начальная строка:", string)
    print("\nЗакодированная строка:", rle_string)
    print("\nРаскодированная строка:", rld_string)
    if rld_string == string:
        print("\nSuccess!")
    else:
        print("\nFailure(")


    # if string[i] == string[len(string) - 1]: break
    #
    # if string[i] == string[i + 1]:
    #     count += 1
    #     rle_string.append(string[i] | 0x80)
    # elif (string[i] != string[i + 1] and (string[i] & 0x80) != 0) or count == 127:
    #     rle_string.append(count)
    #     rle_string.append(string[i])
    #     count = 0
    # elif string[i] != string[i + 1]:
    #     count += 1
    # elif string[i] == string[i + 1] and (string[i] & 0x80) == 1:
    #     rle_string.append(count)
    #     rle_string.append(string[i])
    #     count = 0