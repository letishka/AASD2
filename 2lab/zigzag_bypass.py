
def zigzag_square(matrix):
    # Вход: список списков (матрица).
    # Выход: плоский список значений в порядке зигзаг-обхода

    n = len(matrix)
    result = []
    # Проходим по всем диагоналям (сумма индексов от 0 до 2*n-2)
    for s in range(2 * n - 1):
        if s % 2 == 0:
            # Чётная диагональ: идём сверху вниз (i от max(0, s-(n-1)) до min(s, n-1))
            i = s
            if i >= n:
                i = n - 1
            while i >= 0 and s - i < n:
                j = s - i
                if j >= 0 and j < n:
                    result.append(matrix[i][j])
                i = i - 1
        else:
            # Нечётная диагональ: идём снизу вверх (i от min(s, n-1) до max(0, s-(n-1)))
            i = 0
            if s >= n:
                i = s - (n - 1)
            while i < n and s - i >= 0:
                j = s - i
                if j >= 0 and j < n:
                    result.append(matrix[i][j])
                i = i + 1
    return result


def zigzag_rect(matrix):
    #Вход: список списков (матрица)
    #Выход: плоский список значений в порядке зигзаг-обхода

    n = len(matrix)       # число строк
    m = len(matrix[0])    # число столбцов
    result = []
    # Проходим по всем диагоналям
    for s in range(n + m - 1):
        if s % 2 == 0:
            # Чётная диагональ: идём сверху вниз
            i = s
            if i >= n:
                i = n - 1
            while i >= 0:
                j = s - i
                if j >= 0 and j < m:    result.append(matrix[i][j])
                else:
                    if j < 0:    break
                i = i - 1
        else:
            # Нечётная диагональ: идём снизу вверх
            i = 0
            if s >= m:
                i = s - (m - 1)
            while i < n:
                j = s - i
                if j >= 0 and j < m:
                    result.append(matrix[i][j])
                else:
                    if j < 0:
                        break
                i = i + 1
    return result

def inverse_zigzag(flat, n=8):
    if len(flat) != n*n:
        raise ValueError("Wrong length")
    mat = [[0]*n for _ in range(n)]
    idx = 0
    for s in range(2*n - 1):
        if s % 2 == 0:
            i = s if s < n else n-1
            while i >= 0:
                j = s - i
                if 0 <= j < n:
                    mat[i][j] = flat[idx]
                    idx += 1
                i -= 1
        else:
            i = 0 if s < n else s - (n-1)
            while i < n:
                j = s - i
                if 0 <= j < n:
                    mat[i][j] = flat[idx]
                    idx += 1
                i += 1
    return mat

if __name__ == "__main__":

    mat = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    print("Квадратная матрица 3x3:")
    for row in mat:
        print(row)
    zig = zigzag_square(mat)
    print("Зигзаг-обход:", zig)
    # Ожидается: [1, 2, 4, 7, 5, 3, 6, 8, 9]

    restored = inverse_zigzag(zig, 3)
    assert restored == mat, "inverse_zigzag failed"
    print("inverse_zigzag OK")
    print()

    mat_rect_h = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12]
    ]
    print("Прямоугольная матрица 3x4:")
    for row in mat_rect_h:
        print(row)
    zigr = zigzag_rect(mat_rect_h)
    print("Зигзаг-обход:", zigr)
    # Должно: [1, 2, 5, 9, 6, 3, 4, 7, 10, 11, 8, 12]

    print()

    mat_rect_v = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 11, 12]
    ]
    print("Прямоугольная матрица 4x3:")
    for row in mat_rect_v:
        print(row)
    zigr2 = zigzag_rect(mat_rect_v)
    print("Зигзаг-обход:", zigr2)
    # Должно: [1, 2, 4, 7, 5, 3, 6, 8, 10, 11, 9, 12]