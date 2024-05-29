import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import func


class Worker(QThread):
    updateProgressBar = pyqtSignal(int)

    def __init__(self, tid, cookie, local, max_connections):
        super().__init__()
        self.tid = tid
        self.cookie = cookie
        self.local = local
        self.max_connections = max_connections

    def run(self):
        func.run(self.tid, self.cookie, self.local, self.max_connections, self.updateProgressBar.emit)

class FileSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("标题随便放点字在这里先")
        self.setGeometry(300, 300, 300, 250)  # 调整高度以容纳新增的组件

        layout = QVBoxLayout()
        
        label = QLabel('<font color="red">不要用中文路径，不要开 VPN！</font>', self)
        layout.addWidget(label)

        # 文本输入框 - tid
        self.tid_input = QLineEdit(self)
        self.tid_input.setPlaceholderText("输入tid")
        self.tid_input.setText("8892250740")
        layout.addWidget(self.tid_input)

        # 文本输入框 - cookie
        self.cookie_input = QLineEdit(self)
        self.cookie_input.setPlaceholderText("输入cookie")
        self.cookie_input.setText('XFI=33b27440-1d7f-11ef-ad4e-3b2a0ca8cab7; XFCS=62FD6F9BD9DD17E1E58018D2AAC610B1DA4B6FC15FA68D5E1A02FB1C95C00A25; XFT=PCIn/Mtr430jxKJ+nBC7w1VGWqf2DM4xar/QLO8t2IU=; BAIDUID=50DFFCB34021D66BFD437AD9A55916A6:FG=1; BAIDUID_BFESS=50DFFCB34021D66BFD437AD9A55916A6:FG=1; wise_device=0; BAIDU_WISE_UID=wapp_1716961665661_746; USER_JUMP=-1; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1716961671; ZFY=Hh09UU25i3arQzQ1suChj4:B6E5hWb:BI6btej284IBkg:C; arialoadData=false; st_key_id=17; tb_as_data=6272a347d8193d2766af8a4794bc92e2d9e54f46e8875d78526de9c2048b5c3d1dac954a3133e0867d9f1672a2435eaf379d2eb4fc42a43bef3411eaec68f3472405280b239b698017b4424c79f31ba28032eab2c1cf5d0f3038b3601f603b09e366b265f9538e69fe99fdead2ba399d; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1716961763; BA_HECTOR=852k8k250h8ga4a1040kag25d4f3si1j5dgf41u; ab_sr=1.0.1_ZTZmNWE2Mzc3MzFmOTRhZWZlMDhmNTg1ODJiYTc2YTUyZTEwZTUzZjI2ODM3M2Q4ZTBiYzcwMDQ2NGM3YjE1Njk2ZTQ2MjdhZGQ4NWFlMzhlNDNjY2ZhYjA4NWY2NTBlM2FmNGNkMTZmZTI4MzY1YzU5Y2ZlOTI1MzRmMTVmNDIzNDk4MTNkN2RiNWJkNzQ1NjM2M2RkNWNlOTdjMjkyMQ==; st_data=82b512455d8039d51dd2cc1a73ed15ac8ccb71abe39f94fd1b99bed477311491f6629667514219722b4422dc789c27c86fdde1c8371c4c117bd81dd36eb98eb2744704d2532be3dd1c8594e1372330d27cdb155e1d0993d9f34fbf19bf51597de3b9a6a08b8309543c9de3dec4d65248ec8debd4654a2bbde2ec0e346ab64cf1751d3353943f2b21698a3e6574a2c5f9; st_sign=590cb5b1; RT="z=1&dm=baidu.com&si=04b4184f-f239-4c7c-b97b-73596d97f3f1&ss=lwr7syg2&sl=v&tt=13lnp&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=708xk&ul=7ah4d"')
        layout.addWidget(self.cookie_input)

        # Checkbox - 是否图片本地化
        self.checkbox_localize = QCheckBox("是否图片本地化", self)
        layout.addWidget(self.checkbox_localize)

        # 数字输入框 - 最大线程数
        self.thread_input = QSpinBox(self)
        self.thread_input.setMinimum(1)
        self.thread_input.setMaximum(100)  # 根据需求调整最大值
        self.thread_input.setValue(10)  # 默认值为10
        layout.addWidget(self.thread_input)

        # 开始按钮
        self.btn_start = QPushButton("🚀Start!", self)
        self.btn_start.clicked.connect(self.start_thread)
        layout.addWidget(self.btn_start)

        # 进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # 子线程执行任务
        self.my_thread = None
        

    def start_thread(self):
        if not self.my_thread or not self.my_thread.isRunning():
            self.my_thread = Worker(
                self.tid_input.text(),
                self.cookie_input.text(),
                self.checkbox_localize.isChecked(),
                self.thread_input.value()
            )
            self.my_thread.updateProgressBar.connect(self.updateProgressBar)
            self.my_thread.start()
            self.btn_start.setText("Downloading...")
            # self.my_thread.join()
            # self.btn_start.setText("🚀Start!")

    def updateProgressBar(self, cnt):
        self.progress_bar.setValue(cnt)


def main():
    app = QApplication(sys.argv)
    ex = FileSelector()
    ex.show()
    sys.exit(app.exec_())
