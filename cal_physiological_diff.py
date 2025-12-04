import numpy as np
import pandas as pd
video_id = [1, 2, 3, 4, 5, 6, 7, 8]

# MongoDB integration - dual write (CSV + DB)
try:
    from db_models import insert_feature
    DB_ENABLED = True
except ImportError as e:
    DB_ENABLED = False
    print(f"⚠️  MongoDB not available for features: {e}")

def insert_feature_to_db(start_time, score, gsr_diff, hr_diff, prev_window, valence, arousal, v_id):
    """Helper function to insert feature data to MongoDB (dual write)"""
    if DB_ENABLED:
        try:
            insert_feature({
                'start_time': start_time,
                'score': score,
                'gsr_diff': gsr_diff,
                'hr_diff': hr_diff,
                'previous_window': prev_window,
                'valence_acc_video': valence,
                'arousal_acc_video': arousal,
                'video_id': v_id
            })
        except Exception as e:
            print(f"⚠️  MongoDB insert failed for feature: {e}")

def get_signal_diff(filename, filename_bs, start_time, pred):
        #print("start", start_time)
        original = filename
        path = './final/'
        out_file = open(path + "windowdata.csv", "a+")

        bs_data = filename_bs[['GSR', 'HR']]
        bs_data = np.asanyarray(bs_data)
        GSR_meanblue = bs_data[:, 0].mean()
        HR_meanblue = bs_data[:, 1].mean()
        print("PRED", pred)



        for v in video_id:
                index = original["video_id"] == v
                original_data = original[index]
                if not original_data.empty:
                        data = original_data[['GSR', 'HR']]
                        data = np.asanyarray(data)
                        window_size = 50
                        GSR_diff = []
                        HR_diff = []
                        prev_window_values = []  # Store values for 'prev_window'

                        for i in range(0, len(data) - window_size, window_size):
                            x = data[i:i + window_size, :]

                            xGSR_mean = x[:, 0].mean()
                            a = abs(GSR_meanblue - xGSR_mean)
                            GSR_diff.append(a)

                            xHR_mean = x[:, 1].mean()
                            b = abs(HR_meanblue - xHR_mean)
                            HR_diff.append(b)

                            # Handle prev_window assignment correctly
                            if 'pred' in locals() and len(pred) >= 2:
                                if i == 0:
                                    prev_window_values.append(pred[-2])
                                # elif i == window_size:
                                #     prev_window_values.append(pred[-1])
                                else:
                                    prev_window_values.append(pred[-1])

                        # Create DataFrame after loop to avoid column length mismatch
                        new_window = pd.DataFrame({
                            'GSR_diff': GSR_diff,
                            'HR_diff': HR_diff,
                            'prev_window': prev_window_values
                        })

                        if (v == 1):
                                        new_window["valence_acc_video"] = 1
                                        new_window["arousal_acc_video"] = 1
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                                "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                # DUAL WRITE: CSV file (existing functionality)
                                                out_file.write(
                                                        f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                        f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                        f"{new_window['video_id'].iloc[0]}\n"
                                                )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           1, 1, v)
                        elif(v == 2):
                                        new_window["valence_acc_video"] = 0
                                        new_window["arousal_acc_video"] = 1
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                            "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                # DUAL WRITE: CSV file (existing functionality)
                                                out_file.write(
                                                        f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                        f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                        f"{new_window['video_id'].iloc[0]}\n"
                                                )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           0, 1, v)
                        elif(v == 3):
                                        new_window["valence_acc_video"] = 0
                                        new_window["arousal_acc_video"] = 0
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/"+ str(start_time)+"scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        if not scores.empty and not new_window.empty:
                                                with open('final/windowdata.csv', 'a') as out_file:
                                                        # Check if the file is empty
                                                        if out_file.tell() == 0:
                                                                # If the file is empty, write the header
                                                                out_file.write(
                                                                    "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                                # DUAL WRITE: CSV file (existing functionality)
                                                        out_file.write(
                                                                    f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                                    f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                                    f"{new_window['video_id'].iloc[0]}\n"
                                                                )
                                                
                                                # DUAL WRITE: MongoDB (new functionality)
                                                insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                                   new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                                   0, 0, v)

                        elif(v == 4):
                                        new_window["valence_acc_video"] = 1
                                        new_window["arousal_acc_video"] = 0
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                             "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                # DUAL WRITE: CSV file (existing functionality)
                                                out_file.write(
                                                        f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                        f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                        f"{new_window['video_id'].iloc[0]}\n"
                                                )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           1, 0, v)
                        elif(v == 5):
                                        new_window["valence_acc_video"] = 1
                                        new_window["arousal_acc_video"] = 0
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                            "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                        # DUAL WRITE: CSV file (existing functionality)
                                                        out_file.write(
                                                            f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                            f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                            f"{new_window['video_id'].iloc[0]}\n"
                                                        )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           1, 0, v)
                        elif(v == 6):
                                        new_window["valence_acc_video"] = 1
                                        new_window["arousal_acc_video"] = 0
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                            "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                        # DUAL WRITE: CSV file (existing functionality)
                                                        out_file.write(
                                                            f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                            f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                            f"{new_window['video_id'].iloc[0]}\n"
                                                        )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           1, 0, v)
                        elif(v == 7):
                                        new_window["valence_acc_video"] = 0
                                        new_window["arousal_acc_video"] = 1
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                            "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                        # DUAL WRITE: CSV file (existing functionality)
                                                        out_file.write(
                                                            f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                            f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                            f"{new_window['video_id'].iloc[0]}\n"
                                                        )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           0, 1, v)
                        elif(v == 8):
                                        new_window["valence_acc_video"] = 0
                                        new_window["arousal_acc_video"] = 1
                                        new_window["video_id"] = v
                                        scores = pd.read_csv("score/" + str(start_time) + "scores.csv")
                                        # scores = scores[['Score']]
                                        result = pd.concat([scores, new_window], axis=1)
                                        # Open the file in append mode
                                        with open('final/windowdata.csv', 'a') as out_file:
                                                # Check if the file is empty
                                                if out_file.tell() == 0:
                                                        # If the file is empty, write the header
                                                        out_file.write(
                                                                "Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")

                                                # DUAL WRITE: CSV file (existing functionality)
                                                out_file.write(
                                                        f"{start_time},{scores['Score'].iloc[0]},{new_window['GSR_diff'].iloc[0]},{new_window['HR_diff'].iloc[0]},"
                                                        f"{new_window['prev_window'].iloc[0]},{new_window['valence_acc_video'].iloc[0]},{new_window['arousal_acc_video'].iloc[0]},"
                                                        f"{new_window['video_id'].iloc[0]}\n"
                                                )
                                        
                                        # DUAL WRITE: MongoDB (new functionality)
                                        insert_feature_to_db(start_time, scores['Score'].iloc[0], new_window['GSR_diff'].iloc[0],
                                                           new_window['HR_diff'].iloc[0], new_window['prev_window'].iloc[0],
                                                           0, 1, v)
        final_feature = pd.read_csv("final/windowdata.csv")
        print(f"now{final_feature}")

