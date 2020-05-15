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


def facial_analysis(face_locations, image, config='age, gender, race, emotion'):
    if len(face_locations) > 0:
        config = config.split(',')
        config = [c.strip() for c in config]
        results = []
        im = Image.fromarray(image)
        for f in face_locations:
            face = im.crop((f[3], f[0], f[1], f[2]))
            face = np.asarray(face)
        demography = DeepFace.analyze(face, config)
        return demography
    else:
        return []


def facial_percentage(face_locations, image):
    result = []
    img_pixelcount = image.shape[0] * image.shape[1]
    for f in face_locations:
        face_pixels = (f[2] - f[0]) * (f[1] - f[3])
        result.append(face_pixels / img_pixelcount)
    return result


def create_feature_database(IMG_DIR):
    cols = ['videoId', 'numFaces', 'emotions', 'face_locations', 'face_percent']
    feature_df = pd.DataFrame(columns=cols)
    for filename in os.listdir(IMG_DIR):
        genders = []
        image_obj, num_faces, face_coords = facial_recognition(IMG_DIR + '/' + filename)
        # face locations coordinates are (top, right, bottom, left)
        analysis = facial_analysis(face_coords, image_obj)
        if len(analysis) > 0:
            emotions = [analysis[f]['dominant_emotion'] for f in analysis]
            age = [analysis[f]['age'] for f in analysis]
            gender = [analysis[f]['gender'] for f in analysis]
            race = [analysis[f]['dominant_race'] for f in analysis]
        else:
            emotions = age = gender = race = np.nan

        face_percent = facial_percentage(face_coords, image_obj)
        feature_df = feature_df.append(
            {'videoId': filename[:-4], 'numFaces': num_faces, 'emotions': emotions, 'age': age,
             'gender': gender, 'race': race, 'face_locations': face_coords,
             'face_percent': face_percent}, ignore_index=True)
    return feature_df


def create_feature_data_batch(im_dir):
    cols = ['videoId', 'numFaces', 'emotions', 'age', 'gender', 'race', 'face_locations']
    df = pd.DataFrame(columns=cols)
    batch = 0
    videoIds = []
    face_locations_batch = []
    faces_batch = []
    img_obj_batch = []
    img_objs = []
    last_file = os.listdir(im_dir)[-1]
    num_batch = 0
    for filename in os.listdir(im_dir):
        image = face_recognition.load_image_file(im_dir + '/' + filename)
        img_obj_batch.append(image)
        img_objs.append(image)
        videoIds.append(filename[:-4])
        batch += 1
        if batch == 50 or filename == last_file:
            num_batch += 1
            print("Batch {0} Facial Recognition Start!".format(num_batch))
            face_locations_batch += face_recognition.batch_face_locations(img_obj_batch,
                                                                          number_of_times_to_upsample=1,
                                                                          batch_size=batch)
            empty_indices = [empty_ix for empty_ix, element in enumerate(face_locations_batch) if element == []]
            for index in sorted(empty_indices, reverse=True):
                del face_locations_batch[index]
                del videoIds[index]
                del img_objs[index]
            batch = 0
            img_obj_batch = []
            print("Batch {0} Facial Recognition Finished!".format(num_batch))
    print("Face Image Extraction Start!")
    for ix in range(len(face_locations_batch)):
        im = Image.fromarray(img_objs[ix])
        for f in face_locations_batch[ix]:
            face = im.crop((f[3], f[0], f[1], f[2]))
            face = np.asarray(face)
            faces_batch.append(face)
    print("Face Image Extraction Finished!")

    print("Facial Analysis Begin!")
    analysis_counter = 0
    analysis = DeepFace.analyze(faces_batch)
    print("Facial Analysis Finished!")
    for i in range(len(face_locations_batch)):
        f = face_locations_batch[i]
        emotions = []
        age = []
        gender = []
        race = []
        for j in range(len(f)):
            analysis_counter += 1
            curr_analysis = analysis['instance_' + str(analysis_counter)]
            emotions.append(curr_analysis['dominant_emotion'])
            age.append(curr_analysis['age'])
            gender.append(curr_analysis['gender'])
            race.append(curr_analysis['dominant_race'])
        df = df.append({'videoId': videoIds[i], 'numFaces': len(f), 'emotions': emotions, 'age': age,
                        'gender': gender, 'race': race, 'face_locations': f}, ignore_index=True)

    return df