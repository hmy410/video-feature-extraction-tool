from __future__ import print_function, division
import os
import sys
import subprocess
# import time

def class_process(dir_path, dst_dir_path, class_name):
  class_path = os.path.join(dir_path, class_name)
  if not os.path.isdir(class_path):
    return

  dst_class_path = os.path.join(dst_dir_path, class_name)
  if not os.path.exists(dst_class_path):
    os.makedirs(dst_class_path)

  for file_name in os.listdir(class_path):
    if '.avi' not in file_name:
      continue
    name, ext = os.path.splitext(file_name)

    video_file_path = os.path.join(class_path, file_name)
    try:
      if os.path.exists(video_file_path):
        # print(2)
        # time.sleep(2)
        if not os.path.exists(os.path.join(dst_class_path, '{}.wav'.format(name))):
          cmd = 'ffmpeg -i \"{}\" -f wav -vn \"{}/{}.wav\"'.format(video_file_path, dst_class_path, name)
          # print(cmd)
          fw = open('log.txt', 'a')
          fw.write(cmd)
          fw.close()
          subprocess.call(cmd, shell=True)
          # print('\n')
        else:
          continue
      else:
        os.mkdir(video_file_path)
    except:
      # print(video_file_path)
      continue


if __name__=="__main__":
  dir_path = sys.argv[1]
  dst_dir_path = sys.argv[2]

  for class_name in os.listdir(dir_path):
    class_process(dir_path, dst_dir_path, class_name)