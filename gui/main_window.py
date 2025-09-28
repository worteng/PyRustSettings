from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, QHBoxLayout, QFrame,
    QTextEdit, QCheckBox
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QObject, QEvent, QUrl
from PySide6.QtGui import QMovie
import os, json

class HoverFilter(QObject):
    """Фильтр событий для наведения мыши"""
    def __init__(self, parent, name):
        super().__init__(parent)
        self.parent = parent
        self.name = name

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.parent.show_tweak_info(self.name)
        return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyRustSettings")
        self.setGeometry(200, 200, 1000, 600)

        # Загружаем tweaks.json
        self.tweaks_info = self.load_tweaks_json()

        # Главное разделение (вкладки + превью)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        # Добавляем вкладки
        self.tabs.addTab(self.create_home_tab(), "Главное")
        self.tabs.addTab(self.create_tweaks_tab(), "Твики")
        self.tabs.addTab(QWidget(), "Графика")
        self.tabs.addTab(QWidget(), "Оптимизация")
        self.tabs.addTab(QWidget(), "Бинды")
        self.tabs.addTab(QWidget(), "Прочее")

        # Панель превью справа
        self.preview_panel = self.create_preview_panel()

        # Компоновка
        layout.addWidget(self.tabs, 3)
        layout.addWidget(self.preview_panel, 2)

    def load_tweaks_json(self):
        """Загрузка описаний твиков из core/tweaks.json"""
        json_path = os.path.join("core", "tweaks.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def create_home_tab(self):
        """Главная вкладка"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.path_label = QLabel("Папка с cfg не выбрана")
        layout.addWidget(self.path_label)

        self.load_button = QPushButton("Считать папку с конфигами")
        self.load_button.clicked.connect(self.load_cfg_folder)
        layout.addWidget(self.load_button)

        layout.addStretch()
        return tab

    def create_tweaks_tab(self):
        """Вкладка Твики"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.checkboxes = {}

        for tweak, data in self.tweaks_info.items():
            cb = QCheckBox(tweak)
            cb.installEventFilter(HoverFilter(self, tweak))
            layout.addWidget(cb)
            self.checkboxes[tweak] = cb

        layout.addStretch()
        return tab

    def create_preview_panel(self):
        """Справа панель превью"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)

        # Контейнер для медиа (GIF или видео)
        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setContentsMargins(0, 0, 0, 0)

        # QLabel для GIF
        self.preview_gif_label = QLabel()
        self.preview_gif_label.setAlignment(Qt.AlignCenter)
        self.preview_gif_label.setFixedSize(300, 300)
        self.preview_gif_label.hide()  # скрыт по умолчанию

        # QVideoWidget для MP4
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(360, 220)
        self.video_widget.hide()  # скрыт по умолчанию

        self.media_layout.addWidget(self.preview_gif_label)
        self.media_layout.addWidget(self.video_widget)

        # Текстовое описание
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Описание выбранной настройки")

        layout.addWidget(self.media_container)
        layout.addWidget(self.preview_text)

        # Инициализируем плеер один раз
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        return frame

    def show_tweak_info(self, tweak_name):
        """Обновление превью при наведении на чекбокс"""
        tweak_data = self.tweaks_info.get(tweak_name, {})
        description = tweak_data.get("description", "Описание отсутствует.")
        media_file = tweak_data.get("preview", "")  # ⚠️ Используй "preview", а не "gif"!

        self.preview_text.setPlainText(description)

        # Остановить всё
        if hasattr(self, '_current_movie') and self._current_movie:
            self._current_movie.stop()
            self._current_movie = None

        self.media_player.stop()
        self.preview_gif_label.hide()
        self.video_widget.hide()

        if not media_file:
            self.preview_gif_label.setText("Превью недоступно")
            self.preview_gif_label.show()
            return

        media_path = os.path.join("assets", "graphics", media_file)
        if not os.path.exists(media_path):
            self.preview_gif_label.setText(f"[Файл не найден:\n{media_path}]")
            self.preview_gif_label.show()
            return

        # Определяем тип по расширению
        ext = os.path.splitext(media_file)[1].lower()

        if ext in ('.gif', '.apng'):
            # GIF / APNG — через QMovie
            movie = QMovie(media_path)

            def on_first_frame():
                rect = movie.frameRect()
                if rect.isValid() and not rect.isEmpty():
                    size = rect.size()
                    max_size = 300
                    if size.width() > max_size or size.height() > max_size:
                        size.scale(max_size, max_size, Qt.KeepAspectRatio)
                    self.preview_gif_label.setFixedSize(size)
                movie.frameChanged.disconnect(on_first_frame)

            movie.frameChanged.connect(on_first_frame)
            self.preview_gif_label.setMovie(movie)
            self.preview_gif_label.show()
            movie.start()
            self._current_movie = movie

        elif ext in ('.mp4', '.webm', '.avi', '.mov'):
            # Видео — через QMediaPlayer с бесконечным повтором
            url = QUrl.fromLocalFile(os.path.abspath(media_path))
            self.media_player.setSource(url)
            self.media_player.setLoops(QMediaPlayer.Loops.Infinite)  # 🔁 Бесконечный повтор
            self.video_widget.show()
            self.media_player.play()

        else:
            self.preview_gif_label.setText("Неподдерживаемый формат")
            self.preview_gif_label.show()

    def load_cfg_folder(self):
        """Выбор папки с cfg"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку Rust")
        if folder:
            cfg_path = os.path.join(folder, "cfg")
            if os.path.exists(cfg_path):
                self.path_label.setText(f"Найдена папка cfg: {cfg_path}")
                # TODO: здесь подключим чтение client.cfg и keys.cfg
            else:
                self.path_label.setText("В папке Rust не найдено cfg")
