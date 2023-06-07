from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from PyQt5.QtCore import Qt, QUrl
import subprocess
import sys
import ffmpeg
import os
import glob
import atexit
import shutil

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set the widget to accept drops, then reimplement
        # dragEnterEvent() and dropEvent() to handle drag and drop events
        self.setAcceptDrops(True)

        # File path
        self.file_path = ''
        self.processed_file_path = ''

        self.init_ui()

        # Register cleanup function to run when program exits
        atexit.register(self.cleanup)

    def cleanup(self):
        shutil.rmtree('.hansa', ignore_errors=True)

    def init_ui(self):
        self.setWindowTitle('Hansa')

        self.btn = QPushButton('Browse', self)
        self.btn.clicked.connect(self.browse_file)

        self.lbl = QLabel('Drop a file here or click on "Browse"', self)
        self.te = QTextEdit(self)
        self.te.setReadOnly(True)

        vbox = QVBoxLayout()
        vbox.addWidget(self.btn)
        vbox.addWidget(self.lbl)
        vbox.addWidget(self.te)

        self.setLayout(vbox)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        url = e.mimeData().urls()[0]
        file_path = str(url.toLocalFile())
        self.file_path = file_path
        self.lbl.setText(self.file_path)
        self.preprocess_file()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self)
        if file_path:
            self.file_path = file_path
            self.lbl.setText(self.file_path)
            self.preprocess_file()

    def display_text_file(self, base_filename):
        # Construct the text filename
        text_filename = f".hansa/{base_filename}.wav.txt"
        if os.path.exists(text_filename):
            with open(text_filename, 'r', encoding='utf-8') as file:
                text = file.read()
                self.te.setText(text)

    def execute_cpp_program(self):
        # Extract filename without extension
        base_filename = os.path.splitext(os.path.basename(self.processed_file_path))[0]
        # Construct the output filename
        command = ["./main_exec", "-t", "8", "-spd", "4", "-l", "de", "-m", "models/german_q4_0.bin", "-f", self.processed_file_path, "-otxt", "true", "--print-colors"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                self.te.append(output.strip())
        rc = process.poll()
        self.display_text_file(base_filename)


    def preprocess_file(self):
        # Extract filename without extension
        base_filename = os.path.splitext(os.path.basename(self.file_path))[0]
        # Construct the output filename
        if not os.path.exists('.hansa'):
            os.mkdir('.hansa')
        out_file = f".hansa/{base_filename}.wav"
        try:
            (
                ffmpeg
                .input(self.file_path)
                .output(out_file, acodec='pcm_s16le', ac=1, ar='16000')
                .run(capture_stdout=True, capture_stderr=True)
            )

            self.processed_file_path = out_file
            self.execute_cpp_program()

        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
            raise e

def main():
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
