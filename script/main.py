import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QLineEdit,
    QCheckBox,
    QLabel,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import func
import asyncio


class Worker(QThread):
    updateProgressBar = pyqtSignal(int)
    updateButtonText = pyqtSignal(str)

    def __init__(self, tid, local):
        super().__init__()
        self.tid = tid
        self.local = local

    def run(self):
        asyncio.run(
            func.run(
                self.tid,
                self.local,
                self.updateProgressBar.emit,
                self.updateButtonText.emit,
            )
        )


class FileSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("标题随便放点字在这里先")
        self.setGeometry(300, 300, 300, 200)  # 调整高度以容纳新增的组件

        layout = QVBoxLayout()

        label = QLabel('<font color="red">不要开 VPN！</font>', self)
        layout.addWidget(label)

        # 文本输入框 - url
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("输入url")
        layout.addWidget(self.url_input)

        # Checkbox - 是否图片本地化
        self.checkbox_localize = QCheckBox("是否图片本地化", self)
        layout.addWidget(self.checkbox_localize)

        # 开始按钮
        self.btn_start = QPushButton("🚀Start!", self)
        self.btn_start.clicked.connect(self.start_thread)
        layout.addWidget(self.btn_start)

        # 进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # 子线程执行任务
        self.my_thread = None

    def start_thread(self):
        if not self.my_thread or not self.my_thread.isRunning():
            self.my_thread = Worker(
                int(self.url_input.text().split("?")[0].split("#")[0].split("/")[-1]),
                self.checkbox_localize.isChecked(),
            )
            self.my_thread.updateProgressBar.connect(self.updateProgressBar)
            self.my_thread.updateButtonText.connect(self.updateButtonText)
            self.my_thread.start()

    def updateProgressBar(self, cnt):
        self.progress_bar.setValue(cnt)

    def updateButtonText(self, msg):
        self.btn_start.setText(msg)


def main():
    app = QApplication(sys.argv)
    ex = FileSelector()
    ex.show()
    sys.exit(app.exec_())
