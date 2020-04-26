import cv2
import matplotlib.pyplot as plt
from skimage import io
from skimage.color import rgb2gray, gray2rgb, rgb2hsv
from scipy import ndimage
import numpy as np
from PIL import Image
import os
import pandas as pd
import face_recognition
from deepface import DeepFace

def facial_recognition(filename, cnn=True):
    image = face_recognition.load_image_file(filename)
    if cnn:
        face_locations = face_recognition.face_locations(image, model='cnn')
    else:
        face_locations = face_recognition.face_locations(image)
    return image, len(face_locations), face_locations

def facial_analysis(face_locations,image,config='age, gender, race, emotion'):
    if len(face_locations)>0:
        config = config.split(',')
        config = [c.strip() for c in config]
        results = []
        im = Image.fromarray(image)
        for f in face_locations:
            face = im.crop((f[3],f[0],f[1],f[2]))
            face = np.asarray(face)
            demography = DeepFace.analyze(face,config)
            results.append(demography)
        return results, face_locations
    else:
        return [],face_locations

def facial_percentage(face_locations,image):
    result = []
    img_pixelcount = image_obj.shape[0]*image_obj.shape[1]
    for f in face_locations:
        face_pixels = (f[2]-f[0])*(f[1]-f[3])
        result.append(face_pixels/img_pixelcount)
    return result

def create_feature_database(IMG_DIR):
    cols = ['videoId','numFaces','emotions','face_locations','face_percent']
    feature_df = pd.DataFrame(columns=cols)
    for filename in os.listdir(IMG_DIR):
        genders = []
        image_obj,num_faces,face_coords = facial_recognition(IMG_DIR+'/'+filename)
        #face locations coordinates are (top, right, bottom, left)
        analysis,face_locations = facial_analysis(face_coords,image_obj)
        if len(analysis)>0:
            emotions = [f['dominant_emotion'] for f in analysis]
            age = [f['age'] for f in analysis]
            gender = [f['gender'] for f in analysis]
            race = [f['dominant_race'] for f in analysis]
        else:
            emotions=age=gender=race=np.nan
            
        face_percent = facial_percentage(image_obj,face_coords)
        feature_df = feature_df.append({'videoId':filename[:-4],'numFaces':num_faces,'emotions':emotions,'age':age,
                                        'gender':gender,'race':race,'face_locations':face_locations,
                                        'face_percent':face_percent}, ignore_index=True)
    return feature_df
