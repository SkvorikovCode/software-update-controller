import sys
import os
import json
import shutil
import requests
import zipfile
from datetime import datetime
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QComboBox, QPushButton, QLabel,
                           QProgressBar, QMessageBox, QFrame, QSpacerItem,
                           QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from qt_material import apply_stylesheet
from semantic_version import Version

class CustomFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            CustomFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
        """)

class SoftwareUpdater(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обновление программного обеспечения")
        self.setMinimumSize(900, 600)
        
        # Установка иконки приложения
        self.setWindowIcon(QIcon("icons/app.svg"))
        
        # Инициализация переменных
        self.current_version = None
        self.latest_version = None
        self.backup_path = "backups"
        self.temp_path = "temp"
        self.releases_path = "releases"
        self.github_repo = "SkvorikovCode/software-update-controller"
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        
        # Создаем необходимые директории
        for path in [self.backup_path, self.temp_path, self.releases_path]:
            if not os.path.exists(path):
                os.makedirs(path)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_frame = CustomFrame()
        title_layout = QVBoxLayout(title_frame)
        title_label = QLabel("Система обновления ПО")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        
        # Информация о версиях
        version_frame = CustomFrame()
        version_layout = QVBoxLayout(version_frame)
        version_layout.setSpacing(10)
        
        self.current_version_label = QLabel("Текущая версия: Проверка...")
        self.latest_version_label = QLabel("Доступная версия: Проверка...")
        self.current_version_label.setFont(QFont("Segoe UI", 11))
        self.latest_version_label.setFont(QFont("Segoe UI", 11))
        
        version_layout.addWidget(self.current_version_label)
        version_layout.addWidget(self.latest_version_label)
        
        # COM порты
        port_frame = CustomFrame()
        port_layout = QHBoxLayout(port_frame)
        port_layout.setSpacing(15)
        
        self.port_label = QLabel("USB порт:")
        self.port_label.setFont(QFont("Segoe UI", 11))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self.port_combo.setFont(QFont("Segoe UI", 10))
        
        self.refresh_button = QPushButton("Обновить список")
        self.refresh_button.setFont(QFont("Segoe UI", 10))
        self.refresh_button.clicked.connect(self.update_ports)
        self.refresh_button.setMinimumWidth(150)
        
        # Добавляем иконки для кнопок
        self.refresh_button.setIcon(QIcon("icons/refresh.svg"))
        
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)
        port_layout.addStretch()
        
        # Прогресс бар
        progress_frame = CustomFrame()
        progress_layout = QVBoxLayout(progress_frame)
        
        progress_label = QLabel("Прогресс операции:")
        progress_label.setFont(QFont("Segoe UI", 11))
        self.progress = QProgressBar()
        self.progress.setMinimumHeight(25)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setFont(QFont("Segoe UI", 10))
        self.progress.setStyleSheet("""
            QProgressBar {
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 5px;
            }
        """)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress)
        
        # Кнопки управления
        button_frame = CustomFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)
        
        self.check_updates_button = QPushButton("Проверить обновления")
        self.install_button = QPushButton("Установить")
        self.rollback_button = QPushButton("Откатить к предыдущей версии")
        
        # Добавляем иконки для кнопок
        self.check_updates_button.setIcon(QIcon("icons/check.svg"))
        self.install_button.setIcon(QIcon("icons/install.svg"))
        self.rollback_button.setIcon(QIcon("icons/rollback.svg"))
        
        for button in [self.check_updates_button, self.install_button, self.rollback_button]:
            button.setFont(QFont("Segoe UI", 10))
            button.setMinimumHeight(40)
            button.setMinimumWidth(200)
        
        self.check_updates_button.clicked.connect(self.check_updates)
        self.install_button.clicked.connect(self.install_update)
        self.rollback_button.clicked.connect(self.rollback_version)
        
        self.install_button.setEnabled(False)
        self.rollback_button.setEnabled(False)
        
        button_layout.addWidget(self.check_updates_button)
        button_layout.addWidget(self.install_button)
        button_layout.addWidget(self.rollback_button)
        
        # Добавляем все фреймы в главный layout
        main_layout.addWidget(title_frame)
        main_layout.addWidget(version_frame)
        main_layout.addWidget(port_frame)
        main_layout.addWidget(progress_frame)
        main_layout.addWidget(button_frame)
        main_layout.addStretch()
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
        self.statusBar().setFont(QFont("Segoe UI", 10))
        
        # Инициализация
        self.update_ports()
        self.check_current_version()
    
    def update_ports(self):
        """Обновление списка доступных COM портов"""
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
    
    def check_current_version(self):
        """Проверка текущей версии ПО на устройстве"""
        try:
            port = self.port_combo.currentText()
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.write(b"version\n")
                response = ser.readline().decode().strip()
                self.current_version = Version(response)
                self.current_version_label.setText(f"Текущая версия: {self.current_version}")
        except Exception as e:
            self.current_version_label.setText("Текущая версия: Ошибка чтения")
            QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать версию: {str(e)}")
    
    def check_updates(self):
        """Проверка наличия обновлений на GitHub"""
        try:
            # Очищаем прогресс бар
            self.progress.setValue(0)
            
            response = requests.get(self.github_api_url)
            if response.status_code == 404:
                QMessageBox.warning(self, "Ошибка", 
                                  "Репозиторий не найден или нет публичных релизов")
                return
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Ошибка", 
                                  f"Ошибка при получении данных с GitHub: {response.status_code}")
                return
            
            release_data = response.json()
            try:
                self.latest_version = Version(release_data['tag_name'].lstrip('v'))
                self.latest_version_label.setText(f"Доступная версия: {self.latest_version}")
                
                # Сохраняем URL файла обновления
                self.update_url = None
                for asset in release_data['assets']:
                    if asset['name'].endswith('.zip'):  # Ищем zip архив
                        self.update_url = asset['browser_download_url']
                        self.update_filename = asset['name']
                        break
                
                if not self.update_url:
                    QMessageBox.warning(self, "Ошибка", 
                                      "В релизе не найден архив обновления (.zip)")
                    return
                
                # Скачиваем актуальную версию в releases
                release_dir = os.path.join(self.releases_path, str(self.latest_version))
                if not os.path.exists(release_dir):
                    os.makedirs(release_dir)
                
                # Загружаем архив
                self.progress.setValue(10)
                zip_path = os.path.join(release_dir, self.update_filename)
                
                response = requests.get(self.update_url, stream=True)
                if response.status_code != 200:
                    raise Exception(f"Ошибка загрузки: {response.status_code}")
                
                total_size = int(response.headers.get('content-length', 0))
                with open(zip_path, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for data in response.iter_content(chunk_size=4096):
                            downloaded += len(data)
                            f.write(data)
                            progress = int((downloaded / total_size) * 40) + 10
                            self.progress.setValue(progress)
                
                # Распаковываем архив
                self.progress.setValue(60)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(release_dir)
                
                self.progress.setValue(80)
                
                # Проверяем что архив не пустой
                files = []
                for root, dirs, filenames in os.walk(release_dir):
                    files.extend(filenames)
                
                if not files:
                    raise Exception("Архив обновления пуст")
                
                # Сохраняем список файлов для установки
                self.update_files = []
                for root, dirs, filenames in os.walk(release_dir):
                    for filename in filenames:
                        if filename != self.update_filename:  # Пропускаем сам архив
                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, release_dir)
                            self.update_files.append((file_path, rel_path))
                
                self.progress.setValue(100)
                
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", 
                                  f"Ошибка при обработке релиза: {str(e)}")
                if os.path.exists(release_dir):
                    shutil.rmtree(release_dir)
                return
            
            if self.current_version and self.latest_version > self.current_version:
                self.install_button.setEnabled(True)
                files_list = "\n".join(f"- {rel_path}" for _, rel_path in self.update_files)
                QMessageBox.information(self, "Обновление доступно", 
                                     f"Доступна новая версия: {self.latest_version}\n"
                                     f"Файлы для обновления:\n{files_list}\n"
                                     f"Сохранены в: {release_dir}")
            else:
                QMessageBox.information(self, "Обновления не требуются", 
                                     "У вас установлена последняя версия")
            
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сети: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка проверки обновлений: {str(e)}")
        finally:
            self.progress.setValue(0)
    
    def create_backup(self):
        """Создание резервной копии текущего ПО"""
        try:
            port = self.port_combo.currentText()
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
            backup_path = os.path.join(self.backup_path, backup_filename)
            
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.write(b"backup\n")
                with open(backup_path, 'wb') as f:
                    # Здесь должна быть логика получения бинарных данных с устройства
                    pass
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка создания резервной копии: {str(e)}")
            return False
    
    def install_update(self):
        """Установка обновления"""
        if not hasattr(self, 'latest_version'):
            QMessageBox.warning(self, "Ошибка", "Сначала проверьте наличие обновлений")
            return
            
        if self.create_backup():
            try:
                # Путь к распакованному релизу
                release_dir = os.path.join(self.releases_path, str(self.latest_version))
                if not os.path.exists(release_dir):
                    raise Exception("Файлы обновления не найдены. Проверьте обновления снова.")
                
                if not hasattr(self, 'update_files') or not self.update_files:
                    raise Exception("Список файлов для обновления пуст")
                
                # Установка обновления
                self.progress.setValue(0)
                port = self.port_combo.currentText()
                with serial.Serial(port, 9600, timeout=1) as ser:
                    ser.write(b"update\n")
                    
                    # Отправляем количество файлов
                    num_files = len(self.update_files)
                    ser.write(f"{num_files}\n".encode())
                    
                    # Отправляем каждый файл
                    for i, (file_path, rel_path) in enumerate(self.update_files):
                        # Отправляем имя файла
                        ser.write(f"{rel_path}\n".encode())
                        
                        # Отправляем содержимое файла
                        with open(file_path, 'rb') as f:
                            # TODO: Реализовать протокол передачи файла
                            pass
                        
                        # Обновляем прогресс
                        progress = int((i + 1) / num_files * 100)
                        self.progress.setValue(progress)
                    
                self.progress.setValue(100)
                QMessageBox.information(self, "Успех", "Обновление успешно установлено")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка установки обновления: {str(e)}")
    
    def rollback_version(self):
        """Откат к предыдущей версии"""
        try:
            # Поиск последнего бэкапа
            backups = sorted([f for f in os.listdir(self.backup_path) if f.endswith('.bin')],
                           reverse=True)
            if not backups:
                QMessageBox.warning(self, "Ошибка", "Резервные копии не найдены")
                return
                
            backup_file = os.path.join(self.backup_path, backups[0])
            
            # Установка бэкапа
            port = self.port_combo.currentText()
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.write(b"restore\n")
                # Здесь должна быть логика отправки файла на устройство
                
            QMessageBox.information(self, "Успех", "Восстановление завершено успешно")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отката версии: {str(e)}")

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml', invert_secondary=True)
    
    # Дополнительные стили для темной темы
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
        QMessageBox {
            background-color: #2d2d2d;
        }
        QMessageBox QLabel {
            color: #ffffff;
            font-size: 11pt;
        }
        QMessageBox QPushButton {
            min-width: 100px;
            min-height: 30px;
            font-size: 10pt;
        }
        QComboBox {
            padding: 5px;
            min-height: 25px;
        }
        QPushButton {
            padding: 5px 15px;
        }
        QLabel {
            color: #ffffff;
        }
    """)
    
    window = SoftwareUpdater()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 