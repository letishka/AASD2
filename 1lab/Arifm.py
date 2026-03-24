def encode(data, probs):
    # Вычисляем накопленные вероятности
    cum = {}
    total = 0.0
    for b, p in sorted(probs.items()):
        cum[b] = total
        total += p

    low = 0.0
    high = 1.0
    for b in data:
        r = high - low
        low = low + r * cum[b]
        high = low + r * probs[b]
    return low, high   # возвращаем обе границы


def experiment():
    # Модель: два символа с равной вероятностью 0.5
    probs = {65: 0.5, 66: 0.5}
    # Строка из одного символа 'A' (будем увеличивать длину)
    data = b'A'

    n = 1
    while True:
        cur_data = data * n
        low, high = encode(cur_data, probs)
        print(f"n={n:5d} | low={low:.16f} | high={high:.16f} | diff={high-low:.2e}")
        if low == high:
            print(f"\nГраницы совпали при n = {n}")
            break
        n += 1

        # Опционально: ограничим максимальное n, чтобы не ждать вечность
        if n > 2000:
            print("Слишком долго, прерываем (границы ещё не совпали)")
            break


if __name__ == "__main__":
    # Пример кодирования
    probs = {65: 0.5, 66: 0.5}
    data = b"AB"
    low, high = encode(data, probs)
    print(f"Кодирование {data}: low={low}, high={high}\n")

    experiment()
    print("Тестирование завершено!")