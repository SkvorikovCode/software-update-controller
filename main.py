import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QComboBox, QPushButton, QLabel,
                           QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt
from qt_material import apply_stylesheet

class ArduinoUpdater(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Firmware Updater")
        self.setMinimumSize(600, 400)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Создаем и настраиваем компоненты интерфейса
        port_layout = QHBoxLayout()
        self.port_label = QLabel("COM порт:")
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.update_ports)
        
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)
        
        # Кнопка выбора файла прошивки
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл прошивки не выбран")
        self.select_file_button = QPushButton("Выбрать файл")
        self.select_file_button.clicked.connect(self.select_firmware)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_file_button)
        
        # Прогресс бар
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Кнопка обновления прошивки
        self.update_button = QPushButton("Обновить прошивку")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_firmware)
        
        # Добавляем все компоненты в главный layout
        layout.addLayout(port_layout)
        layout.addLayout(file_layout)
        layout.addWidget(self.progress)
        layout.addWidget(self.update_button)
        layout.addStretch()
        
        # Инициализация
        self.firmware_path = None
        self.update_ports()
    
    def update_ports(self):
        """Обновление списка доступных COM портов"""
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)
    
    def select_firmware(self):
        """Выбор файла прошивки"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл прошивки",
            "",
            "Hex Files (*.hex);;All Files (*.*)"
        )
        if file_name:
            self.firmware_path = file_name
            self.file_label.setText(f"Выбран файл: {file_name}")
            self.update_button.setEnabled(True)
    
    def update_firmware(self):
        """Обновление прошивки"""
        # Здесь будет реализована логика обновления прошивки
        # Это заглушка для демонстрации
        self.progress.setValue(0)
        # TODO: Добавить реальную логику обновления
        self.progress.setValue(100)

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    
    window = ArduinoUpdater()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 