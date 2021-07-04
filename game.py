import sys

from PyQt5.QtWidgets import *

from qt_widgets import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
app.exec_()
