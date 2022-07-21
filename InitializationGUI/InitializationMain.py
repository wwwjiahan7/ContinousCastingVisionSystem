"""
==================
Author: Yifei Zhang
Email: imeafi@gmail.com
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox
from Modules.parse import CfgManager
from InitializationGUI.TargetCircleWidget import TargetCircle
from InitializationCameraWidget import InitializationCameraWidget
from CalibrateWidget import Calibration
from harvesters.core import Harvester
from platform import system


class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.cfgManager = CfgManager(path='../CONF.cfg')
        self.initUI()
        self.clickedBinding()

    def initUI(self):
        self.setWindowTitle(self.tr('Initialization'))
        self.btn1 = QPushButton(self.tr('Distance & VOF\nCheck'))  # 距离与视场检查
        self.btn1.setFixedSize(120, 80)
        self.btn2 = QPushButton(self.tr('Hand-Eye\nCalibration'))  # 手眼标定
        self.btn2.setFixedSize(120, 80)
        self.btn3 = QPushButton(self.tr('Target Circle\n Adjustment'))  # 目标物体的拟合圆调整
        self.btn3.setFixedSize(120, 80)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.btn1)
        btnLayout.addWidget(self.btn2)
        btnLayout.addWidget(self.btn3)

        #============== Camera =========================
        self.h = Harvester()
        if system() == 'Linux':
            self.h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
        else:
            self.h.add_file('C:/Program Files/MATRIX VISION/mvIMPACT Acquire/bin/x64/mvGenTLProducer.cti')
        self.h.update()
        print(self.h.device_info_list)
        self.camera_1 = self.h.create_image_acquirer(0)
        self.camera_2 = self.h.create_image_acquirer(1)

        #self.camera_1 = self.h.create_image_acquirer(0)
        #self.camera_2 = self.h.create_image_acquirer(1)

        self.camera_1.start()
        self.camera_2.start()
        self.leftCamera = InitializationCameraWidget(cfg=self.cfgManager.cfg, cameraType=self.tr('LeftCamera'), harvesters=self.camera_1)
        self.rightCamera = InitializationCameraWidget(cfg=self.cfgManager.cfg, cameraType=self.tr('RightCamera'), harvesters=self.camera_2)
        #self.leftCamera.setFixedSize(self.leftCamera.w, self.leftCamera.h)
        #self.rightCamera.setFixedSize(self.rightCamera.w, self.rightCamera.h)


        #============== Calibration =================
        self.calibration = Calibration(cfg=self.cfgManager.cfg, parent=self)

        cameraLayout = QHBoxLayout()
        cameraLayout.addWidget(self.leftCamera)
        cameraLayout.addWidget(self.rightCamera)

        layout = QVBoxLayout()
        layout.addLayout(btnLayout)
        layout.addLayout(cameraLayout)

        self.im_np = self.leftCamera.camera.capture()
        self.h, self.w = self.im_np.shape
        self.resize(self.w * 2, self.h + 100)
        self.setLayout(layout)
        self.show()

    def clickedBinding(self):
        #self.distanceVOF = DistanceVOFCheck(self.cfgManager.cfg)
        self.btn1.clicked.connect(self.leftCamera.slot_draw_mininum_rects)
        self.btn1.clicked.connect(self.rightCamera.slot_draw_mininum_rects)

        #self.btn2.clicked.connect(self.calibration.slot_init)
        self.btn2.clicked.connect(self.slot_calibrate_btn)
        self.btn3.clicked.connect(self.slot_target_circle_btn)


    def slot_calibrate_btn(self):
        warningStr='Do you want to recalibrate the arm and the vision system?\n' \
                   'You are supposed to do this process only if one of the followings happened:\n' \
                   '1. This is a brand new system and have not calibrate yet.\n' \
                   '2. The relative position between cameras and the arm has been changed.\n' \
                   '3. The focal length of cameras has been changed.\n' \
                   'Before you click YES button please make sure the chessboard has been right installed on the' \
                   'end of arm.\n\n\n' \
                   'WARNING: THE ARM WILL MOVE AUTOMATICALLY DURING CALIBRATION.'

        ret = QMessageBox.warning(self, self.tr('Warning!'),
                                  self.tr(warningStr), QMessageBox.No, QMessageBox.Yes)

        if ret == QMessageBox.Yes:
            self.calibration.calibrateWidget.show()
            self.calibration.start()

    def slot_target_circle_btn(self):
        self.target_circle_widget = TargetCircle(self.cfgManager.cfg)
        self.target_circle_widget.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainGUI()
    sys.exit(app.exec())
