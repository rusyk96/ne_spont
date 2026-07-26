import json
import urllib.request
import struct

MANIFEST_URL = "https://raw.githubusercontent.com/rusyk96/ne_spont/main/webp/manifest.json"
RAW_BASE_URL = "https://raw.githubusercontent.com/rusyk96/ne_spont/main/webp/"

def get_webp_dimensions(url):
    """Скачивает только первые 30 байт файла для определения ширины и высоты WebP"""
    try:
        req = urllib.request.Request(url, headers={'Range': 'bytes=0-30'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
            
            # Проверяем сигнатуру WEBP
            if len(data) >= 30 and data[8:12] == b'WEBP':
                # Читаем чанк VP8 / VP8L / VP8X
                chunk_type = data[12:16]
                
                if chunk_type == b'VP8 ':
                    # VP8 Lossy
                    w, h = struct.unpack('<HH', data[26:30])
                    width = w & 0x3FFF
                    height = h & 0x3FFF
                elif chunk_type == b'VP8L':
                    # VP8 Lossless
                    b1, b2, b3, b4 = struct.unpack('<BBBB', data[21:25])
                    width = 1 + (((b2 & 0x3F) << 8) | b1)
                    height = 1 + (((b4 & 0x0F) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
                elif chunk_type == b'VP8X':
                    # VP8 Extended (профиль с прозрачностью/метаданными)
                    width = 1 + struct.unpack('<I', data[24:27] + b'\x00')[0]
                    height = 1 + struct.unpack('<I', data[27:30] + b'\x00')[0]
                else:
                    return None, None
                
                return width, height
    except Exception as e:
        print(f"Ошибка при считывании {url}: {e}")
    return None, None

def process_manifest():
    print("📥 Скачиваем текущий manifest.json...")
    req = urllib.request.urlopen(MANIFEST_URL)
    raw_data = json.loads(req.read().decode('utf-8'))

    updated_manifest = []
    total = len(raw_data)

    print(f"🔍 Анализируем {total} файлов...")

    for index, item in enumerate(raw_data, 1):
        # Поддерживаем и строки, и объекты
        file_name = item if isinstance(item, str) else item.get('name')
        
        # Очищаем имя для корректного URL
        clean_name = urllib.parse.quote(file_name)
        img_url = f"{RAW_BASE_URL}{clean_name}"
        
        width, height = get_webp_dimensions(img_url)
        
        if width and height:
            is_portrait = height > width
            photo_type = "portrait" if is_portrait else "landscape"
            print(f"[{index}/{total}] {file_name} -> {photo_type} ({width}x{height})")
        else:
            photo_type = "landscape" # Фоллбэк, если файл недоступен
            print(f"[{index}/{total}] ⚠️ {file_name} -> не удалось определить, ставим landscape")

        updated_manifest.append({
            "name": file_name,
            "type": photo_type
        })

    # Сохраняем обновленный файл
    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(updated_manifest, f, ensure_ascii=False, indent=2)

    print("\n✅ Готово! Файл manifest.json обновлен и сохранен локально.")
    print("Закомить его в репозиторий, и фронтенд полетит!")

if __name__ == "__main__":
    process_manifest()
