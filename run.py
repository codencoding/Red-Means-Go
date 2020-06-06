ROOT_DIR = "./"
import os
import sys
import json
import pandas as pd
import datetime

sys.path.insert(0, os.path.abspath(ROOT_DIR + 'src/scraping'))
import youtube_requesting as ytr
import metadata as mdata

sys.path.insert(0, os.path.abspath(ROOT_DIR + "src/modeling"))
import facialFeatures as face
import basic_stats as basic

with open(ROOT_DIR + "config/" + "config-scraping.json") as f:
    cfg = json.load(f)

# read in command line arguments
args = sys.argv

# declare global vars from cfg json and credentials json
game_title = cfg['selected-game']
videos_dir = cfg['videos-dir'].format(game_title)
cur_date = datetime.datetime.now().strftime('_%m_%d_%y')
full_feature_write_name = cfg['full-features-write-name'].format(game_title,cur_date)
overwrite = cfg['overwrite']

# this prevents accidentally overwriting previously scraped data
if (overwrite == "false") and os.path.exists(ROOT_DIR + videos_dir + full_feature_write_name):
    vid_dir = os.listdir(videos_dir)
    num_dupes = len([f for f in vid_dir if full_feature_write_name.split(".")[0] in f])
    split_feature_name = full_feature_write_name.split(".")
    full_feature_write_name = split_feature_name[0] + "(" + str(num_dupes) + ")." + split_feature_name[1]


if not os.path.exists(videos_dir):
    os.makedirs(videos_dir)

if "test-project" in args:
    print("Running on Test Data.")
    
    # init test arguments / file paths   
    out_fp = cfg['test-metadata-csv-read-path'].format(game_title,game_title)
    thumbnails_dir = ROOT_DIR + cfg['test-thumbs-dir'].format(game_title)
    
    # youtube data already present in test directory, no need to download
    df = pd.read_csv(out_fp)
    print("Metadata Read Successfully!")
else:
    print("FULL RUN")
    # init api credentials for scraping
    with open(ROOT_DIR + "api_key.json") as f:
        credentials = json.load(f)
    api_keys = credentials['api_keys']
    
    # init default arguments / file paths    
    api_service_name = cfg['api-service-name']
    api_version = cfg['api-version']
    out_fp = cfg['summary-metadata-csv-write-path'].format(game_title,game_title,cur_date)
    full_out_fp = cfg['full-metadata-csv-write-path'].format(game_title,game_title,cur_date)
    thumbnails_dir = ROOT_DIR + cfg['thumbnails-dir'].format(game_title)
    num_recent_videos = cfg['num-recent-videos']
    videos_per_channel = cfg['videos-per-channel']
    scrape_write_dir = cfg['scrape-write-dir'].format(game_title)
    master_dic_write_fp = cfg['requests-dic-write-path'].format(game_title, game_title)
    master_dic_fp = cfg['requests-dic-read-path'].format(game_title, game_title)
    
    # downloads youtube data and returns filepath of the downloaded data
    scrape_data_fp = ytr.generate_dataset(game_title, num_recent_videos, videos_per_channel, scrape_write_dir, 
                                          api_service_name, api_version, api_keys[0])

    # get metadata
    df, sum_df = mdata.metadata_main(api_keys, api_service_name, api_version, 
                  out_fp, master_dic_write_fp, scrape_data_fp, 
                  game_title, master_dic_fp,full_out_fp)


# download thumbnails
# dataframe required at ROOT_DIR + cfg["thumbnails-dir"].format(cfg["selected-game"])
for qual in cfg["thumbnail-qual"]:
    if cfg["thumbnail-qual"][qual]:
        mdata.download_df_thumbs(df, thumbnails_dir, res=qual)

# do feature extraction
thumbnail_list = df['videoId'].values
basic_stats_df = basic.basic_image_stats(thumbnails_dir,thumbnail_list)
advanced_stats_df = face.create_feature_data_batch(thumbnails_dir,thumbnail_list)

# combine feature extraction into a csv. Go to notebooks/eda for futher analysis of data
all_image_stats_df = basic_stats_df.merge(advanced_stats_df,how="left",on="videoId")
master_df = df.merge(all_image_stats_df,how="left",on="videoId")
master_df.to_csv(ROOT_DIR + videos_dir + full_feature_write_name,index=False)