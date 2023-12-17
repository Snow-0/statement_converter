import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, \
     QWidget, QPushButton, QLabel, QFileDialog, QRadioButton)
from PyQt5 import uic

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui.ui", self)

        # create the buttons and labels
        self.setWindowTitle("Bank Statement Converter")
        self.convert_button = self.findChild(QPushButton, "pushButton_3")
        self.button = self.findChild(QPushButton, "pushButton")
        self.export_button = self.findChild(QPushButton, "pushButton_2")

        self.label = self.findChild(QLabel, "label")
        self.label_2 = self.findChild(QLabel, "label_2")

        self.boa_radio = self.findChild(QRadioButton, "radioButton")
        self.wf_radio = self.findChild(QRadioButton, "radioButton_2")
        self.ewb_radio = self.findChild(QRadioButton, "radioButton_3")
        self.truist_radio = self.findChild(QRadioButton, "radioButton_4")



        self.button.clicked.connect(self.open_file)
        self.export_button.clicked.connect(self.set_output)

        self.convert_button.clicked.connect(self.convert)


    def open_file(self):
        file_filter = "PDF Files (*.pdf)"
        file = QFileDialog.getOpenFileName(self, "Open PDF File", "", file_filter)[0]
        self.label.setText(file)
    

    # implement export location feature
    def set_output(self):
        pass

    def convert(self):
        bank = ""
        if self.boa_radio.isChecked():
            bank = "Bank of America"
        if self.wf_radio.isChecked():
            bank = "Wells Fargo"
        if self.ewb_radio.isChecked():
            bank = "EastWest Bank"
        if self.truist_radio.isChecked():
            bank = "Truist Bank"


        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    

