# -*- coding: utf-8 -*-

from data_process import *
import numpy as np
import torch
from torch.autograd import Variable
from torch import nn
import torchvision.models as models
import torch.cuda
import torchvision.transforms as transforms

import os
import librosa
import pickle
import threading

img_to_tensor = transforms.ToTensor()


def make_model():
    vggmodel = models.vgg16(pretrained=True)
    vggmodel.classifier=nn.Sequential(*list(vggmodel.classifier.children())[:-3])
    vggmodel = vggmodel.eval()  # 一定要有这行，不然运算速度会变慢（要求梯度）而且会影响结果

    # vggmodel.cuda()  # 将模型从CPU发送到GPU,如果没有GPU则删除该行
    return vggmodel


def extract_feature(model,data):
    model.eval()  # 必须要有，不然会影响特征提取结果
    data = torch.tensor(data, dtype=torch.float32)
    # data = data.cuda()  # 如果只是在cpu上跑的话要将这行去掉
    with torch.no_grad():
        result = model(Variable(data))

    result_npy = result.data.cpu().numpy()  # 保存的时候一定要记得转成cpu形式的，不然可能会出错

    return result_npy  # 返回的矩阵shape是[1, 512, 14, 14]，这么做是为了让shape变回[512, 14,14]


def extract_img(video_dir, jpg_dir): #加载视频图像数据集，加载模型，特征提取部分在界面部分
    # os.environ["CUDA_VISIBLE_DEVICES"] = '0'

    myUCF101 = UCF101(video_dir, jpg_dir,
                      transform=transforms.Compose([ClipSubstractMean(), RandomCrop(), ToTensor()]))

    imgdataloader = DataLoader(myUCF101, batch_size=2, shuffle=False) #设置batch_size为2
    model = make_model()

    return imgdataloader,model,myUCF101.__len__()

mutex=threading.Lock()

def extract_audio(audio_dir): #提取音频特征
    audio_features=[]

    for class_name in os.listdir(audio_dir):
        class_path = os.path.join(audio_dir, class_name)
        for file_name in os.listdir(class_path):
            mutex.acquire()
            try:
                file=os.path.join(class_path, file_name)
                y,sr=librosa.load(file)
                mfcc=librosa.feature.mfcc(y,sr,n_mfcc=13)
            # time.sleep(5)
            except Exception as e:
                print(e)
                fl = open('log.txt', 'a')
                fl.write(str(e) + "\n")
                fl.close()
            audio_features.append(mfcc)
            mutex.release()

    fw = open('AudioFeatures.txt', 'wb')
    pickle.dump(audio_features, fw)
    fw.close()

if __name__=="__main__":

    os.environ["CUDA_VISIBLE_DEVICES"] = '0'

    video_dir = 'x'
    jpg_dir = 'x_jpg'


    myUCF101 = UCF101(video_dir, jpg_dir,
                      transform=transforms.Compose([ClipSubstractMean(),RandomCrop(), ToTensor()]))

    imgdataloader = DataLoader(myUCF101, batch_size=1, shuffle=False)
    model=make_model()


    features = []
    num=0
    for i_batch, sample_batched in enumerate(imgdataloader):
        sample_batched = np.array(sample_batched['video_x'])
        for i in range (2):

            tmp = extract_feature(model, sample_batched[i])

            features.append(tmp)
            print(tmp)
            num += 1
            info="共"+str(myUCF101.__len__())+"个视频，已处理"+str(num)+"个视频"
            print(info)





