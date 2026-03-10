import sys
import os
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clandestina - Recomendador de Vinos")
        self.setGeometry(100, 100, 1200, 800)
        
        # Enable developer tools to debug
        self.browser = QWebEngineView()
        
        # Determinar la ruta base. PyInstaller extrae los archivos temporales a sys._MEIPASS
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        index_path = os.path.join(base_dir, "index.html")
        self.browser.load(QUrl.fromLocalFile(index_path))
        
        self.setCentralWidget(self.browser)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
