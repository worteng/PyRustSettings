import os

# Путь к папке с медиафайлами
folder = os.path.join("assets", "graphics")

# Проверяем, существует ли папка
if not os.path.exists(folder):
    print(f"Папка не найдена: {folder}")
else:
    # Проходим по всем файлам в папке
    for filename in os.listdir(folder):
        if filename.lower().endswith(".mp4"):
            print(filename)