import os
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QCheckBox, QPushButton, QMessageBox, QProgressBar,
                            QLabel, QGroupBox, QHBoxLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
import sys
import winreg
import ctypes
from pathlib import Path
import psutil
import datetime
import subprocess

class CleanerThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, selected_tasks):
        super().__init__()
        self.selected_tasks = selected_tasks
        self.total_cleaned = 0
        
    def get_size(self, path):
        total = 0
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
        except:
            pass
        return total

    def run(self):
        results = {"cleaned": 0, "errors": []}
        total_tasks = len(self.selected_tasks)
        completed_tasks = 0
        
        for task in self.selected_tasks:
            try:
                if task == "windows_temp":
                    self.status.emit("Windows Temp dosyaları temizleniyor...")
                    self.clean_windows_temp(results)
                elif task == "recycle_bin":
                    self.status.emit("Geri dönüşüm kutusu temizleniyor...")
                    self.clean_recycle_bin(results)
                elif task == "fivem":
                    self.status.emit("FiveM önbelleği temizleniyor...")
                    self.clean_fivem_cache(results)
                elif task == "games":
                    self.status.emit("Oyun önbellekleri temizleniyor...")
                    self.clean_game_cache(results)
                elif task == "downloads":
                    self.status.emit("İndirilenler klasörü temizleniyor...")
                    self.clean_downloads(results)
                elif task == "prefetch":
                    self.status.emit("Prefetch dosyaları temizleniyor...")
                    self.clean_prefetch(results)
                elif task == "dns_cache":
                    self.status.emit("DNS önbelleği temizleniyor...")
                    self.clean_dns_cache(results)
                elif task == "thumbnails":
                    self.status.emit("Küçük resim önbelleği temizleniyor...")
                    self.clean_thumbnails(results)
                elif task == "error_reports":
                    self.status.emit("Hata raporları temizleniyor...")
                    self.clean_error_reports(results)
                elif task == "steam_download":
                    self.status.emit("Steam indirme önbelleği temizleniyor...")
                    self.clean_steam_downloads(results)
                elif task == "windows_update":
                    self.status.emit("Windows Update temizliği yapılıyor...")
                    self.clean_windows_update(results)
                elif task == "office_temp":
                    self.status.emit("Office geçici dosyaları temizleniyor...")
                    self.clean_office_temp(results)
            except Exception as e:
                results["errors"].append(str(e))
            
            completed_tasks += 1
            self.progress.emit(int((completed_tasks / total_tasks) * 100))
        
        self.finished.emit(results)

    def clean_windows_temp(self, results):
        temp_paths = [
            os.environ.get('TEMP'),
            os.environ.get('TMP'),
            os.path.join(os.environ.get('WINDIR'), 'Temp')
        ]
        
        for temp_path in temp_paths:
            if temp_path and os.path.exists(temp_path):
                for item in os.listdir(temp_path):
                    item_path = os.path.join(temp_path, item)
                    try:
                        size = self.get_size(item_path)
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        results["cleaned"] += size
                    except:
                        continue

    def clean_recycle_bin(self, results):
        try:
            # Geri dönüşüm kutusu boyutunu al
            recycle_size = 0
            for drive in range(65, 91):
                drive_letter = chr(drive)
                try:
                    recycler_path = f"{drive_letter}:\\$Recycle.Bin"
                    if os.path.exists(recycler_path):
                        recycle_size += self.get_size(recycler_path)
                except:
                    continue
            
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                            "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\BitBucket\\Volume")
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
            results["cleaned"] += recycle_size
        except Exception as e:
            raise Exception(f"Geri dönüşüm kutusu temizlenemedi: {str(e)}")

    def clean_fivem_cache(self, results):
        fivem_path = os.path.join(os.getenv('LOCALAPPDATA'), 'FiveM')
        
        if os.path.exists(fivem_path):
            cache_paths = [
                os.path.join(fivem_path, 'cache'),
                os.path.join(fivem_path, 'server-cache'),
                os.path.join(fivem_path, 'server-cache-priv')
            ]
            
            for path in cache_paths:
                if os.path.exists(path):
                    try:
                        size = self.get_size(path)
                        shutil.rmtree(path)
                        results["cleaned"] += size
                    except Exception as e:
                        raise Exception(f"FiveM cache temizlenemedi: {str(e)}")

    def clean_game_cache(self, results):
        game_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common",
            r"C:\Program Files\Epic Games",
            os.path.join(os.getenv('LOCALAPPDATA'), 'Origin'),
            os.path.join(os.getenv('PROGRAMDATA'), 'Origin')
        ]
        
        for base_path in game_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    if 'cache' in dirs or 'Cache' in dirs:
                        cache_dir = os.path.join(root, 'cache') if 'cache' in dirs else os.path.join(root, 'Cache')
                        try:
                            size = self.get_size(cache_dir)
                            shutil.rmtree(cache_dir)
                            results["cleaned"] += size
                        except:
                            continue

    def clean_downloads(self, results):
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        if os.path.exists(downloads_path):
            try:
                # 30 günden eski dosyaları temizle
                for item in os.listdir(downloads_path):
                    item_path = os.path.join(downloads_path, item)
                    if os.path.getctime(item_path) < (datetime.datetime.now() - datetime.timedelta(days=30)).timestamp():
                        try:
                            size = self.get_size(item_path)
                            if os.path.isfile(item_path):
                                os.unlink(item_path)
                            else:
                                shutil.rmtree(item_path)
                            results["cleaned"] += size
                        except:
                            continue
            except Exception as e:
                raise Exception(f"Downloads klasörü temizlenemedi: {str(e)}")

    def clean_prefetch(self, results):
        prefetch_path = os.path.join(os.environ.get('WINDIR'), 'Prefetch')
        if os.path.exists(prefetch_path):
            try:
                for item in os.listdir(prefetch_path):
                    item_path = os.path.join(prefetch_path, item)
                    try:
                        size = self.get_size(item_path)
                        os.unlink(item_path)
                        results["cleaned"] += size
                    except:
                        continue
            except Exception as e:
                raise Exception(f"Prefetch dosyaları temizlenemedi: {str(e)}")

    def clean_dns_cache(self, results):
        try:
            subprocess.run(['ipconfig', '/flushdns'], check=True)
            results["cleaned"] += 1024 * 1024  # Yaklaşık 1MB
        except Exception as e:
            raise Exception(f"DNS önbelleği temizlenemedi: {str(e)}")

    def clean_thumbnails(self, results):
        thumb_path = os.path.join(os.environ.get('LOCALAPPDATA'), 
                                 'Microsoft\\Windows\\Explorer')
        try:
            thumb_db = os.path.join(thumb_path, 'thumbcache_*.db')
            for file in Path(thumb_path).glob('thumbcache_*.db'):
                try:
                    size = os.path.getsize(file)
                    os.unlink(file)
                    results["cleaned"] += size
                except:
                    continue
        except Exception as e:
            raise Exception(f"Küçük resim önbelleği temizlenemedi: {str(e)}")

    def clean_error_reports(self, results):
        error_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA'), 'Microsoft\\Windows\\WER'),
            os.path.join(os.environ.get('PROGRAMDATA'), 'Microsoft\\Windows\\WER')
        ]
        
        for path in error_paths:
            if os.path.exists(path):
                try:
                    size = self.get_size(path)
                    shutil.rmtree(path)
                    os.makedirs(path)
                    results["cleaned"] += size
                except:
                    continue

    def clean_steam_downloads(self, results):
        steam_download_path = os.path.join(
            os.environ.get('PROGRAMFILES(X86)') or os.environ.get('PROGRAMFILES'),
            'Steam\\steamapps\\downloading'
        )
        
        if os.path.exists(steam_download_path):
            try:
                size = self.get_size(steam_download_path)
                for item in os.listdir(steam_download_path):
                    item_path = os.path.join(steam_download_path, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except:
                        continue
                results["cleaned"] += size
            except Exception as e:
                raise Exception(f"Steam indirme önbelleği temizlenemedi: {str(e)}")

    def clean_windows_update(self, results):
        update_paths = [
            os.path.join(os.environ.get('WINDIR'), 'SoftwareDistribution\\Download'),
            os.path.join(os.environ.get('WINDIR'), 'SoftwareDistribution\\DataStore')
        ]
        
        # Windows Update servisini durdur
        try:
            subprocess.run(['net', 'stop', 'wuauserv'], check=True)
            
            for path in update_paths:
                if os.path.exists(path):
                    try:
                        size = self.get_size(path)
                        shutil.rmtree(path)
                        os.makedirs(path)
                        results["cleaned"] += size
                    except:
                        continue
                        
            # Windows Update servisini yeniden başlat
            subprocess.run(['net', 'start', 'wuauserv'], check=True)
        except Exception as e:
            raise Exception(f"Windows Update temizliği yapılamadı: {str(e)}")

    def clean_office_temp(self, results):
        office_temp = os.path.join(
            os.environ.get('APPDATA'),
            'Microsoft\\Office\\Recent'
        )
        
        if os.path.exists(office_temp):
            try:
                size = self.get_size(office_temp)
                for item in os.listdir(office_temp):
                    item_path = os.path.join(office_temp, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                    except:
                        continue
                results["cleaned"] += size
            except Exception as e:
                raise Exception(f"Office geçici dosyaları temizlenemedi: {str(e)}")

class CleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("ArtseeN Sistem Temizleyici")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QCheckBox {
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 10pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
            QLabel {
                font-size: 10pt;
            }
        """)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("ArtseeN Sistem Temizleyici")
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Temizleme seçenekleri grubu
        cleanup_group = QGroupBox("Temizleme Seçenekleri")
        cleanup_layout = QVBoxLayout()
        
        self.checkboxes = {
            "windows_temp": QCheckBox("Windows Temp Dosyaları"),
            "recycle_bin": QCheckBox("Geri Dönüşüm Kutusu"),
            "fivem": QCheckBox("FiveM Cache ve Server Data"),
            "games": QCheckBox("Oyun Cache Dosyaları"),
            "downloads": QCheckBox("30 Günden Eski İndirilenler"),
            "prefetch": QCheckBox("Windows Prefetch Dosyaları"),
            "dns_cache": QCheckBox("DNS Önbelleği"),
            "thumbnails": QCheckBox("Windows Küçük Resim Önbelleği"),
            "error_reports": QCheckBox("Windows Hata Raporları"),
            "steam_download": QCheckBox("Steam İndirme Önbelleği"),
            "windows_update": QCheckBox("Eski Windows Update Dosyaları"),
            "office_temp": QCheckBox("Office Geçici Dosyaları")
        }
        
        for checkbox in self.checkboxes.values():
            cleanup_layout.addWidget(checkbox)
        
        cleanup_group.setLayout(cleanup_layout)
        layout.addWidget(cleanup_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Tümünü Seç")
        self.select_all_btn.clicked.connect(self.select_all)
        
        self.clean_button = QPushButton("Seçili Öğeleri Temizle")
        self.clean_button.clicked.connect(self.start_cleaning)
        
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.clean_button)
        layout.addLayout(button_layout)
        
        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Durum etiketi
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        main_widget.setLayout(layout)
        
        # Sistem bilgisi
        self.update_system_info()

    def select_all(self):
        all_selected = all(cb.isChecked() for cb in self.checkboxes.values())
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(not all_selected)

    def update_system_info(self):
        try:
            disk = psutil.disk_usage('/')
            free_space = disk.free / (1024 ** 3)  # GB cinsinden
            self.status_label.setText(f"Kullanılabilir Disk Alanı: {free_space:.2f} GB")
        except:
            self.status_label.setText("")

    def start_cleaning(self):
        selected_tasks = [key for key, cb in self.checkboxes.items() if cb.isChecked()]
        
        if not selected_tasks:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir temizleme seçeneği seçin!")
            return
        
        reply = QMessageBox.question(self, "Onay", 
                                   "Seçili öğeler silinecek. Devam etmek istiyor musunuz?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.progress_bar.setVisible(True)
            self.clean_button.setEnabled(False)
            self.select_all_btn.setEnabled(False)
            
            self.cleaner_thread = CleanerThread(selected_tasks)
            self.cleaner_thread.progress.connect(self.update_progress)
            self.cleaner_thread.status.connect(self.update_status)
            self.cleaner_thread.finished.connect(self.cleaning_finished)
            self.cleaner_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def cleaning_finished(self, results):
        self.progress_bar.setVisible(False)
        self.clean_button.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        
        cleaned_mb = results["cleaned"] / (1024 * 1024)  # MB cinsinden
        
        message = f"Temizlik tamamlandı!\nToplam {cleaned_mb:.2f} MB alan temizlendi."
        if results["errors"]:
            message += "\n\nBazı hatalar oluştu:"
            for error in results["errors"]:
                message += f"\n- {error}"
        
        QMessageBox.information(self, "Temizlik Tamamlandı", message)
        self.update_system_info()

def main():
    app = QApplication(sys.argv)
    window = CleanerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 