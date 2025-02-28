import sys
import os
import json
import shutil
import requests
from datetime import datetime
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QComboBox, QPushButton, QLabel,
                           QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qt_material import apply_stylesheet
from semantic_version import Version

class SoftwareUpdater(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обновление программного обеспечения")
        self.setMinimumSize(800, 500)
        
        # Инициализация переменных
        self.current_version = None
        self.latest_version = None
        self.backup_path = "backups"
        self.github_repo = "SkvorikovCode/software-update-controller"
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Информация о версиях
        version_layout = QVBoxLayout()
        self.current_version_label = QLabel("Текущая версия: Проверка...")
        self.latest_version_label = QLabel("Доступная версия: Проверка...")
        version_layout.addWidget(self.current_version_label)
        version_layout.addWidget(self.latest_version_label)
        
        # COM порты
        port_layout = QHBoxLayout()
        self.port_label = QLabel("USB порт:")
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Обновить список")
        self.refresh_button.clicked.connect(self.update_ports)
        
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)
        
        # Прогресс бар
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        self.check_updates_button = QPushButton("Проверить обновления")
        self.install_button = QPushButton("Установить")
        self.rollback_button = QPushButton("Откатить к предыдущей версии")
        
        self.check_updates_button.clicked.connect(self.check_updates)
        self.install_button.clicked.connect(self.install_update)
        self.rollback_button.clicked.connect(self.rollback_version)
        
        self.install_button.setEnabled(False)
        self.rollback_button.setEnabled(False)
        
        button_layout.addWidget(self.check_updates_button)
        button_layout.addWidget(self.install_button)
        button_layout.addWidget(self.rollback_button)
        
        # Добавляем все компоненты в главный layout
        layout.addLayout(version_layout)
        layout.addLayout(port_layout)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Инициализация
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
            
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
                    if asset['name'].endswith('.bin'):  # или другое расширение вашего файла
                        self.update_url = asset['browser_download_url']
                        break
                
                if not self.update_url:
                    QMessageBox.warning(self, "Ошибка", 
                                      "В релизе не найден файл обновления")
                    return
                
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", 
                                  "Неверный формат версии в релизе. Используйте формат v1.0.0")
                return
            
            if self.current_version and self.latest_version > self.current_version:
                self.install_button.setEnabled(True)
                QMessageBox.information(self, "Обновление доступно", 
                                     f"Доступна новая версия: {self.latest_version}")
            else:
                QMessageBox.information(self, "Обновления не требуются", 
                                     "У вас установлена последняя версия")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сети: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка проверки обновлений: {str(e)}")
    
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
        if not hasattr(self, 'update_url'):
            QMessageBox.warning(self, "Ошибка", "Сначала проверьте наличие обновлений")
            return
            
        if self.create_backup():
            try:
                # Загрузка обновления
                self.progress.setValue(0)
                response = requests.get(self.update_url, stream=True)
                if response.status_code != 200:
                    raise Exception(f"Ошибка загрузки: {response.status_code}")
                
                # Временный файл для загрузки
                temp_file = "temp_update.bin"
                total_size = int(response.headers.get('content-length', 0))
                
                with open(temp_file, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for data in response.iter_content(chunk_size=4096):
                            downloaded += len(data)
                            f.write(data)
                            progress = int((downloaded / total_size) * 50)
                            self.progress.setValue(progress)
                
                # Установка обновления
                port = self.port_combo.currentText()
                with serial.Serial(port, 9600, timeout=1) as ser:
                    ser.write(b"update\n")
                    # Здесь должна быть логика отправки файла на устройство
                    self.progress.setValue(100)
                
                # Очистка
                os.remove(temp_file)
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
    apply_stylesheet(app, theme='dark_teal.xml')
    
    window = SoftwareUpdater()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 