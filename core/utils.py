import sys
import os

def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу — работает и в dev, и в PyInstaller """
    try:
        # PyInstaller создаёт временную папку _MEIPASS при --onefile
        base_path = sys._MEIPASS
    except Exception:
        # Обычный режим разработки
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)