import sys
import os
import json
import threading
import winreg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QSystemTrayIcon, QMenu, QProgressBar, QDialog, QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
import file_organizer

class FileOrganizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件整理工具")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "zhmetosr25.ico")))
        self.setGeometry(100, 100, 400, 200)
        
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.type_config_file = os.path.join(os.path.dirname(__file__), 'types.json')
        
        self.init_tray_icon()
        self.initUI()
        self.load_config()
        self.load_type_config()
    
    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        

        
        self.dir_label = QLabel("选择要整理的目录:")
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("点击浏览选择目录...")
        self.dir_input.setReadOnly(True)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_directory)
        
        self.organize_btn = QPushButton("开始整理")
        self.organize_btn.clicked.connect(self.organize_files)
        
        self.watch_btn = QPushButton("开始监视")
        self.watch_btn.setCheckable(True)
        self.watch_btn.clicked.connect(self.toggle_watch)
        
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
        layout.addWidget(self.dir_label)
        layout.addWidget(self.dir_input)
        layout.addWidget(self.browse_btn)
        layout.addWidget(self.organize_btn)
        layout.addWidget(self.watch_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.progress_bar)
        
        main_widget.setLayout(layout)
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.dir_input.setText(directory)
    
    def organize_files(self):
        directory = self.dir_input.text()
        if not directory:
            QMessageBox.warning(self, "警告", "请先选择要整理的目录！")
            return
            
        try:
            self.progress_bar.setVisible(True)
            file_organizer.organize_files(directory)
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "完成", "文件整理完成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"整理文件时出错:\n{str(e)}")
            
    def toggle_watch(self):
        directory = self.dir_input.text()
        if not directory:
            QMessageBox.warning(self, "警告", "请先选择要监视的目录！")
            self.watch_btn.setChecked(False)
            return
            
        if self.watch_btn.isChecked():
            self.watch_thread = threading.Thread(target=file_organizer.watch_directory, args=(directory,))
            self.watch_thread.daemon = True
            self.watch_thread.start()
            self.watch_btn.setText("停止监视")
            QMessageBox.information(self, "提示", "已开始监视目录，新文件将自动整理")
        else:
            self.watch_btn.setText("开始监视")
            QMessageBox.information(self, "提示", "已停止监视目录")

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                if 'directory' in config:
                    self.dir_input.setText(config['directory'])
                if 'watch' in config and config['watch']:
                    self.watch_btn.setChecked(True)
                    self.toggle_watch()
                if 'auto_start' in config and config['auto_start']:
                    self.auto_start_action.setChecked(True)
                    self.toggle_auto_start()
    
    def save_config(self):
        config = {
            'directory': self.dir_input.text(),
            'watch': self.watch_btn.isChecked(),
            'auto_start': self.auto_start_action.isChecked()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
            
    def toggle_auto_start(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
                                
            app_path = os.path.abspath(sys.argv[0])
            
            if self.auto_start_action.isChecked():
                winreg.SetValueEx(key, "FileOrganizer", 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, "FileOrganizer")
                except WindowsError:
                    pass
            
            winreg.CloseKey(key)
            self.save_config()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置开机自启时出错:\n{str(e)}")
            
    def update_auto_start_menu(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_READ)
            
            app_path = os.path.abspath(sys.argv[0])
            try:
                reg_value = winreg.QueryValueEx(key, "FileOrganizer")[0]
                self.auto_start_action.setChecked(reg_value == app_path)
            except WindowsError:
                self.auto_start_action.setChecked(False)
                
            winreg.CloseKey(key)
        except Exception:
            self.auto_start_action.setChecked(False)
    
    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "zhmetosr25.ico")))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示窗口")
        show_action.triggered.connect(self.show)
        
        self.auto_start_action = tray_menu.addAction("开机自启")
        self.auto_start_action.setCheckable(True)
        self.auto_start_action.triggered.connect(self.toggle_auto_start)
        self.update_auto_start_menu()
        
        help_action = tray_menu.addAction("帮助")
        help_action.triggered.connect(self.show_help)
        
        exit_action = tray_menu.addAction("退出")
        exit_action.triggered.connect(sys.exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def show_help(self):
        help_text = "1. 选择要整理的目录。\n2. 点击“开始整理”按钮整理文件。\n3. 点击“开始监视”按钮可以实时监视目录并自动整理新文件。\n4. 可以在设置中配置文件类型和目标文件夹。"
        QMessageBox.information(self, "帮助", help_text)
        
    def closeEvent(self, event):
        event.ignore()
        self.save_config()
        self.hide()
        self.tray_icon.showMessage(
            "文件整理工具",
            "程序已最小化到系统托盘，可通过托盘菜单退出",
            QSystemTrayIcon.Information,
            2000
        )
    
    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("文件类型设置")
        settings_dialog.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout()
        
        self.type_table = QTableWidget()
        self.type_table.setColumnCount(2)
        self.type_table.setHorizontalHeaderLabels(["文件类型", "目标文件夹"])
        self.type_table.setRowCount(len(self.file_types))
        for i, (file_type, folder) in enumerate(self.file_types.items()):
            self.type_table.setItem(i, 0, QTableWidgetItem(file_type))
            self.type_table.setItem(i, 1, QTableWidgetItem(folder))
        
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_type_config)
        
        row_label = QLabel("表格行数:")
        self.row_spinbox = QSpinBox()
        self.row_spinbox.setRange(1, 100)
        self.row_spinbox.setValue(len(self.file_types))
        self.row_spinbox.valueChanged.connect(self.update_table_rows)
        
        interval_label = QLabel("监视间隔(秒):")
        self.interval_spinbox = QDoubleSpinBox()
        self.interval_spinbox.setRange(1.0, 60.0)
        self.interval_spinbox.setValue(5.0)
        self.interval_spinbox.setSingleStep(0.5)
        
        layout.addWidget(row_label)
        layout.addWidget(self.row_spinbox)
        layout.addWidget(interval_label)
        layout.addWidget(self.interval_spinbox)
        layout.addWidget(self.type_table)
        layout.addWidget(save_btn)
        settings_dialog.setLayout(layout)
        settings_dialog.exec_()
    
    def update_table_rows(self):
        rows = self.row_spinbox.value()
        if rows > self.type_table.rowCount():
            for i in range(self.type_table.rowCount(), rows):
                self.type_table.insertRow(i)
        else:
            for i in range(self.type_table.rowCount() - 1, rows - 1, -1):
                self.type_table.removeRow(i)
    
    def load_type_config(self):
        if os.path.exists(self.type_config_file):
            with open(self.type_config_file, 'r') as f:
                self.file_types = json.load(f)
        else:
            self.file_types = {}
    
    def save_type_config(self):
        self.file_types = {}
        for row in range(self.type_table.rowCount()):
            file_type = self.type_table.item(row, 0).text()
            folder = self.type_table.item(row, 1).text()
            if file_type and folder:
                self.file_types[file_type] = folder
        with open(self.type_config_file, 'w') as f:
            json.dump(self.file_types, f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileOrganizerGUI()
    window.show()
    sys.exit(app.exec_())