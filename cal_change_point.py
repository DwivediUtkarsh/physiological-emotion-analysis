from collections import Counter
from centralized_baseline import is_change_present
from densratio import densratio
import glob
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from natsort import natsorted, ns
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# MongoDB integration - dual write (CSV + DB)
try:
    from db_models import insert_change_score
    DB_ENABLED = True
except ImportError as e:
    DB_ENABLED = False
    print(f"⚠️  MongoDB not available for change scores: {e}")
def get_change_point_scores(filename, start_time, window_size=50):
    original_data = filename

    # print(original_data.columns)
    # print("score_cal",original_data)

    # if(video_id!=-1):
    # filter_data = original_data['video']==video_id
    # original_data = original_data [filter_data]

    # print('directory:{},filename:{}'.format(directory, filename))

    # data = original_data[['value_EDA','value_TEMP','value_HR']]
    data = original_data[['GSR', 'HR']]
    # print('data:{}'.format(data))
    data = np.asanyarray(data)
    # print(data.shape)
    # out_file = open(directory+filename.split("/")[len(filename.split("/"))-1].split(".")[0]+"_scores.csv","w+")
    path = './score/'
    out_file = open(path +str(start_time)+"scores.csv", "w+")
    # x = filename.split("/")[len(filename.split("/")) - 1].split(".")[0] + "_scores.csv"
    # print(x)

    out_file.write("Start,Border,End,Score\n")
    scores = []
    db_scores = []  # Collect scores for MongoDB insertion
    # print("len of data", len(data))
    for i in range(0, len(data) - 2 * window_size, window_size):
        # Creating samples
        x = data[i:i + window_size, :]
        # print(x.shape)
        y = data[i + window_size:i + 2 * window_size, :]
        # print(y.shape)

        alpha = 0.1  # needed for RuLSif

        # calculating x to y
        densratio_obj = densratio(x, y, alpha=alpha)
        score_x_y = float(densratio_obj.alpha_PE)

        # calculating y to x
        densratio_obj = densratio(y, x, alpha=alpha)
        score_y_x = float(densratio_obj.alpha_PE)

        '''Total change point score = score_x_y + score_y_x -- Taking absolute'''
        start_ts = int(original_data['timestamp'].iat[i])
        border_ts = int(original_data['timestamp'].iat[i + window_size])
        end_ts = int(original_data['timestamp'].iat[i + 2 * window_size])
        total_score = abs(score_x_y) + abs(score_y_x)
        
        # DUAL WRITE: CSV file (existing functionality)
        out_file.write(str(start_ts) + "," + str(border_ts) + "," + str(end_ts) + "," + str(total_score) + "\n")
        out_file.flush()
        
        # Collect for MongoDB insertion
        if DB_ENABLED:
            db_scores.append({
                'start': start_ts,
                'border': border_ts,
                'end': end_ts,
                'score': total_score
            })
    
    out_file.close()
    
    # DUAL WRITE: MongoDB (new functionality)
    if DB_ENABLED and db_scores:
        try:
            for score_data in db_scores:
                insert_change_score(
                    start_time=start_time,
                    start=score_data['start'],
                    border=score_data['border'],
                    end=score_data['end'],
                    score=score_data['score']
                )
            print(f"📊 Inserted {len(db_scores)} change scores to MongoDB")
        except Exception as e:
            print(f"⚠️  MongoDB insert failed for change scores: {e}. CSV backup intact.")

