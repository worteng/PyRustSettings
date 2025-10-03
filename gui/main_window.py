# gui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, QHBoxLayout, QFrame,
    QTextEdit, QCheckBox, QMessageBox
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QObject, QEvent, QUrl
from PySide6.QtGui import QMovie
import os
import json
from core.config_manager import ConfigManager
from core.utils import resource_path

class HoverFilter(QObject):
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
        self.checkboxes = {}  # убедись, что есть

        self.setWindowTitle("PyRustSettings")
        self.setGeometry(200, 200, 1000, 600)

        self.tweaks_info = self.load_tweaks_json()
        self.cfg_folder = None
        self.config_manager = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.addTab(self.create_home_tab(), "Главное")
        self.tabs.addTab(self.create_tweaks_tab(), "Твики")

        self.preview_panel = self.create_preview_panel()
        layout.addWidget(self.tabs, 3)
        layout.addWidget(self.preview_panel, 2)

    def load_tweaks_json(self):
        json_path = resource_path(os.path.join("core", "tweaks.json"))
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def create_home_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.path_label = QLabel("Папка с cfg не выбрана")
        layout.addWidget(self.path_label)

        self.load_button = QPushButton("Считать папку с конфигами")
        self.load_button.clicked.connect(self.load_cfg_folder)
        layout.addWidget(self.load_button)

        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_configs)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button)

        layout.addStretch()
        return tab

    def create_tweaks_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.checkboxes = {}

        for tweak_name, data in self.tweaks_info.items():
            if data.get("type") == "bool":
                cb = QCheckBox(tweak_name)
                cb.installEventFilter(HoverFilter(self, tweak_name))
                cb.clicked.connect(
                    lambda checked, t=tweak_name: self.on_tweak_changed(t, checked)
                )
                layout.addWidget(cb)
                self.checkboxes[tweak_name] = cb

        layout.addStretch()
        return tab

    def create_preview_panel(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)

        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_gif_label = QLabel()
        self.preview_gif_label.setAlignment(Qt.AlignCenter)
        self.preview_gif_label.setFixedSize(300, 300)
        self.preview_gif_label.hide()

        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(360, 220)
        self.video_widget.hide()

        self.media_layout.addWidget(self.preview_gif_label)
        self.media_layout.addWidget(self.video_widget)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Описание выбранной настройки")

        layout.addWidget(self.media_container)
        layout.addWidget(self.preview_text)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        return frame

    def show_tweak_info(self, tweak_name):
        tweak_data = self.tweaks_info.get(tweak_name, {})
        description = tweak_data.get("description", "Описание отсутствует.")
        media_file = tweak_data.get("preview", "")

        self.preview_text.setPlainText(description)

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

        media_path = resource_path(os.path.join("assets", "graphics", media_file))
        if not os.path.exists(media_path):
            self.preview_gif_label.setText(f"[Файл не найден:\n{media_path}]")
            self.preview_gif_label.show()
            return

        ext = os.path.splitext(media_file)[1].lower()

        if ext in ('.gif', '.apng'):
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
            url = QUrl.fromLocalFile(os.path.abspath(media_path))
            self.media_player.setSource(url)
            self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
            self.video_widget.show()
            self.media_player.play()

        else:
            self.preview_gif_label.setText("Неподдерживаемый формат")
            self.preview_gif_label.show()

    def _normalize_file_field(self, raw_file_field):
        if not raw_file_field:
            return "client"
        f = raw_file_field.lower()
        if f.endswith(".cfg"):
            f = f[:-4]
        if f not in ("client", "keys"):
            return "client"
        return f

    def load_cfg_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку Rust")
        if folder:
            cfg_path = os.path.join(folder, "cfg")
            if os.path.exists(cfg_path):
                self.cfg_folder = cfg_path
                self.path_label.setText(f"Найдена папка cfg: {cfg_path}")
                self.config_manager = ConfigManager(cfg_path)
                self.sync_checkboxes_with_config()
                self.save_button.setEnabled(True)
            else:
                self.path_label.setText("В папке Rust не найдено cfg")
        else:
            print("Папка не выбрана")

    def sync_checkboxes_with_config(self):
        for tweak_name, cb in self.checkboxes.items():
            tweak_data = self.tweaks_info.get(tweak_name, {})
            if tweak_data.get("type") != "bool":
                continue

            key = tweak_data.get("key")
            file_field = self._normalize_file_field(tweak_data.get("file"))
            current_value = self.config_manager.get_value(key, file_field)

            true_val = tweak_data.get("true_value", "1")
            best_val = tweak_data.get("best")
            default_val = tweak_data.get("default")

            # compare raw strings, but normalize whitespace/case a bit
            cur = (current_value or "").strip()
            tv = (true_val or "").strip()
            bv = (best_val or "").strip()

            is_enabled = False
            if cur != "":
                if cur == tv or (bv and cur == bv):
                    is_enabled = True
            else:
                # If not present, fallback to default
                if default_val is not None and str(default_val).strip() == tv:
                    is_enabled = True

            cb.blockSignals(True)
            cb.setChecked(is_enabled)
            cb.blockSignals(False)

    def on_tweak_changed(self, tweak_name: str, checked: bool):
        if not self.config_manager:
            return

        tweak_data = self.tweaks_info.get(tweak_name)
        if not tweak_data or tweak_data.get("type") != "bool":
            return

        key = tweak_data["key"]
        file_field = self._normalize_file_field(tweak_data.get("file"))

        if checked:
            new_value = tweak_data.get("best", tweak_data.get("true_value", "1"))
        else:
            new_value = tweak_data.get("false_value", "0")

        self.config_manager.set_value(key, new_value, file_field)

    def save_configs(self):
        if not self.config_manager:
            return
        try:
            self.config_manager.save()
            # не перечитываем файл, оставляем данные в памяти
            QMessageBox.information(self, "Успех", "Конфигурация успешно сохранена!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{str(e)}")
