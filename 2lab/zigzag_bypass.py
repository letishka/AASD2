
def zigzag_square(matrix):
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
    n = len(matrix)       # число строк
    m = len(matrix[0])    # число столбцов
    result = []
    # Проходим по всем диагоналям
    for s in range(n + m - 1):
        if s % 2 == 0:
            # Чётная диагональ: идём вверх
            i = s
            if i >= n:    i = n - 1
            while i >= 0:
                j = s - i
                if j >= 0 and j < m:
                    result.append(matrix[i][j])
                elif j < 0:    break
                i -= 1
        else:
            # Нечётная диагональ: идём вниз
            i = 0
            if s >= m:    i = s - (m - 1)
            while i < n:
                j = s - i
                if j >= 0 and j < m:
                    result.append(matrix[i][j])
                elif j < 0:    break
                i += 1
    return result

def inverse_zigzag(matrix, n=8):
    if len(matrix) != n*n:
        print("\nWrong length\n")
    mat = [[0]*n for _ in range(n)]
    idx = 0
    for s in range(2*n - 1):
        if s % 2 == 0:
            i = s if s < n else n-1
            while i >= 0:
                j = s - i
                if 0 <= j < n:
                    mat[i][j] = matrix[idx]
                    idx += 1
                i -= 1
        else:
            i = 0 if s < n else s - (n-1)
            while i < n:
                j = s - i
                if 0 <= j < n:
                    mat[i][j] = matrix[idx]
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
    print(f"  Ожидание: [1, 2, 4, 7, 5, 3, 6, 8, 9].\nРеальность: {zig}.\n")

    restored = inverse_zigzag(zig, 3)
    print("Востановленная:")
    for row in restored:
        print(row)

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
    print(f"  Ожидание: [1, 2, 5, 9, 6, 3, 4, 7, 10, 11, 8, 12].\nРеальность: {zigr}.\n")

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
    print(f"  Ожидание: [1, 2, 4, 7, 5, 3, 6, 8, 10, 11, 9, 12].\nРеальность: {zigr2}.\n")