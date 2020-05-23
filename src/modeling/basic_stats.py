import os
import numpy as np
import pandas as pd
from skimage import io
from skimage.color import rgb2hsv
import cv2
from scipy import ndimage

def basic_image_stats(read_from, thumb_list):
    filenames = []
    for filename in os.listdir(read_from):
        if filename.endswith(".jpg") and (filename.split('.')[0] in thumb_list):
            filenames.append(filename)
    print("Getting basic stats for",len(filenames),"thumbnails")
    thumbnails = {'thumbnailFilename': filenames}
    df = pd.DataFrame(thumbnails)

    def get_video_id(filename):
        return filename.split('.')[0]
    
    videoId = df['thumbnailFilename'].apply(lambda x: get_video_id(x))
    df.insert(loc=0, column='videoId', value=videoId)
    
    def calc_image_stats(read_from, filename):
        filepath = read_from + filename
        image = io.imread(filepath)

        width = image.shape[0]
        height = image.shape[1]
        size = width*height

        rgb_img = image
        hsv_img = rgb2hsv(image)
        hue_img = hsv_img[:, :, 0]
        saturation_img = hsv_img[:,:, 1]
        value_img = hsv_img[:, :, 2]

        num_rgb = len(np.unique(rgb_img.reshape(-1, rgb_img.shape[2]), axis=0))
        
        unique_rgb_ratio = num_rgb/size
        
        mean_hue = np.mean(hue_img, axis=(0,1))

        mean_saturation = np.mean(saturation_img, axis=(0,1))

        mean_brightness = np.mean(value_img)

        img_grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contrast = img_grey.std()

        sobel_x = ndimage.sobel(value_img, axis=0, mode='constant')
        sobel_y = ndimage.sobel(value_img, axis=1, mode='constant')
        edge_image = np.hypot(sobel_x, sobel_y)
        edgesum = np.sum(edge_image)
        

        return {'size': size, 
                'num_rgb': num_rgb, 
                'unique_rgb_ratio': unique_rgb_ratio,
                'mean_hue': mean_hue, 
                'mean_saturation': mean_saturation, 
                'mean_brightness': mean_brightness, 
                'contrast': contrast, 
                'edge_score': edgesum}
    stats = []
    df['stats'] = df['thumbnailFilename'].apply(lambda x: calc_image_stats(read_from, x))
    df2 = pd.concat([df.drop(['stats'], axis=1), df['stats'].apply(pd.Series)], axis=1)
    
    # df2.to_csv(save_dir + "basic_stats.csv", index=False)

    return df2