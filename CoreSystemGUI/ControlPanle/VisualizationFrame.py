from PyQt5.QtWidgets import QFrame, QCheckBox, QVBoxLayout


class VisualizationFrame(QFrame):
    def __init__(self, cfg):
        super(VisualizationFrame, self).__init__()
        self.cfg = cfg
        # 只用于ROI区域显示，并不会影响ROI本身
        self.ROICheckBox = QCheckBox(self.tr('检测区域显示'))  # 在main.py中绑定
        # 显示检测结果
        self.targetsCheckBox = QCheckBox(self.tr('检测目标显示'))  # 在main.py中绑定

        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Sunken)
        vboxlayout = QVBoxLayout()
        vboxlayout.addWidget(self.ROICheckBox)
        vboxlayout.addWidget(self.targetsCheckBox)

        self.setLayout(vboxlayout)
