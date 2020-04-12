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


def generate_dataset(q_term, num_channels, videos_per_channel):
    topic_id = request_topic_id(q_term + " topic")
    topic_recent_playlist_id = request_recent_playlist_id(topic_id)
    recent_playlist_details = request_playlist_videos(topic_recent_playlist_id,5)
    video_ids = get_video_ids(topic_recent_playlist_id, recent_playlist_details, num_channels)
    parent_ids = get_parent_channels(video_ids)
    channel_videos_dic = populate_channel_game_videos(q_term, parent_ids)
    res = generate_result_dics(video_ids, parent_ids, channel_videos_dic)
    return res


def generate_result_dics(videos, parents, channel_videos):
    all_results = []
    for i in range(len(parents)):
        out_dic = {"video_id": videos[i],
                   "position": i,
                   "channel_id": parents[i],
                   "channel_videos": channel_videos[parents[i]]}
        all_results.append(out_dic)
    return all_results


def get_channel_game_videos(game, parent):
    request = youtube.channels().list(
        part="snippet,contentDetails",
        id=parent,
        )
    response = request.execute()
    uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    uploads_details = request_playlist_videos(uploads_id, 50)
    game_vids = []
    for vid_data in uploads_details['items']:
        vid_title = vid_data['snippet']['title'].lower()
        vid_desc = vid_data['snippet']['description'].lower()
        if game in vid_title or game in vid_desc:
            game_vids.append(vid_data['snippet']['resourceId']['videoId'])
    return game_vids


def get_parent_channels(video_ids):
    parent_channel_ids = []
    for vid_id in video_ids:
        vid_content = request_sparse_video_details(vid_id)
        parent_channel = vid_content['items'][0]['snippet']['channelId']
        parent_channel_ids.append(parent_channel)
    return parent_channel_ids


def get_video_ids(playlist_id, playlist_details, num_vids):
    recent_video_ids = []
    for vid_data in playlist_details['items']:
        recent_video_ids.append(vid_data['snippet']['resourceId']['videoId'])
        if len(recent_video_ids) == num_vids:
            break
    next_token = playlist_details['nextPageToken']
    cur_page = request_playlist_videos(playlist_id, 5, next_token)
    while len(recent_video_ids) < num_vids:
        cur_page = request_playlist_videos(playlist_id, 5, next_token)
        for vid_data in cur_page['items']:
            recent_video_ids.append(vid_data['snippet']['resourceId']['videoId'])
            if len(recent_video_ids) == num_vids:
                break
        next_token = cur_page['nextPageToken']
    return recent_video_ids


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


def populate_channel_game_videos(game, parents):
    channel_videos = {}
    for par_chan in parents:
        if par_chan not in channel_videos.keys():
            channel_videos[par_chan] = get_channel_game_videos(game, par_chan)
        else:
            continue
    return channel_videos


def request_playlist_videos(playlist_id, num_results, page_token=None):
    if page_token:
        request = youtube.playlistItems().list(
            part="snippet",
            maxResults=num_results,
            playlistId=playlist_id,
            pageToken=page_token
        )
    else:
        request = youtube.playlistItems().list(
                part="snippet",
                maxResults=num_results,
                playlistId=playlist_id,
            )
    response = request.execute()
    return response


def request_recent_playlist_id(game_topic_channel):
    request = youtube.channelSections().list(
        part="snippet,contentDetails",
        channelId=game_topic_channel,
        )
    response = request.execute()
    recent_playlist = None
    for section in response['items']:
        try: 
            if section['snippet']['localized']['title'] == "Recent Videos":
                recent_playlist = section['contentDetails']['playlists'][0]
            else:
                continue
        except:
            continue
    return recent_playlist


def request_sparse_video_details(video_id):
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    # note that this uses youtube.videos instead of youtube.search
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    return response 


def request_topic_id(q_term): 
    request = youtube.search().list(
            part="snippet",
            q=q_term,
            maxResults="1",
            type="channel",
            order="relevance"
            )
    response = request.execute()
    game_topic_channel = response['items'][0]['snippet']['channelId']
    return game_topic_channel


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




