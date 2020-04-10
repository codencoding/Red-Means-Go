import os
import json
import pandas as pd
import time
from PIL import Image
import requests
from io import BytesIO
import numpy as np
from dateutil.parser import parse

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

def request_channels(q_term, num_results,order_type):
    # all arguments must be strings, returns json object with list of channels
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    
    # Search parameters
    request = youtube.search().list(
        part="snippet",
        q=q_term,
        maxResults=num_results,
        type="channel",
        order=order_type
    )
    response = request.execute()

    return response

def request_channel_videos(channel_id, num_results, order_type, page_token):
    # all arguments must be strings, returns json object with list of videos from the given channel
    
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    if page_token:
        request = youtube.search().list(
            part="snippet",
            maxResults=num_results,
            type="video",
            channelId=channel_id,
            order=order_type,
            pageToken=page_token
        )
    else:
        request = youtube.search().list(
            part="snippet",
            maxResults=num_results,
            type="video",
            channelId=channel_id,
            order=order_type
        )
    response = request.execute()
    return response

def request_video_details(video_id, api_key, api_service_name, api_version):
    """API cost of 7"""
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    # note that this uses youtube.videos instead of youtube.search
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()
    return response

def get_vid_stats(vid):
    channel_id = vid['snippet']['channelId']
    channel_title = vid['snippet']['channelTitle']
    try:
        thumbnail_link = vid['snippet']['thumbnails']['maxres']['url']
    except:
        thumbnail_link = vid['snippet']['thumbnails']['high']['url']
    title = vid['snippet']['title']
    date = vid['snippet']['publishedAt']
    views = vid['statistics']['viewCount']
    likes = vid['statistics']['likeCount']
    dislikes = vid['statistics']['dislikeCount']
    comments = vid['statistics']['commentCount']
    stats = {"channel_id":channel_id,
             "channel_title":channel_title,
             "thumbnail_link":thumbnail_link,
             "title":title,
             "date":parse(date),
             "views":int(views),
             "likes":int(likes),
             "dislikes":int(dislikes),
             "comments":int(comments)}
    return stats

# full pipeline for scraping and generating dataframe
def main_pipeline():
    metadata = []
    # get initial search results (usually going to be a list of channels)
    out = request_channels("gaming","5","relevance")
    data = out['items']
    # get channel ids from search results
    channel_ids = []
    for channel in data:
        cur_channel_id = channel['snippet']['channelId']
        channel_ids.append(cur_channel_id)
        # get channel videos from the current channel id (we can also choose to handpick channels / videos)
        videos = request_channel_videos(cur_channel_id,"5","date",None)
        video_ids = []
        for video in videos['items']:
            cur_id = video['id']['videoId']
            video_ids.append(cur_id)
            # use youtube videos api to get metadata about a single video, by video id
            cur_vid = request_video_details(cur_id)['items'][0]
            row = get_vid_stats(cur_vid)
            metadata.append(row)
        time.sleep(1)

    # create a dataframe from the gathered metadata
    columns = ['channelId','channelTitle','thumbnailLink',
               'videoTitle','Date','Views',
               'Likes','Dislikes','Comments']
    df = pd.DataFrame(metadata,columns=columns)
    return df

def get_channel_id(q_term):
    # rough channel conversion function (may not work all the time)
    
    init_search = request_channels(q_term,"1","relevance")
    chan_id = init_search['items'][0]['snippet']['channelId']
    return chan_id

def generate_video_data(video_list):
    # generates video data for each video in given list and returns a formatted df of video statistics
    channel_data = []
    for vid in video_list['items']:
        cur_id = vid['id']['videoId']
        cur_vid = request_video_details(cur_id)['items'][0]
        row = get_vid_stats(cur_vid)
        channel_data.append(row)
    columns = ['channelId','channelTitle','thumbnailLink',
               'videoTitle','Date','Views',
               'Likes','Dislikes','Comments']
    df = pd.DataFrame(channel_data,columns=columns)
    df['Views'] = df['Views'].astype(int)
    df['Likes'] = df['Likes'].astype(int)
    df['Dislikes'] = df['Dislikes'].astype(int)
    df['Comments'] = df['Comments'].astype(int)
    return df

def generate_thumbnails(thumbnail_list):
    # just makes a request call to the thumbnail link
    imgs = []
    for link in thumbnail_list:
        response = requests.get(link)
        img = Image.open(BytesIO(response.content))
        imgs.append(img)
    return imgs

def evaluate_videos(df):
    # evaulated based on z score of views and likes currently, very rough approx
    avg_views = df['Views'].mean()
    avg_likes = df['Likes'].mean()
    avg_dislikes = df['Dislikes'].mean()
    avg_comments = df['Comments'].mean()
    
    std_views = np.std(df['Views'])
    std_likes = np.std(df['Likes'])
    std_dislikes = np.std(df['Dislikes'])
    std_comments = np.std(df['Comments'])
    
    z_views = df['Views'].apply(lambda x: (x - avg_views) / std_views)
    z_likes = df['Likes'].apply(lambda x: (x - avg_likes) / std_likes)
    z_dislikes = df['Dislikes'].apply(lambda x: (x - avg_dislikes) / std_dislikes)
    z_comments = df['Comments'].apply(lambda x: (x - avg_comments) / std_comments)
    
    good_videos = []
    bad_videos = []
    for i in range(len(df)):
        if z_views[i] > .3 and z_likes[i] > .3:
            good_videos.append(i)
        if z_views[i] < -.5 and z_likes[i] < -.5:
            bad_videos.append(i)

    return good_videos, bad_videos

def analyze_channel(keyword):
    channel_id = get_channel_id(keyword)
    channel_videos = request_channel_videos(channel_id, "30", "date", None)
    video_data_df = generate_video_data(channel_videos)
    video_thumbnails = generate_thumbnails(video_data_df['thumbnailLink'].values)
    good_videos, bad_videos = evaluate_videos(video_data_df)
    return good_videos, bad_videos