import pandas as pd
import json
import os
import json
import pandas as pd
import time
from PIL import Image
import requests
from io import BytesIO
import numpy as np
from datetime import datetime
import dateutil.relativedelta
from dateutil.parser import parse
from scipy import stats
import ast
import sys

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


def channel_video_success(row, weights=None):
    """Get sum of z-scores as a success metric."""
    metric_cols = ["z_comments", "z_dislikes",
                   "z_likes", "z_views"]
    if weights is None:
        weights = [1 for _ in metric_cols]
    
    scores = [row[key] for key in metric_cols]
    return sum(scores)


def check_vid_game(vid_stats, game_title):
    """Confirm a video is about a given game_title."""
    game_title = game_title.lower()
    try:
        tags = vid_stats['tags']
    except:
        tags = []
    try:
        title = vid_stats['title'].lower()
    except:
        title = np.nan
    try:
        description = vid_stats['description'].lower()
    except:
        description = np.nan
    if type(tags) == float:
        tags = []
    if type(title) == float:
        title = ""
    if type(description) == float:
        description = "" 
    if game_title in title or game_title in description:
        return True
    else:
        for tag in tags:
            if game_title in tag.lower():
                return True
    return False


def download_vid_thumb(video_id, df, save_dir, res):
    """Download the video thumbnail from a given video_id."""
    dict_val = df[df.videoId == video_id]["thumbnails"].iloc[0]
    if pd.isnull(dict_val):
        return
    if isinstance(dict_val, str):
        url = eval(dict_val)[res]["url"]
    else:
        url = dict_val[res]["url"]
    with open(save_dir + video_id + ".jpg", 'wb') as f:
        f.write(requests.get(url).content)
        
def download_df_thumbs(df, save_dir, res):
    """Download all video thumbnails from a given dataframe and output to save_dir."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    num_thumbnails = len(df['videoId'])
    count = 0
    for v_id in df["videoId"]:
        if count % 25 == 0:
            print("Thumbnail Download:", count, "of", num_thumbnails)
        count += 1
        if os.path.exists(save_dir + v_id + ".jpg"):
            continue
        else:
            download_vid_thumb(v_id, df, save_dir, res)
    print("Thumbnails Successfully Downloaded!")
        
        
def generate_metadata(master_dic, data, game_title, api_keys, api_service_name, api_version):
    """Generate a statistic metadata csv based on retrieve YouTube video data."""
    all_metadata = pd.DataFrame()
    progress_count = 0
    api_idx = 0
    for par_data in data['data']:
        if progress_count % 25 == 0:
            print("Metadata Progress:",progress_count,"of",len(data['data'])," Parent Channels")
        channel_game_vids = []
        for channel_vid in par_data['channel_videos']:
            if channel_vid in master_dic.keys():
                cur_vid_details = master_dic[channel_vid]
                cur_vid_stats = get_vid_stats(cur_vid_details)
                if check_vid_game(cur_vid_stats, game_title):
                    channel_game_vids.append(cur_vid_stats)
            else:
                # TODO: Handle missing / incorrect API key
                try:
                    api_key = api_keys[api_idx]
                    api_idx += 1
                    if api_idx == len(api_keys):
                        api_idx = 0
                    cur_vid_details = request_video_details(channel_vid,
                                                            api_key,
                                                            api_service_name,
                                                            api_version)
                    if len(cur_vid_details['items']) == 0:
                        cur_vid_details = {}
                    else:
                        cur_vid_details = cur_vid_details['items'][0]
                    master_dic[channel_vid] = cur_vid_details
                    cur_vid_stats = get_vid_stats(cur_vid_details)
                    if check_vid_game(cur_vid_stats, game_title):
                        channel_game_vids.append(cur_vid_stats)
                except:
                    print("Video was not in local storage and there was a problem scraping:")
                    print(sys.exc_info()[0])
                    raise
        cur_metadata = pd.DataFrame(channel_game_vids)
        cur_metadata['tags'] = cur_metadata['tags'].apply(lambda x: str(x))
        cur_metadata['thumbnails'] = cur_metadata['thumbnails'].apply(lambda x: str(x))
        cur_metadata['z_views'] = stats.zscore(cur_metadata['viewCount'])
        cur_metadata['z_likes'] = stats.zscore(cur_metadata['likeCount'])
        cur_metadata['z_dislikes'] = stats.zscore(cur_metadata['dislikeCount'])
        cur_metadata['z_comments'] = stats.zscore(cur_metadata['commentCount'])
        all_metadata = pd.concat([all_metadata,cur_metadata],sort=True).reset_index(drop=True)
        progress_count += 1
    unique_metadata = all_metadata.drop_duplicates().reset_index(drop=True)

    return unique_metadata


def generate_search_result_df(unique_metadata,data):
    """Create a dataframe based off of the retrieved data in data."""
    out_data = []
    for par_data in data['data']:
        if par_data['video_id'] in unique_metadata['videoId'].values:
            vid_stats = unique_metadata[unique_metadata['videoId'] == par_data['video_id']].iloc[0]
            vid_stats['position'] = par_data['position']
            out_data.append(vid_stats)
        else:
            all_nans = unique_metadata.iloc[0].apply(lambda x: np.nan)
            all_nans['videoId'] = par_data['video_id']
            all_nans['position'] = par_data['position']
            out_data.append(all_nans)
    out_df = pd.DataFrame(out_data).reset_index(drop=True)
    return out_df
        
        
def get_success_metrics(df):
    """Create success columns for a given df."""
    df["global_success"] = df.apply(global_video_success, axis=1)
    df["global_success"] = zscore(df["global_success"], nan_policy="omit")
    df["channel_success"] = df.apply(channel_video_success, axis=1)
    
    return df


def get_vid_stats(vid):
    """Get basic video statistics."""
    try:
        vid_id = vid['id']
    except:
        vid_id = np.nan
    try:
        channel_id = vid['snippet']['channelId']
    except:
        channel_id = np.nan
    try:
        channel_title = vid['snippet']['channelTitle']
    except:
        channel_title = np.nan
    try:
        thumbnail_links = vid['snippet']['thumbnails']
    except:
        thumbnail_links = np.nan
    try:
        title = vid['snippet']['title']
    except:
        title = np.nan
    try:
        language = vid['snippet']['defaultAudioLanguage']
    except:
        language = np.nan
    try:
        date = parse(vid['snippet']['publishedAt'])
    except:
        date = np.nan
    try:
        duration = vid['contentDetails']['duration']
    except:
        duration = np.nan
    try:
        views = vid['statistics']['viewCount']
    except:
        views = np.nan
    try:
        likes = vid['statistics']['likeCount']
    except:
        likes = np.nan
    try:
        dislikes = vid['statistics']['dislikeCount']
    except:
        dislikes = np.nan
    try:
        comments = vid['statistics']['commentCount']
    except:
        comments = np.nan
    try:
        favorites = vid['statistics']['favoriteCount']
    except:
        favorites = np.nan
    try:
        description = vid['snippet']['description']
    except:
        description = np.nan
    try:
        tags = vid['snippet']['tags']
    except:
        tags = np.nan
    try:
        cat_id = vid['snippet']['categoryId']
    except:
        cat_id = np.nan
    stats = {"videoId": vid_id,
             "channelId":channel_id,
             "channelTitle":channel_title,
             "thumbnails":thumbnail_links,
             "title":title,
             "date":date,
             "duration": duration,
             "viewCount":float(views),
             "likeCount":float(likes),
             "dislikeCount":float(dislikes),
             "commentCount":float(comments),
             "favoriteCount":float(favorites),
             "tags":tags,
             "defaultLanguage":language,
             "categoryId":float(cat_id),
             "description": description}
    return stats

        
def global_video_success(row, weights=None):
    """Create a video success measurement based on basic video stats."""
    metric_cols = ["commentCount", "dislikeCount", "favoriteCount",
                   "likeCount", "viewCount"]
    if weights is None:
        weights = [1 for _ in metric_cols]
    weights[1] = -1
    
    scores = [row[key] for key in metric_cols]
    return sum(scores)


def init_master_dic(dic_fp):
    """Create a master dictionary for holding video data from a YouTube json request output file."""
    if dic_fp == '':
        return {}
    elif not os.path.exists(dic_fp):
        print("Requests Dictionary path does not exist.")
        print("If you do not have a local requests dic, pass '' in the config file for the key: 'requests-dic-read-path'")
        raise ValueError
    with open(dic_fp) as json_file:
        out_dic = json.load(json_file)
    return out_dic
    
    
def metadata_main(api_keys, api_service_name, api_version,
                  out_fp, master_dic_write_fp, 
                  init_data_fp, game_title, master_dic_fp, full_out_fp):
    # driver function 
    
    # loads cached data if any is present
    master_dic = init_master_dic(master_dic_fp)
    with open(init_data_fp) as json_file:
        data = json.load(json_file)
        
    # generates metadata for entire dataset
    all_metadata = generate_metadata(master_dic, data, game_title, api_keys, api_service_name, api_version)
    
    # saves request data to local memory
    if len(master_dic.keys()) > 0:
        save_requests_dic(master_dic_write_fp, master_dic)
    
    # generates metadata only for search results
    out_df = generate_search_result_df(all_metadata, data)
    all_metadata.to_csv(full_out_fp,index=False)
    out_df.to_csv(out_fp,index=False)
    print("Summary Metadata Saved at: " + out_fp)
    return all_metadata, out_df

def request_video_details(video_id, api_key, api_service_name, api_version):
    """Get video details from a video id; has an API cost of 7"""
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)
    # note that this uses youtube.videos instead of youtube.search
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    )
    response = request.execute()
    return response

def save_requests_dic(fp, data):
    """Create a requests json from used api requests."""
    with open(fp,"w") as json_file:
        json.dump(data, json_file)
    print("API Requests logged locally at: " + fp)
