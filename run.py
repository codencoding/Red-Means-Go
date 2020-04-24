ROOT_DIR = "./"
import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.abspath(ROOT_DIR + 'src/scraping'))
import youtube_requesting as ytr
import metadata as mdata

with open(ROOT_DIR + "config/" + "config-scraping.json") as f:
    cfg = json.load(f)

with open(ROOT_DIR + "api_key.json") as f:
    credentials = json.load(f)

# read in command line arguments
args = sys.argv


# declare global vars from cfg json and credentials json
api_keys = credentials['api_keys']
api_service_name = cfg['api-service-name']
api_version = cfg['api-version']
game_title = cfg['selected-game']
master_dic_write_fp = cfg['requests-dic-write-path'].format(game_title, game_title)
master_dic_fp = cfg['requests-dic-read-path'].format(game_title, game_title)

if "test" in args:
    out_fp = cfg['test-metadata-csv-write-path'].format(game_title,game_title)
    init_data_fp = cfg['test-scrape-results'].format(game_title)
    thumbnails_dir = ROOT_DIR + cfg['test-thumbs-dir'].format(game_title)
else:
    out_fp = cfg['metadata-csv-write-path'].format(game_title,game_title)
    init_data_fp = cfg['test-scrape-results'].format(game_title)
    thumbnails_dir = ROOT_DIR + cfg['thumbnails-dir'].format(game_title)
    

# download youtube data

# get metadata
df = mdata.metadata_main(api_keys, api_service_name, api_version, 
              out_fp, master_dic_write_fp, init_data_fp, 
              game_title, master_dic_fp)
# df = pd.read_csv(ROOT_DIR + cfg["videos-dir"].format(cfg["selected-game"]) + "fortnite_full_metadata.csv")


# download thumbnails
# df required at ROOT_DIR + cfg["thumbnails-dir"].format(cfg["selected-game"])
for qual in cfg["thumbnail-qual"]:
    if cfg["thumbnail-qual"][qual]:
        mdata.download_df_thumbs(df, thumbnails_dir, res=qual)

# do feature extraction

# combine feature extraction into a csv
