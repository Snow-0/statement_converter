import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QFileDialog,
    QLineEdit,
    QComboBox,
)
from PyQt5 import uic
from converter import convert_csv
import os


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
        self.label_3 = self.findChild(QLabel, "label_3")

        self.combo_box = self.findChild(QComboBox, "comboBox")

        self.file_name = self.findChild(QLineEdit, "lineEdit")

        self.button.clicked.connect(self.open_file)
        self.export_button.clicked.connect(self.save_output)

        self.convert_button.clicked.connect(self.convert)
        self.setGeometry(400, 400, 680, 450)

        self.file = ""
        self.save_loc = ""

    def open_file(self):
        file_filter = "PDF Files (*.pdf)"
        self.file = QFileDialog.getOpenFileName(self, "Open PDF File", "", file_filter)[
            0
        ]
        file_name = os.path.basename(self.file).split("/")[-1]
        self.label.setText(f"File: {file_name}")

    # implement export location feature
    def save_output(self):
        self.save_loc = QFileDialog.getExistingDirectory(self, "Select Directory", "")
        self.label_2.setText(f"Export: {self.save_loc}")

    def convert(self):
        bank = self.combo_box.currentText()
        #        try:
        #            convert_csv(self.file, bank, self.save_loc, self.file_name.text())
        #            self.label_3.setText("Done!")
        #        except ValueError:
        #            self.label_3.setText("Error! Please try again.")
        #
        convert_csv(self.file, bank, self.save_loc, self.file_name.text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
