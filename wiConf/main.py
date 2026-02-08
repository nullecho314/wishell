import sys
import os
import configparser
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QLabel, QPushButton, QFormLayout, QMessageBox
)

class WiConf(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("wiConf - Configuration Editor")
        self.resize(600, 400)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(base_dir, "config.ini")

        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(self.config_file)

        # Ana widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        central.setLayout(layout)

        # Sol tarafta bölümler
        self.sectionList = QListWidget()
        self.sectionList.addItems(self.config.sections())
        self.sectionList.currentTextChanged.connect(self.loadSection)
        layout.addWidget(self.sectionList, 1)

        # Sağ tarafta key-value editör
        self.formLayout = QFormLayout()
        self.formWidget = QWidget()
        self.formWidget.setLayout(self.formLayout)
        layout.addWidget(self.formWidget, 3)

        # Save butonu
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveConfig)
        layout.addWidget(self.saveButton)

        self.editors = {}
        if self.config.sections():
            self.sectionList.setCurrentRow(0)

    def loadSection(self, section):
        # Önce temizle
        for i in reversed(range(self.formLayout.count())):
            self.formLayout.removeRow(i)
        self.editors.clear()

        if section in self.config:
            for key, value in self.config[section].items():
                editor = QLineEdit(value)
                self.formLayout.addRow(QLabel(key), editor)
                self.editors[key] = editor

    def saveConfig(self):
        current_section = self.sectionList.currentItem().text()
        if current_section:
            for key, editor in self.editors.items():
                self.config[current_section][key] = editor.text()
            with open(self.config_file, "w") as f:
                self.config.write(f)
            QMessageBox.information(self, "Saved", "Configuration saved successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WiConf()
    window.show()
    sys.exit(app.exec())
