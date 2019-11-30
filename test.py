# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'extract_video_features.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from extract_features import extract_img,extract_audio,extract_feature
import video_jpg_ucf101_hmdb51
import n_frames_ucf101_hmdb51
import audio_wav_ucf101_hmdb51
import numpy as np
import pickle
import time


class Ui_Form(QWidget):
    def setupUi(self, Form):

        Form.setObjectName("Form")
        Form.resize(461, 381)
        # self.listWidget = QListWidget()
        self.verticalLayoutWidget = QWidget(Form)
        self.verticalLayoutWidget.setGeometry(QRect(30, 170, 401, 181))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")


        global textBrowser
        textBrowser = QTextBrowser(self.verticalLayoutWidget)
        textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(textBrowser)
        self.label = QLabel(Form)
        self.label.setGeometry(QRect(30, 20, 61, 16))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("label")
        self.lineEdit = QLineEdit(Form)
        self.lineEdit.setGeometry(QRect(90, 20, 251, 21))
        self.lineEdit.setObjectName("lineEdit")
        self.pushButton = QPushButton(Form)
        self.pushButton.setGeometry(QRect(360, 20, 61, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.select_directory)

        self.pushButton_2 = QPushButton(Form)
        self.pushButton_2.setGeometry(QRect(30, 60, 401, 91))


        font = QFont()
        font.setFamily("Bauhaus 93")
        font.setPointSize(28)
        font.setBold(False)
        font.setWeight(50)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setIconSize(QSize(30, 30))
        self.pushButton_2.setObjectName("pushButton_2")

        self.thread=work_img()
        self.thread1=work_audio()
        self.thread1.trigger.connect(self.slotEnd)
        self.pushButton_2.clicked.connect(self.slotStart)
        # self.thread.start()
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
        self.timer = QTimer()
        self.timer.timeout.connect(self.showTime)


    def showTime(self):
        # 获取系统当前时间
        global flag
        time = QDateTime.currentDateTime()
        # 设置系统时间的显示格式
        timeDisplay = self.startime.msecsTo(time)
        # 在标签上显示时间
        if flag==1:
            textBrowser.append(str(timeDisplay/1000)+'s')
            textBrowser.moveCursor(textBrowser.textCursor().End)
        flag=0

    def startTimer(self):
        # 设置时间间隔并启动定时器
        self.startime=QDateTime.currentDateTime()
        self.timer.start(1)


    def endTimer(self):
        # 停止定时器
        self.timer.stop()

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Extract Video Features"))
        self.label.setText(_translate("Form", "Video:"))
        self.pushButton.setText(_translate("Form", "Select"))
        self.pushButton_2.setText(_translate("Form", "START!"))

    def select_directory(self):
        global video_dir, jpg_dir, audio_dir
        video_dir= QFileDialog.getExistingDirectory(self, "select directory", "./")

        print(video_dir)
        self.lineEdit.setText(video_dir)
        jpg_dir = "{}_jpg".format(video_dir)
        audio_dir = "{}_wav".format(video_dir)

    def slotStart(self):
        self.pushButton_2.setEnabled(False)
        self.startTimer()
        self.thread.start()
        # time.sleep(5)
        self.thread1.start()

    def slotEnd(self):
        self.pushButton_2.setEnabled(True)
        self.endTimer()



class work_img(QThread):
    trigger = pyqtSignal(int) # 自定义信号，执行run()函数时，从相关线程发射此信号

    def __init__(self):
        super(work_img, self).__init__()
        self.mutex = QMutex()

        # self.working = True
        # self.num = 0

    # def __del__(self):
    #     self.working = False
    #     self.wait()

    def run(self):

        try:
            if video_dir==0:
                raise Exception
        except:
            print("error")
            self.trigger.emit()
            return
        # print("开始")
        self.mutex.lock()
        if not os.path.exists(jpg_dir):

            for class_name in os.listdir(video_dir):

                video_jpg_ucf101_hmdb51.class_process(video_dir, jpg_dir, class_name)


            for class_name in os.listdir(jpg_dir):

                n_frames_ucf101_hmdb51.class_process(jpg_dir, class_name)

        # print("预处理结束")
        imgdataloader, model, len = extract_img(video_dir,jpg_dir)
        features = []
        num = 0
        # QThread.sleep(1000)

        # 提取图像特征
        # 设置batch_size为2，每个视频选取16帧，（16,3,224,224）
        for i_batch, sample_batched in enumerate(imgdataloader):

            sample_batched = np.array(sample_batched['video_x'])
            try:
                for i in range(2):
                    # self.mutex.lock()
                    flag=0
                    tmp = extract_feature(model, sample_batched[i])
                    # self.mutex.unlock()
                    # QThread.sleep(1)
                    features.append(tmp)
                    num += 1
                    info = "共" + str(len) + "个视频，已处理" + str(num) + "个视频，未处理"+str(len-num)+"个视频"
                    print(info)
                    flag=1
                    textBrowser.append(info)
                    textBrowser.moveCursor(textBrowser.textCursor().End)  # 文本框显示到底部
            except Exception as e:
                print(e)
                # QThread.sleep(1)
                # self.sleep(5)

        fw = open('ImageFeatures.txt', 'wb')
        pickle.dump(features, fw)
        fw.close()

        # print("结束")


        self.mutex.unlock()
        # try:

        self.trigger.emit(1)
        # except Exception as e:
        #     print(e)

            # self.sleep(1)

class work_audio(QThread):
    trigger = pyqtSignal(int)  # 自定义信号，执行run()函数时，从相关线程发射此信号

    def __init__(self):
        super(work_audio, self).__init__()
        self.mutex = QMutex()

    def run(self):
        try:
            if video_dir==0:
                raise Exception
        except:
            # print("error")
            self.trigger.emit()
            return
        # print("开始1")
        self.mutex.lock()
        if not os.path.exists(audio_dir):
            for class_name in os.listdir(video_dir):

                audio_wav_ucf101_hmdb51.class_process(video_dir, audio_dir, class_name)

                # QThread.sleep(1)
        # print("预处理2结束")
        # QThread.sleep(1000)
        try:
            extract_audio(video_dir)
        except Exception as e:
            print(e)


        # print("结束1")
        self.mutex.unlock()
        self.trigger.emit(2)


if __name__=="__main__":
    import sys
    from PyQt5.QtGui import QIcon
    app=QApplication(sys.argv)
    widget=QWidget()
    ui=Ui_Form()
    ui.setupUi(widget)
    widget.setWindowIcon(QIcon('web.png'))#增加icon图标，如果没有图片可以没有这句
    widget.show()
    sys.exit(app.exec_())