import os
import sys
import json
import pandas as pd
import requests

sys.path.insert(0, os.path.abspath('../../src/scraping'))
import youtube_requesting as ytr


def fetch_raw_data(ROOT_DIR, cfg):
    data = {}
    fp = ROOT_DIR + cfg["videos-dir"] + cfg["selected-game"] + '/'
    for fname in os.listdir(fp):
        if fname.endswith(".json"):
            with open(fp + fname) as f:
                read_data = json.load(f)
            data[read_data["date_scraped"]] = read_data["data"]
            
    return data

def get_vid_metadata(vid_data, api_key):
    api_service_name = "youtube"
    api_version = "v3"
    
    vid_id = vid_data["video_id"]
    vid_pos = vid_data["position"]
    
    mdata = ytr.request_video_details(vid_id, api_key, api_service_name, api_version)['items'][0]
    out = mdata["statistics"]
    
    unwanted_keys = ['liveBroadcastContent', 'localized', 'defaultAudioLanguage']
    for key in unwanted_keys:
        if key in mdata["snippet"]:
            mdata["snippet"].pop(key)
    
    out.update(mdata["snippet"])
    out["video_id"] = vid_id
    out["position"] = vid_pos
    return pd.Series(out)


def make_mdata_df(data, api_key):
    metadata = []

    for vid in data:
        temp_dict = {
            "video_id":vid["video_id"],
            "position":vid["position"]
        }
        metadata.append(temp_dict)
    
    df = pd.DataFrame(metadata).apply(get_vid_metadata, api_key=api_key, axis=1)
    
    return df

def download_vid_thumb(video_id, df, save_dir, res="default"):
    dict_val = df[df.video_id == video_id]["thumbnails"].iloc[0]
    if isinstance(dict_val, str):
        url = eval(dict_val)[res]["url"]
    else:
        url = dict_val[res]["url"]
    with open(save_dir + video_id + ".jpg", 'wb') as f:
        f.write(requests.get(url).content)
        
def download_df_thumbs(df, save_dir, res="default"):
    save_dir += res + '/'
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    
    for v_id in df.video_id:
        download_vid_thumb(v_id, df, save_dir, res)
        
