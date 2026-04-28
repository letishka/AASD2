import math
from PIL import Image
from from_RGB_to_YCbCr import rgb_to_ycbcr, ycbcr_to_rgb

def channel_to_blocks(channel_bytes, width, height, block_size=8):
    blocks = []
    for by in range(0, height, block_size):
        for bx in range(0, width, block_size):
            block = [[0.0] * block_size for _ in range(block_size)]
            sum_val = 0.0
            count = 0
            for y in range(block_size):
                for x in range(block_size):
                    ix = bx + x
                    iy = by + y
                    if ix < width and iy < height:
                        val = channel_bytes[iy * width + ix]
                        block[y][x] = val
                        sum_val += val
                        count += 1
            if count < block_size * block_size and count > 0:
                avg = sum_val / count
                for y in range(block_size):
                    for x in range(block_size):
                        ix = bx + x
                        iy = by + y
                        if ix >= width or iy >= height:
                            block[y][x] = avg
            blocks.append(block)
    return blocks

def blocks_to_channel(blocks, width, height, block_size=8):
    data = bytearray(width * height)
    idx = 0
    for by in range(0, height, block_size):
        for bx in range(0, width, block_size):
            block = blocks[idx]; idx += 1
            for y in range(block_size):
                for x in range(block_size):
                    ix = bx + x
                    iy = by + y
                    if ix < width and iy < height:
                        val = block[y][x]
                        if val < 0: val = 0
                        if val > 255: val = 255
                        data[iy * width + ix] = int(round(val))
    return bytes(data)

def build_dct_matrix(n=8):
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if j == 0:
                C[i][j] = 1.0 / math.sqrt(n)
            else:
                C[i][j] = math.sqrt(2.0 / n) * math.cos(((2 * i + 1) * j * math.pi) / (2 * n))
    return C

def mat_mul(A, B):
    n, m, p = len(A), len(A[0]), len(B[0])
    res = [[0.0] * p for _ in range(n)]
    for i in range(n):
        for j in range(p):
            s = 0.0
            for k in range(m):
                s += A[i][k] * B[k][j]
            res[i][j] = s
    return res

def transpose(M):
    return [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]

def dct_2d(block):
    n = len(block)
    C = build_dct_matrix(n)
    Ct = transpose(C)
    temp = mat_mul(Ct, block)
    coeffs = mat_mul(temp, C)
    return coeffs

def idct_2d(coeffs):
    n = len(coeffs)
    C = build_dct_matrix(n)
    Ct = transpose(C)
    temp = mat_mul(C, coeffs)
    block = mat_mul(temp, Ct)
    return block

def quantize(coeffs, qtable):
    n, m = len(coeffs), len(coeffs[0])
    q = [[0]*m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            q[i][j] = int(round(coeffs[i][j] / qtable[i][j]))
    return q

def dequantize(q, qtable):
    n, m = len(q), len(q[0])
    coeffs = [[0.0]*m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            coeffs[i][j] = q[i][j] * qtable[i][j]
    return coeffs

def process_channel(channel_bytes, width, height, qtable):
    blocks = channel_to_blocks(channel_bytes, width, height, 8)
    quant_blocks = []
    for blk in blocks:
        coeffs = dct_2d(blk)
        quant_blocks.append(quantize(coeffs, qtable))
    restored_blocks = []
    for qblk in quant_blocks:
        coeffs = dequantize(qblk, qtable)
        restored_blocks.append(idct_2d(coeffs))
    return blocks_to_channel(restored_blocks, width, height, 8)

# Таблицы квантования
Q_Y = [
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
]

Q_C = [
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
]

if __name__ == "__main__":
    # Загружаем цветное изображение
    img = Image.open("color_image.png").convert('RGB')
    # Обрезаем до кратности 8
    w = img.width - (img.width % 8)
    h = img.height - (img.height % 8)
    img = img.crop((0, 0, w, h))

    rgb_bytes = img.tobytes()
    ycbcr_bytes = rgb_to_ycbcr(rgb_bytes)

    # Извлекаем компоненты
    y_bytes = bytes(ycbcr_bytes[i] for i in range(0, len(ycbcr_bytes), 3))
    cb_bytes = bytes(ycbcr_bytes[i] for i in range(1, len(ycbcr_bytes), 3))
    cr_bytes = bytes(ycbcr_bytes[i] for i in range(2, len(ycbcr_bytes), 3))

    # Применяем DCT + квантование к каждому каналу (полный размер)
    y_restored = process_channel(y_bytes, w, h, Q_Y)
    cb_restored = process_channel(cb_bytes, w, h, Q_C)
    cr_restored = process_channel(cr_bytes, w, h, Q_C)

    # Собираем YCbCr
    restored_ycbcr = bytearray()
    for i in range(w * h):
        restored_ycbcr.append(y_restored[i])
        restored_ycbcr.append(cb_restored[i])
        restored_ycbcr.append(cr_restored[i])

    restored_rgb = ycbcr_to_rgb(bytes(restored_ycbcr))
    restored_img = Image.frombytes('RGB', (w, h), restored_rgb)
    restored_img.save("restored_dct_ycbcr.jpg")
    print("Сохранено restored_dct_ycbcr.jpg")