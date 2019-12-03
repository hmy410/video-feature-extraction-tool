# -*- coding: utf-8 -*-

from __future__ import print_function, division
import os
import pandas as pd
from skimage import io, transform
import numpy as np
import random
import torch
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
# Ignore warnings
import warnings
warnings.filterwarnings("ignore")
plt.ion()   # interactive mode
TARGET_IMG_SIZE = 224


class ClipSubstractMean(object): #减去rgb的平均值
    def __init__(self, b=104, g=117, r=123):
        self.means = np.array((r, g, b)) #rgb的平均值

    def __call__(self, sample):
        video_x = sample['video_x']
        new_video_x = video_x - self.means #减去rgb的平均值
        return {'video_x': new_video_x}


class Rescale(object): #大小调整为(182,242)
    """Rescale the image in a sample to a given size.

    Args:
        output_size (tuple or int): Desired output size. If tuple, output is
            matched to output_size. If int, smaller of image edges is matched
            to output_size keeping aspect ratio the same.
    """

    def __init__(self, output_size=(182, 242)):
        assert isinstance(output_size, (int, tuple))
        self.output_size = output_size

    def __call__(self, sample):
        video_x= sample['video_x']

        h, w = video_x.shape[1], video_x[2]
        if isinstance(self.output_size, int):
            if h > w:
                new_h, new_w = self.output_size * h / w, self.output_size
            else:
                new_h, new_w = self.output_size, self.output_size * w / h
        else:
            new_h, new_w = self.output_size

        new_h, new_w = int(new_h), int(new_w)
        new_video_x = np.zeros((16, new_h, new_w, 3))
        for i in range(16):
            image = video_x[i, :, :, :]
            img = transform.resize(image, (new_h, new_w))
            new_video_x[i, :, :, :] = img

        return {'video_x': new_video_x}


class RandomCrop(object): #对修改过大小的帧随机截取(TARGET_IMG_SIZE,TARGET_IMG_SIZE)
    """Crop randomly the image in a sample.

    Args:
        output_size (tuple or int): Desired output size. If int, square crop
            is made.
    """

    def __init__(self, output_size=(TARGET_IMG_SIZE)):
        assert isinstance(output_size, (int, tuple))
        if isinstance(output_size, int):
            self.output_size = (output_size, output_size)
        else:
            assert len(output_size) == 2
            self.output_size = output_size

    def __call__(self, sample):
        video_x = sample['video_x']

        h, w = video_x.shape[1], video_x.shape[2]
        new_h, new_w = self.output_size
        np.random.seed(0)
        top = np.random.randint(0, h - new_h)
        left = np.random.randint(0, w - new_w)

        new_video_x = np.zeros((16, new_h, new_w, 3))
        for i in range(16):
            image = video_x[i, :, :, :]
            image = image[top: top + new_h, left: left + new_w]
            # image= transform.resize(image,(TARGET_IMG_SIZE,TARGET_IMG_SIZE))
            new_video_x[i, :, :, :]=image


        return {'video_x': new_video_x}


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample):
        video_x = sample['video_x']

        # swap color axis because
        # numpy image: batch_size x H x W x C
        # torch image: batch_size x C X H X W
        video_x = video_x.transpose((0, 3, 1, 2))
        video_x = np.array(video_x)

        return {'video_x': torch.from_numpy(video_x)}


class UCF101(Dataset):
    """UCF101 Landmarks dataset."""

    def __init__(self, video_dir, jpg_dir, transform=None):
        """
        Args:
            info_list (string): Path to the info list file with annotations.
            root_dir (string): Directory with all the video frames.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.landmarks_frame = pd.DataFrame()

        for _,_,i in os.walk(video_dir):
            if i:

                self.landmarks_frame=self.landmarks_frame.append(i,ignore_index=True)


        self.video_dir = video_dir
        self.jpg_dir=jpg_dir
        self.transform = transform

    def __len__(self):
        return len(self.landmarks_frame)

    # get (16,240,320,3) 原图片大小320*240
    def __getitem__(self, idx):
        path=self.landmarks_frame.iloc[idx,0].split("_")
        video_path=os.path.join(self.video_dir,path[1])
        video_path = os.path.join(video_path, self.landmarks_frame.iloc[idx,0])

        # video_label = self.landmarks_frame.iloc[idx, 1]
        video_x = self.get_single_video_x(video_path)
        sample = {'video_x': video_x}

        if self.transform:
            sample = self.transform(sample)
        return sample

    def get_single_video_x(self, video_path):
        path = video_path.split('/')
        path=path[-1].split('\\')
        slash_rows=path[-1].split('.')
        dir_name = os.path.join(path[1],slash_rows[0])

        video_jpgs_path = os.path.join(self.jpg_dir, dir_name)
        # get the random 16 frame
        data = pd.read_csv(os.path.join(video_jpgs_path, 'n_frames'), delimiter=' ', header=None)
        frame_count = data[0][0]
        video_x = np.zeros((16, 240, 320, 3))
        random.seed(0)
        image_start = random.randint(1, frame_count - 17) #随机取连续的16帧，start随机
        image_id = image_start
        for i in range(16):
            s = "%05d" % image_id
            image_name = 'image_' + s + '.jpg'
            image_path = os.path.join(video_jpgs_path, image_name)
            tmp_image = io.imread(image_path)

            video_x[i, :, :, :] = tmp_image
            image_id += 1
        return video_x




if __name__ == '__main__':

    video_dir = 'test'
    jpg_dir='test_jpg'
    # info_list = 'ucfTrainTestlist/list.txt'

    myUCF101 = UCF101(video_dir, jpg_dir,
                      transform=transforms.Compose([ClipSubstractMean(),RandomCrop(), ToTensor()]))

    dataloader = DataLoader(myUCF101, batch_size=2, shuffle=False, num_workers=8)

    for i_batch, sample_batched in enumerate(dataloader):
        #batch_size=8,16帧,处理后的图像大小(224,224)
        print(i_batch, sample_batched['video_x'])
