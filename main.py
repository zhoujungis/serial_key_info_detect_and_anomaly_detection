import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from log_key_info_analize import MainWindow as LogAnalyzeWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 9))

    window = LogAnalyzeWindow()
    window.show()
    sys.exit(app.exec())
