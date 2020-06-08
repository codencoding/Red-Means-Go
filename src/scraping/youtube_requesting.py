import os
import json
import pandas as pd
import time
from PIL import Image
import requests
from io import BytesIO
import numpy as np
from dateutil.parser import parse
from datetime import datetime
import dateutil.relativedelta

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


def full_run_search_result(youtube, q_term, num_search_results, videos_per_channel):
    # list of strings: 
    # returns the lists of video/parent channel ids from a search result with the given query term
    video_ids, parent_ids = iterate_search_results(youtube, q_term, num_search_results)
    
    # dictionary:
    # returns a dictionary where the keys are the parent channel ids
    # and the values are the video ids from the uploads playlist for that channel of length videos_per_channel
    channel_videos_dic = populate_channel_game_videos(youtube, q_term, parent_ids, videos_per_channel)
    print("------------------")
    print("unique channels gathered: ", len(channel_videos_dic.keys()))
    print("------------------")
    
    # list of dictionaries:
    # Each dictionary corresponds to a video_id from the recent playlist in the game topic channel
    # the number of dictionaries is equal to num_recent_videos.
    #
    # Each dictionary contains the video id, parent channel id, 
    # position in the YouTube game topic recent playlist, 
    # and list of videos from that channel on the speicified game.
    print("------------------")
    print("Aggregating Results...")
    res = generate_result_dics(video_ids, parent_ids, channel_videos_dic)
    print("Data Successfully scraped!")
    print("------------------")
    return res

def full_run_topic_channel(q_term, num_recent_videos, videos_per_channel):
    # string: 
    # Gets the id of the YouTube auto-generated topic channel for the q_term
    topic_id = request_topic_id(q_term + " topic")
    
    # string: 
    # Gets the playlist id of the recent playlist in the game topic channel
    topic_recent_playlist_id = request_recent_playlist_id(topic_id)
    
    # list of strings: 
    # returns the YouTube response object containing the specified amount of video_ids from the recent playlist
    video_ids = get_video_ids(topic_recent_playlist_id, num_recent_videos)
    
    # list of strings:
    # returns the parent channel of the videos in the game topic recent playlist
    parent_ids = get_parent_channels(video_ids)
    
    # dictionary:
    # returns a dictionary where the keys are the parent channel ids
    # and the values are the video ids from the uploads playlist for that channel of length videos_per_channel
    channel_videos_dic = populate_channel_game_videos(q_term, parent_ids, videos_per_channel)
    
    # list of dictionaries:
    # Each dictionary corresponds to a video_id from the recent playlist in the game topic channel
    # the number of dictionaries is equal to num_recent_videos.
    #
    # Each dictionary contains the video id, parent channel id, 
    # position in the YouTube game topic recent playlist, 
    # and list of videos from that channel on the speicified game.
    res = generate_result_dics(video_ids, parent_ids, channel_videos_dic)
    return res

def generate_dataset(q_term, num_recent_videos, videos_per_channel, write_path, 
                     api_service_name, api_version, api_key):
    # Driver Function: uses all other functions to generate the scraped dataset
    # setting up the API
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    # change this function to change how the dataset is generated
    # options are either search result, or topic channel
    res = full_run_search_result(youtube, q_term, num_recent_videos, videos_per_channel)
    date = time.strftime("%m_%d_%y",time.localtime())
    fname = "scrape_" + date + ".json"
    fname = save_to_json(res, date, write_path, fname)
    return write_path + fname


def generate_result_dics(videos, parents, channel_videos):
    """Create a dictionary for video search results"""
    all_results = []
    for i in range(len(videos)):
        out_dic = {"video_id": videos[i],
                   "position": i,
                   "channel_id": parents[i],
                   "channel_videos": channel_videos[parents[i]]}
        all_results.append(out_dic)
    return all_results


def get_channel_game_videos(youtube, game, parent, num_vids):
    """Get all the videos from a channel related to the given game parameter."""
    request = youtube.channels().list(
        part="snippet,contentDetails",
        id=parent,
        )
    response = request.execute()
    
    game_vids = []
    if num_vids < 50:
        max_results = num_vids
    else:
        max_results = 50
       
    # initial first page result
    uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    uploads_details = request_playlist_videos(youtube, uploads_id, max_results) 
    for vid_data in uploads_details['items']:
        game_vids.append(vid_data['snippet']['resourceId']['videoId'])
        if len(game_vids) == num_vids:
            break  
            
    # if first page doesn't provide enough videos specified by num_vids, this iterates the pages
    # until the length of game_vids matches num_vids
    try:
        
        next_token = uploads_details['nextPageToken']
        while len(game_vids) < num_vids:
            cur_page = request_playlist_videos(uploads_id, max_results, next_token)
            for vid_data in cur_page['items']:
                game_vids.append(vid_data['snippet']['resourceId']['videoId'])
                if len(game_vids) == num_vids:
                    break 
            if 'nextPageToken' in cur_page.keys():
                next_token = cur_page['nextPageToken']
            else:
                print("No additional pages")
                break
            time.sleep(3) # trying to not overload the api
    except Exception as e:
        print("Error:",e)
        print("Channel Title:",uploads_details['items'][0]['snippet']['channelTitle'])
        print("continuing...")
    return game_vids


def get_parent_channels(video_ids):
    """Get a list of channel videos that correspond to the given video ids."""
    parent_channel_ids = []
    for vid_id in video_ids:
        vid_content = request_sparse_video_details(vid_id)
        parent_channel = vid_content['items'][0]['snippet']['channelId']
        parent_channel_ids.append(parent_channel)
        
    return parent_channel_ids


def get_video_ids(playlist_id, num_vids):
    """Get the video ids of each video in the given playlist from playlist_id."""
    recent_video_ids = []
    max_results = 50
    if num_vids < max_results:
        playlist_details = request_playlist_videos(playlist_id, num_vids)
    else:
        playlist_details = request_playlist_videos(playlist_id, max_results)
        
    for vid_data in playlist_details['items']:
        recent_video_ids.append(vid_data['snippet']['resourceId']['videoId'])
        if len(recent_video_ids) == num_vids:
            break         
    
    # extends recent video ids if the num_vids was larger than the initial page's results
    next_token = playlist_details['nextPageToken']
    while len(recent_video_ids) < num_vids:
        cur_page = request_playlist_videos(playlist_id, max_results, next_token)
        for vid_data in cur_page['items']:
            recent_video_ids.append(vid_data['snippet']['resourceId']['videoId'])
            if len(recent_video_ids) == num_vids:
                break
        next_token = cur_page['nextPageToken']
        time.sleep(3)
    return recent_video_ids


def get_vid_stats(vid):
    """Get basic video statistics from a video object."""
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


def iterate_search_results(youtube, q_term, num_results):
    """Retrieve the full iterations of YouTube search pages until num_results videos are acquired."""
    print("------------------")
    print("Starting iteration of search results...")
    video_ids = []
    parent_ids = []
    max_results = 50
    
    if num_results < 50:
        max_results = num_results
        
    init_search = search_result(youtube, q_term, max_results)
    for vid_data in init_search['items']:
        video_ids.append(vid_data['id']['videoId'])
        parent_ids.append(vid_data['snippet']['channelId'])
        if len(video_ids) == num_results:
            break
    print("Current results retrieved:", len(video_ids), 100*len(video_ids)/num_results, "%")
    try:
        next_token = init_search['nextPageToken']
        while len(video_ids) < num_results:
            cur_page = search_result(youtube, q_term, max_results, next_token)
            for vid_data in cur_page['items']:
                video_ids.append(vid_data['id']['videoId'])
                parent_ids.append(vid_data['snippet']['channelId'])
                if len(video_ids) == num_results:
                    break
            next_token = cur_page['nextPageToken']
            print("Current results retrieved:", len(video_ids), 100*len(video_ids)/num_results, "%")
    except:
        print("No new pages. Returning current video ids and parent ids")
    print("Done iterating search results!")
    print("------------------")
    return video_ids, parent_ids


def populate_channel_game_videos(youtube, game, parents, num_vids):
    """Retrieve relevant gaming videos for all distinct channels."""
    print("------------------")
    print("Starting retrieval of channel videos for", len(parents), "channels...")
    channel_videos = {}
    counter = 0
    for par_chan in parents:
        if counter % 5 == 0:
            print("Channels completed: " + str(counter), 100*counter/len(parents), "%")
        if par_chan not in channel_videos.keys():
            channel_videos[par_chan] = get_channel_game_videos(youtube, game, par_chan, num_vids)
            counter += 1
        else:
            counter += 1
    print("Done Retrieving Channel Videos!")
    print("------------------")
    return channel_videos

def request_playlist_videos(youtube, playlist_id, num_results, page_token=None):
    """Request all the videos from a playlist_id using YouTube's api."""
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
    """Request the recent videos playlist corresponding to a given game topic."""
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
    """Retrieve sparse video data from a video_id."""
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
    """Find a channel topic id given a query term."""
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
    """Get video details from a video id; API cost of 7"""
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    # note that this uses youtube.videos instead of youtube.search
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()
    return response


def save_to_json(data, date, dir_path, fname, overwrite=False):  
    """Save retrieved data to a json in dir_path."""
    out_dic = {"date_scraped": date,
               "data": data
              }
    if os.path.exists(dir_path + fname) and not overwrite:
        cur_dir = os.listdir(dir_path)
        fname_split = fname.split(".")
        num_dupes = len([f for f in cur_dir if fname_split[0] in f])
        fname = fname_split[0] + "(" + str(num_dupes) + ")." + fname_split[1]
    if os.path.isdir(dir_path):
        with open(dir_path + fname, 'w') as outfile:
            json.dump(out_dic, outfile)
    else:
        os.makedirs(dir_path)
        with open(dir_path + fname, 'w') as outfile:
            json.dump(out_dic, outfile) 
    return fname
            
def search_result(youtube, q_term, max_results, page_token=None):
    """Return a list of videos the correspond to the given query term."""
    d = datetime.now()
    prev_month = d - dateutil.relativedelta.relativedelta(months=1)
    prev_month_rfc = prev_month.isoformat('T') + "Z"
    time.sleep(3)
    if page_token:
        request = youtube.search().list(
            part="snippet",
            q=q_term,
            maxResults=max_results,
            pageToken=page_token,
            type="video",
            order="relevance",
            publishedAfter=prev_month_rfc
            )
    else:
        request = youtube.search().list(
                part="snippet",
                q=q_term,
                maxResults=max_results,
                type="video",
                order="relevance",
                publishedAfter=prev_month_rfc
                )
    response = request.execute()
    return response
