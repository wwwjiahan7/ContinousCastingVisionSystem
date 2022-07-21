import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFont
from CoreSystemGUI.ControlPanle.ControlPanleWidget import ControlPanleWidget
from Modules.system import *
from CoreSystemGUI.CameraPanle.CoreSystemCameraWidget import CoreSystemCameraWidget
from CoreSystemGUI.ControlPanle.MoreWidget import MoreWidget

class MainGUI(QObject):
    def __init__(self, path='CONF.cfg'):
        super().__init__()
        self.core = CoreSystem()
        self.core.start()  # backend计算线程开启
        # 当CoreSystem后背资源加载完毕后，启动主界面
        self.core.resourceInitOKSignal.connect(self.initUI)
        #self.initUI()


    def initUI(self):
        self.cfg = self.core.cfgManager.cfg
        self.leftCameraWidget = CoreSystemCameraWidget(cfg=self.cfg, cameraType=self.tr('LeftCamera'), harvesters=self.core.left_cam)
        self.rightCameraWidget = CoreSystemCameraWidget(cfg=self.cfg, cameraType=self.tr('RightCamera'), harvesters=self.core.right_cam)
        self.core.left_cam = self.leftCameraWidget
        self.core.right_cam = self.rightCameraWidget
        # ControlPanle实例化
        self.controlPanle = ControlPanleWidget(cfg=self.cfg)


        # =========================================   Signal Slot 绑定 ==============================================

        # ControlPanle - STATUS WIDGET 状态刷新绑定
        self.leftCameraWidget.cameraStatusSignal.connect(self.controlPanle.statusWidget.leftCameraStatusLabel.clrChange)
        self.rightCameraWidget.cameraStatusSignal.connect(self.controlPanle.statusWidget.rightCameraStatusLabel.clrChange)
        self.leftCameraWidget.cameraStatusSignal.connect(self.core.robot.set_left_camera)
        self.rightCameraWidget.cameraStatusSignal.connect(self.core.robot.set_right_camera)
        self.leftCameraWidget.cameraStatusSignal.emit('OK')
        self.rightCameraWidget.cameraStatusSignal.emit('OK')
        self.controlPanle.statusWidget.cudaStatusLabel.clrChange('OK' if self.core.cuda_available else 'Break')
        self.core.robot.network.robotCommunicationStatusSignal.connect(self.controlPanle.statusWidget.robotStatusLabel.clrChange)


        ### 相机状态与核心检测器的绑定: 每次相机状态刷新时，同时调用检测器
        #self.leftCameraWidget.cameraStatusSignal.connect(self.core.detect)
        #self.rightCameraWidget.cameraStatusSignal.connect(self.core.detect)

        # ControlPanle - BUTTON WIDGET 按键绑定
        self.controlPanle.buttonWidget.button_visCamera1.clicked.connect(self.leftCameraWidget.show)  # 相机按钮绑定
        self.controlPanle.buttonWidget.button_visCamera2.clicked.connect(self.rightCameraWidget.show)
        self.controlPanle.buttonWidget.button_log.clicked.connect(self.controlPanle.buttonWidget.logWidgetPop) # 日志按钮绑定
        self.controlPanle.buttonWidget.button_showLogDir.clicked.connect(self.controlPanle.buttonWidget.logDirPop)
        self.controlPanle.buttonWidget.button_moreSettings.clicked.connect(self.more_btn_slot)


        # ControlPanle - Visualization Widget 框选绑定
        self.controlPanle.visualizationWidget.ROICheckBox.stateChanged.connect(self.leftCameraWidget.toggle_rois)
        self.controlPanle.visualizationWidget.ROICheckBox.stateChanged.connect(self.rightCameraWidget.toggle_rois)
        self.controlPanle.visualizationWidget.targetsCheckBox.stateChanged.connect(self.leftCameraWidget.toggle_targets)
        self.controlPanle.visualizationWidget.targetsCheckBox.stateChanged.connect(self.rightCameraWidget.toggle_targets)



        # CoreSystem 核心算法检测到rect的信号绑定
        self.core.targetFoundSignal.connect(self.leftCameraWidget.found_targets_slot)
        self.core.targetFoundSignal.connect(self.rightCameraWidget.found_targets_slot)

        # =========================================   Signal Slot 绑定 ==============================================
        self.controlPanle.setWindowTitle('无人化浇钢视觉引导系统')
        self.controlPanle.setWindowIcon(QIcon('../xjtu.jpg'))
        font = QFont()
        font.setPointSize(10)
        font.setFamily('Microsoft Yahei UI')
        self.controlPanle.setFont(font)
        self.controlPanle.show()

    def more_btn_slot(self):
        self.moreWidget = MoreWidget(self.core.cfg, self.leftCameraWidget, self.rightCameraWidget)
        self.moreWidget.show()





if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainGUI()
    sys.exit(app.exec())
