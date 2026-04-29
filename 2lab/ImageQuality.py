import math

def adapt_quantization_table(q_table, quality):
    if quality < 1:    quality = 1
    if quality > 99:    quality = 99
    if quality < 50:    S = 5000.0 / quality
    else:    S = 200.0 - 2.0 * quality

    n = len(q_table)
    m = len(q_table[0])
    new_table = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            val = (q_table[i][j] * S) / 100.0
            val = int(math.ceil(val))
            if val < 1:    val = 1
            if val > 255:    val = 255
            new_table[i][j] = val
    return new_table

# Стандартная таблица квантования для яркости (8x8)
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

if __name__ == "__main__":
    print("Исходная таблица квантования (Q=50):")
    for row in Q_Y:
        print(" ".join("%3d" % v for v in row))# Короткий тест: при Q=50 таблица не должна измениться

    q50 = adapt_quantization_table(Q_Y, 50)
    assert q50 == Q_Y, "Ошибка: при Q=50 таблица должна остаться неизменной"
    print("Тест Q=50 пройден")

    print("\nАдаптированная таблица для Q=90:")
    q90 = adapt_quantization_table(Q_Y, 90)
    for row in q90:
        print(" ".join("%3d" % v for v in row))

    print("\nАдаптированная таблица для Q=10:")
    q10 = adapt_quantization_table(Q_Y, 10)
    for row in q10:
        print(" ".join("%3d" % v for v in row))