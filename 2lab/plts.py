import os
import matplotlib.pyplot as plt
from PIL import Image
from write_to_file import (
    compress_image,
    write_compressed_file,
    read_compressed_file,
    decompress_image,
    compare_to_original,
)

# Список тестовых изображений (должны лежать в текущей папке)
IMAGES = {
    "Lenna": "Lenna.png",
    "Color": "color_image.png",
    "Grey": "grey_image.png",
    "BW_no_dither": "bw_no_dither.png",
    "BW_dither": "bw_dither.png",
}

QUALITY_VALUES = list(range(10, 91, 10))   # 10, 20, ..., 90
OUTPUT_DIR = "quality_results"             # папка для результатов
os.makedirs(OUTPUT_DIR, exist_ok=True)

for label, img_path in IMAGES.items():
    # Открываем изображение и обрезаем до кратного 8
    img = Image.open(img_path).convert('RGB')
    w = img.width - (img.width % 8)
    h = img.height - (img.height % 8)
    img = img.crop((0, 0, w, h))

    sizes = []  # размеры сжатых данных (байт)

    print(f"\n=== Обрабатываю {label} ({img_path}) ===")
    for q in QUALITY_VALUES:
        # Сжатие
        comp = compress_image(img, quality=q)

        # Сохраняем сжатый файл (можно во временный, но для отчёта сохраним по имени)
        comp_filename = os.path.join(OUTPUT_DIR, f"{label}_q{q}.raw")
        write_compressed_file(
            comp_filename,
            comp['width'], comp['height'],
            comp['cb_width'], comp['cb_height'],
            comp['cr_width'], comp['cr_height'],
            comp['q_table'],
            comp['compressed_data']
        )
        size = len(comp['compressed_data'])
        sizes.append(size)

        # Чтение и декомпрессия
        ww, hh, cbw, cbh, crw, crh, qtab, data = read_compressed_file(comp_filename)
        restored_img = decompress_image(ww, hh, cbw, cbh, crw, crh, qtab, data)

        # Сохраняем восстановленное изображение
        rest_filename = os.path.join(OUTPUT_DIR, f"{label}_q{q}_restored.png")
        restored_img.save(rest_filename)

        # Краткий отчёт в консоль
        psnr, max_diff = compare_to_original(img_path, rest_filename)
        print(f"  Q={q:2d}: size={size:7d} B  PSNR={psnr:.2f} dB  max_diff={max_diff:.1f}")

    # Строим график
    plt.figure(figsize=(8, 5))
    plt.plot(QUALITY_VALUES, sizes, 'bo-', linewidth=2, markersize=6)
    plt.xlabel('Качество (Quality)')
    plt.ylabel('Размер сжатых данных (байт)')
    plt.title(f'Зависимость размера от качества – {label}')
    plt.grid(True)
    graph_filename = os.path.join(OUTPUT_DIR, f"graph_{label}.png")
    plt.savefig(graph_filename, dpi=150)
    plt.close()
    print(f"График сохранён: {graph_filename}")

print("\nВсе графики и восстановленные изображения сохранены в папку", OUTPUT_DIR)