import sys
import os
import configparser
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

class WiCore(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("wiCore")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(base_dir, "config.ini")

        self.wishelldir = os.path.abspath(os.path.join(base_dir, ".."))
        os.environ["wishelldir"] = self.wishelldir

        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(config_file)

        self.hide_inaccessible = self.config.getboolean("General", "hide_inaccessible", fallback=False)
        self.show_hidden = self.config.getboolean("General", "show_hidden", fallback=False)
        self.confirm_quit = self.config.getboolean("General", "confirm_quit", fallback=False)

        # Varsayılan: work area override aktif
        self.override_workarea = self.config.getboolean("General", "override_workarea", fallback=True)

        # Hep en arkada olsun
        self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.Tool, True)

    def closeEvent(self, event):
        super().closeEvent(event)

    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)

        # Applications menüsü
        apps_path = self.config.get("General", "applications_path", fallback="").strip('"').strip()
        if apps_path:
            appsMenu = QMenu("Applications", self)
            if os.path.isdir(apps_path):
                try:
                    for item in os.listdir(apps_path):
                        if not self.show_hidden:
                            if item.lower() == "desktop.ini" or item.startswith("."):
                                continue
                        item_path = os.path.join(apps_path, item)
                        if os.path.isdir(item_path):
                            try:
                                subMenu = QMenu(item, self)
                                for subitem in os.listdir(item_path):
                                    if not self.show_hidden:
                                        if subitem.lower() == "desktop.ini" or subitem.startswith("."):
                                            continue
                                    subitem_path = os.path.join(item_path, subitem)
                                    if os.path.isfile(subitem_path):
                                        action = QAction(subitem, self)
                                        action.triggered.connect(lambda checked=False, p=subitem_path: self.launchApp(p))
                                        subMenu.addAction(action)
                                if subMenu.actions():
                                    appsMenu.addMenu(subMenu)
                            except PermissionError:
                                if not self.hide_inaccessible:
                                    pass
                        elif os.path.isfile(item_path):
                            action = QAction(item, self)
                            action.triggered.connect(lambda checked=False, p=item_path: self.launchApp(p))
                            appsMenu.addAction(action)
                except PermissionError:
                    if not self.hide_inaccessible:
                        appsMenu.addAction(QAction("(Access denied)", self))
            else:
                appsMenu.addAction(QAction("(Path not found)", self))
            contextMenu.addMenu(appsMenu)

        # Settings
        settings_path = self.config.get("General", "settings_path", fallback="").strip()
        if settings_path:
            settingsAction = QAction("Settings", self)
            settingsAction.triggered.connect(self.openSettings)
            contextMenu.addAction(settingsAction)

        # Explorer
        explorer_path = self.config.get("General", "explorer_path", fallback="").strip()
        if explorer_path:
            explorerAction = QAction("Explorer", self)
            explorerAction.triggered.connect(lambda: self.launchApp(explorer_path))
            contextMenu.addAction(explorerAction)

        # About
        aboutAction = QAction("About", self)
        aboutAction.triggered.connect(lambda: QMessageBox.information(self, "About",
            "wiCore for wiShell\nVersion 1.0\n\nCore functionality for wiShell"))
        contextMenu.addAction(aboutAction)

        # Quit menüsü
        quitMenu = QMenu("Quit", self)
        exitAction = QAction("Exit from wiCore", self)
        exitAction.triggered.connect(lambda: self.exitWiCore())
        quitMenu.addAction(exitAction)

        # Restart wiCore
        restartAction = QAction("Restart wiCore", self)
        restartAction.triggered.connect(lambda: self.restartWiCore())
        quitMenu.addAction(restartAction)

        quitMenu.addSeparator()

        if self.config.has_section("Quit"):
            for option, command in self.config.items("Quit"):
                action = QAction(option.capitalize(), self)
                action.triggered.connect(lambda checked=False, opt=option, cmd=command: self.runQuitCommand(opt, cmd))
                quitMenu.addAction(action)

        contextMenu.addSeparator()
        contextMenu.addMenu(quitMenu)

        contextMenu.exec(event.globalPos())

    def launchApp(self, path):
        try:
            if path.lower().startswith("explorer.exe"):
                parts = path.split()
                subprocess.Popen(parts)
            else:
                os.startfile(path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot launch:\n{path}\n\n{e}")

    def openSettings(self):
        raw_path = self.config.get("General", "settings_path", fallback="")
        resolved_path = raw_path.replace("%wishelldir%", os.environ.get("wishelldir", self.wishelldir))
        try:
            os.startfile(resolved_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot open settings:\n{resolved_path}\n\n{e}")

    def exitWiCore(self):
        if self.confirm_quit:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Question)
            box.setWindowTitle("Confirm Exit")
            box.setText("Do you want to exit wiCore?")
            yes_button = box.addButton(QMessageBox.Yes)
            yes_button.setToolTip("Exit application")
            box.addButton(QMessageBox.No)
            box.exec()
            if box.clickedButton() != yes_button:
                return
        QApplication.quit()

    def restartWiCore(self):
        # Uygulamayı yeniden başlat
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def runQuitCommand(self, option, command):
        if self.confirm_quit:
            msg = f"Do you want to {option}?"
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Question)
            box.setWindowTitle("Confirm Quit")
            box.setText(msg)
            yes_button = box.addButton(QMessageBox.Yes)
            yes_button.setToolTip(f"Command: {command}")
            box.addButton(QMessageBox.No)
            box.exec()
            if box.clickedButton() != yes_button:
                return
        try:
            os.system(command)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot run:\n{command}\n\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    desktop = WiCore()
    desktop.setGeometry(QApplication.primaryScreen().geometry())
    desktop.show()
    sys.exit(app.exec())
