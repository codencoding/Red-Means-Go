import numpy as np
from PIL import Image
import os
import pandas as pd
import face_recognition
from deepface import DeepFace

def facial_recognition(filename, cnn=True):
    """
    facial_recognition

    Identifies faces in an image

    Input : Filename
    Output : Image object, number of faces and list of face coordinates
    """
    #Load image from filename
    image = face_recognition.load_image_file(filename)
    if cnn:
        #Use CNN model if cnn is set to True
        face_locations = face_recognition.face_locations(image, model='cnn')
    else:
        # Use HOG model if cnn is set to True
        face_locations = face_recognition.face_locations(image)
    #Return image object, number of faces and list of face coordinates
    return image, len(face_locations), face_locations



def facial_analysis(face_locations, image, config='age, gender, race, emotion'):
    """
    facial_analysis

    Analyze faces using DeepFace according to config with options of Race, Age, Gender and Emotion

    Input : list of face coordinates, image object, configuration string
    Output : result of analysis for features specified in config options
    """
    #Skipped if no faces
    if len(face_locations) > 0:
        #Split up config string into list
        config = config.split(',')
        config = [c.strip() for c in config]
        results = []
        #Convert image object to PIL Image object
        im = Image.fromarray(image)
        #Go through each face, crop out the face from the image
        for f in face_locations:
            face = im.crop((f[3], f[0], f[1], f[2]))
            face = np.asarray(face)
        demography = DeepFace.analyze(face, config)
        return demography
    else:
        return []



def facial_percentage(face_locations, image):
    """
    facial_percentage

    Returns percent of image each face takes up

    Input : list of face coordinates, image object
    Output : list of facial percentage for each face
    """
    result = []
    #Get image resolution
    img_pixelcount = image.shape[0] * image.shape[1]
    for f in face_locations:
        #Count size of face section of image
        face_pixels = (f[2] - f[0]) * (f[1] - f[3])
        #Calculate the percentage of the face in the image
        result.append(face_pixels / img_pixelcount)
    return result



def create_feature_database(IMG_DIR):
    """
    create_feature_database

    For each image in the thumbnail, preprocess and analyze images then returns a dataframe containing facial features for
    images containing faces

    Input : directory of thumbnails
    Output : dataframe containing facial features for all faces containing a face
    """
    cols = ['videoId', 'numFaces', 'emotions', 'face_locations', 'face_percent']
    #Create empty dataframe
    feature_df = pd.DataFrame(columns=cols)
    for filename in os.listdir(IMG_DIR):
        #Analyze all images and calculate facial features for each image
        genders = []
        image_obj, num_faces, face_coords = facial_recognition(IMG_DIR + '/' + filename)
        #face locations coordinates are (top, right, bottom, left)
        analysis = facial_analysis(face_coords, image_obj)
        if len(analysis) > 0:
            emotions = [analysis[f]['dominant_emotion'] for f in analysis]
            age = [analysis[f]['age'] for f in analysis]
            gender = [analysis[f]['gender'] for f in analysis]
            race = [analysis[f]['dominant_race'] for f in analysis]
        else:
            emotions = age = gender = race = np.nan

        face_percent = facial_percentage(face_coords, image_obj)
        #Add facial features of image to dataframe
        feature_df = feature_df.append(
            {'videoId': filename[:-4], 'numFaces': num_faces, 'emotions': emotions, 'age': age,
             'gender': gender, 'race': race, 'face_locations': face_coords,
             'face_percent': face_percent}, ignore_index=True)
    return feature_df



def create_feature_data_batch(im_dir,video_ids):
    """
    create_feature_data_batch

    Similar function to create_feature_data however utilizing the batch version of functions used in the original function
    suited towards larger set of images

    Input : directory of thumbnails, list of video ids
    Output : dataframe containing facial features for all faces containing a face
    """
    cols = ['videoId', 'numFaces', 'emotions', 'age', 'gender', 'race', 'face_locations']
    #Create empty dataframe
    df = pd.DataFrame(columns=cols)
    #Initialize variables
    batch = 0 #Current batch size
    videoIds = []
    face_locations_batch = []
    faces_batch = []
    img_obj_batch = []
    img_objs = []
    files = [f + ".jpg" for f in video_ids if os.path.exists(im_dir+f+".jpg")]
    last_file = files[-1]
    num_batch = 0
    for filename in files:
        #Append image objects from files into lists until batch size of 50 or last file
        image = face_recognition.load_image_file(im_dir + '/' + filename)
        img_obj_batch.append(image)
        img_objs.append(image)
        videoIds.append(filename[:-4])
        batch += 1
        if batch == 50 or filename == last_file:
            num_batch += 1
            #Extract faces from all images in batch
            print("Batch {0} Facial Recognition Start!".format(num_batch))
            face_locations_batch += face_recognition.batch_face_locations(img_obj_batch,
                                                                          number_of_times_to_upsample=1,
                                                                          batch_size=batch)
            #Get index where no faces were detected in image
            empty_indices = [empty_ix for empty_ix, element in enumerate(face_locations_batch) if element == []]
            #Remove those entries from all our lists
            for index in sorted(empty_indices, reverse=True):
                del face_locations_batch[index]
                del videoIds[index]
                del img_objs[index]
            batch = 0
            img_obj_batch = []
            print("Batch {0} Facial Recognition Finished!".format(num_batch))
    print("Face Image Extraction Start!")
    #For each image, crop out all the faces and append to faces_batch
    for ix in range(len(face_locations_batch)):
        im = Image.fromarray(img_objs[ix])
        for f in face_locations_batch[ix]:
            face = im.crop((f[3], f[0], f[1], f[2]))
            face = np.asarray(face)
            faces_batch.append(face)
    print("Face Image Extraction Finished!")

    print("Facial Analysis Begin!")
    #Do analysis of all faces in faces_batch
    analysis_counter = 0
    """
    Note : On DSMLP servers and other computers when running DeepFace.analyze multiple times the model would get loaded 
    over and over causing memory issues so instead we do one large analysis job of all faces
    """
    analysis = DeepFace.analyze(faces_batch)
    print("Facial Analysis Finished!")
    #Append all features into the dataframe
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

