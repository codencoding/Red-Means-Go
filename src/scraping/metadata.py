import os
import sys
import json
import pandas as pd
import requests

sys.path.insert(0, os.path.abspath('../../src/scraping'))
import youtube_requesting as ytr


def fetch_raw_data(fp, cfg):
    data = {}
#     fp = ROOT_DIR + cfg["videos-dir"] + cfg["selected-game"] + '/'
    for fname in os.listdir(fp):
        if fname.endswith(".json"):
            with open(fp + fname) as f:
                read_data = json.load(f)
            data[read_data["date_scraped"]] = read_data["data"]
            
    return data

def get_vid_metadata(vid_data, api_key, mdata):
#     api_service_name = "youtube"
#     api_version = "v3"
    unwanted_keys = ['liveBroadcastContent', 'localized', 'defaultAudioLanguage']
    
    vid_id = vid_data["video_id"]
    
#     mdata = ytr.request_video_details(vid_id, api_key, api_service_name, api_version)['items']
    out = mdata["statistics"]
    
    for key in unwanted_keys:
        if key in mdata["snippet"]:
            mdata["snippet"].pop(key)
    
    out.update(mdata["snippet"])
    out.update(vid_data)
    
    return out


def request_data(vid_id, api_key):
    api_service_name = "youtube"
    api_version = "v3"
    
    mdata = ytr.request_video_details(vid_id, api_key, api_service_name, api_version)['items']
    if len(mdata) == 0:
        return None
    
    return mdata[0]


def make_mdata_df(data, api_key):
    metadata = []

    for vid in data:
        temp_dict = {
            "video_id":vid["video_id"],
            "position":vid["position"],
            "channel_videos":vid["channel_videos"]
        }
        mdata = request_data(vid["video_id"], api_key)
        if mdata is None:
            continue
        mdata = get_vid_metadata(vid, api_key, mdata)
        temp_dict.update(mdata)
        
        metadata.append(temp_dict)
    
    return pd.DataFrame(metadata)

def download_vid_thumb(video_id, df, save_dir, res):
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
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    
    for v_id in df["videoId"]:
        download_vid_thumb(v_id, df, save_dir, res)
        
