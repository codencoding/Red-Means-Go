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
    
    

# download youtube data

# get metadata
df = pd.read_csv(ROOT_DIR + cfg["videos-dir"].format(cfg["selected-game"]) + "fortnite_full_metadata.csv")


# download thumbnails
# df required at ROOT_DIR + cfg["thumbnails-dir"].format(cfg["selected-game"])
for qual in cfg["thumbnail-qual"]:
    if cfg["thumbnail-qual"][qual]:
        mdata.download_df_thumbs(df, ROOT_DIR + cfg["thumbnails-dir"].format(cfg["selected-game"]), res=qual)

# do feature extraction

# combine feature extraction into a csv
