# Import the module (file) containing the function
import csv

import pandas as pd
import numpy as np
import schedule
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import glob
from datetime import datetime
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# MongoDB integration - dual write (CSV + DB)
try:
    from db_models import insert_video_start, clear_active_predictions
    DB_ENABLED = True
    print("✅ MongoDB integration enabled in main.py")
except ImportError as e:
    DB_ENABLED = False
    print(f"⚠️  MongoDB not available in main.py: {e}")

global_nearest_centroid_index = None


class CSVHandler(FileSystemEventHandler):
    nearest_centroid_index = None

    def __init__(self, source_folder, destination_folder):
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.first_iteration = True
        self.x = 1
        self.files_copied_count = 0


    def on_created(self, event):
        if event.is_directory:
            return

        print(f"File created: {event.src_path}")

        file_extension = os.path.splitext(event.src_path)[1].lower()

        # Check for both CSV and TMP extensions, ignore MP4 files
        if file_extension in (".csv", ".tmp") and file_extension not in (".mp4", ".txt"):

            if event.src_path.lower().endswith((".csv", ".tmp")):

                file_name = os.path.basename(event.src_path)
                source_path = os.path.normpath(os.path.join(self.source_folder, file_name))
                destination_path = os.path.join(self.destination_folder, file_name)

                # Check if the source file exists before copying
                if os.path.exists(source_path):
                    # Copy the file even if it has a .tmp extension
                    shutil.copyfile(source_path, destination_path)
                    print(f"File '{file_name}' copied to {self.destination_folder}")

                    df = pd.read_csv(destination_path, encoding='ISO-8859-1', header=None)
                    print("\nDataFrame from the copied file:")
                    print(df)

                    # Retrieve the latest timestamp file in the destination folder
                    list_of_files = os.listdir(destination_folder)
                    latest_file = max(list_of_files,
                                      key=lambda x: os.path.getctime(os.path.join(destination_folder, x)))
                    latest_file_path = os.path.join(destination_folder, latest_file)

                    df_latest = pd.read_csv(latest_file_path, encoding='ISO-8859-1', header=None)

                    video = df_latest.loc[0, 1]
                    print(f"video == {video}")


                    self.files_copied_count += 1
                    print("self.files_copied_count:", self.files_copied_count)

                    if (video % 2 == 0):

                        # Read the copied file into a DataFrame
                        try:

                            video_id = 0
                            start_time = 0
                            start_time2 = 0
                            end_time = 0
                            actual_end_time = 0


                            start_times = df_latest.loc[0]
                            start_timess = start_times.values[0]
                            start_time = int(start_timess)
                            # start_time = int(start_times)
                            print("time",  start_time)

                            if (self.files_copied_count == 1): #| video == 0):
                                video_id = 1 #180
                                actual_end_time = start_time + 180000
                            elif (self.files_copied_count == 2): #| video == 2):
                                video_id = 2 #151
                                actual_end_time = start_time + 151000
                            elif (self.files_copied_count == 3): # | video == 4):
                                video_id = 3 #160
                                actual_end_time = start_time + 160000
                            elif (self.files_copied_count == 4): # | video == 6):
                                video_id = 4 #117
                                actual_end_time = start_time + 117000
                            
                            # DUAL WRITE: MongoDB - Record video start event
                            if DB_ENABLED and video_id > 0:
                                try:
                                    insert_video_start(start_time, video_id)
                                    print(f"📊 Video start recorded in MongoDB: video_id={video_id}, timestamp={start_time}")
                                except Exception as e:
                                    print(f"⚠️  MongoDB insert failed for video start: {e}")


                            # if (self.files_copied_count == self.x):
                            #     video_id = 6
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (177000 - 20000)
                            #     actual_end_time = start_time + video6
                            # if (self.files_copied_count == self.x):
                            #     video_id = 7
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (172000 - 20000)
                            #     actual_end_time = start_time + video7
                            # if (self.files_copied_count == self.x):
                            #     video_id = 4
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (118000 - 20000)
                            #     actual_end_time = start_time + video4
                            # if (self.files_copied_count == self.x):
                            #     video_id = 8
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (165000 - 20000)
                            #     actual_end_time = start_time + video8
                            # if (self.files_copied_count == self.x):
                            #     video_id = 5
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (1c45000 - 20000)
                            #     actual_end_time = start_time + video5
                            # if (self.files_copied_count == self.x):
                            #     video_id = 2
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (146000 - 20000)
                            #     actual_end_time = start_time + video2
                            # if (self.files_copied_count == self.x):
                            #     video_id = 3
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (198000 - 20000)
                            #     actual_end_time = start_time + video3
                            # if (self.files_copied_count == self.x):
                            #     video_id = 1
                            #     self.x = self.x + 1
                            #     #actual_end_time = start_time + (147000 - 20000)
                            #     actual_end_time = start_time + video1

                            # current_time = int(time.time() * 1000)
                            #
                            # if start_time2 <= current_time:
                            #     while start_time2 < current_time:
                            #         current_time = int(time.time() * 1000)
                            #         time.sleep(5)
                            # time.sleep(5)

                            # time.sleep(16)




                            if (self.files_copied_count == 1):
                                time.sleep(180)
                                global global_nearest_centroid_index
                                # now = datetime.now()
                                new_data = []
                                signals = pd.read_csv("signals_data.csv")
                                # print(signals)
                                PS = np.asanyarray(signals) 
                                # length_data = (len(PS))
                                print("timestamp", int(PS[0, 3]))
                                for j in range(len(PS)):
                                    timestamp_value = int(PS[j, 3])
                                    # print("timestamp_value", timestamp_value)
                                    # temp_end_time = start_time2 + 20000
                                    if ((start_time2 <= timestamp_value) and ( actual_end_time >= timestamp_value)):
                                        # if ((start_time2 <= PS[j, 3]) & (end_time >= PS[j, 3])):
                                        new_data.append(PS[j])

                                print("new_data", new_data)
                                new_df = pd.DataFrame(new_data)
                                new_df.rename(columns={0: 'Time_series'}, inplace=True)
                                new_df.rename(columns={1: 'GSR'}, inplace=True)
                                new_df.rename(columns={2: 'HR'}, inplace=True)
                                new_df.rename(columns={3: 'timestamp'}, inplace=True)
                                new_df.rename(columns={4: 'time2'}, inplace=True)
                                # new_df["subject"] = str(id)
                                # id = str(i)
                                new_df["video_id"] = video_id
                                new_df.to_csv("test/online_" + str(start_time2) + ".csv")


                                # read_file
                                filename = pd.read_csv("test/online_" + str(start_time2) + ".csv")
                                print("filename", filename)

                                # Calculate_change_point_score
                                from cal_change_point import get_change_point_scores

                                get_change_point_scores(filename, start_time2, window_size=50)
                                # now2 = datetime.now()
                                # time_difference = now - now2
                                # difference_in_milliseconds = time_difference.total_seconds() * 1000
                                # print("time taken for profile creation", difference_in_milliseconds)
                                # now = datetime.now()
                                score_df = pd.read_csv("score/" + str(start_time2) + "scores.csv")
                                input = "Score"
                                if score_df.empty:
                                    print(
                                        f"Warning: DataFrame new_df is empty. Skipping the remaining code for iteration")
                                else:
                                    # calculate_physiological_difference
                                    from profile_cluster_creation import do_cluster_newdata
                                    from profile_cluster_creation import do_new_user_label
                                    from profile_cluster_creation import nearest_cluster_allocation

                                    valence_arousal_vectors = do_cluster_newdata(score_df, input)
                                    new_vector = do_new_user_label(valence_arousal_vectors)
                                    nearest_centroid_index = nearest_cluster_allocation(new_vector)
                                # now2 = datetime.now()
                                # time_difference = now2 - now
                                # difference_in_milliseconds = time_difference.total_seconds() * 1000
                                # print("time taken for profile creation", difference_in_milliseconds)

                                print(nearest_centroid_index)

                                global_nearest_centroid_index = nearest_centroid_index

                            else:
                                    temp_start = start_time
                                    bs_start_time = (temp_start - 5000)
                                    time.sleep(15)

                                    prediction = [3,2]

                                    for i in range(start_time, actual_end_time, 5000):

                                        # current_time2 = int(time.time() * 1000)
                                        # if (current_time2 >= dummy_end_time):
                                        #     break
                                        #
                                        # else:

                                            if (i >= (actual_end_time-20000)):
                                                # DUAL WRITE: CSV - Clear pred.csv (existing functionality)
                                                file_path = './annotation_interface/public/pred.csv'
                                                with open(file_path, 'r') as file:
                                                    reader = csv.reader(file)
                                                    header = next(reader, None)  # Read the first row (header)

                                                # Overwrite the file with just the header
                                                if header:
                                                    with open(file_path, 'w', newline='') as file:
                                                        writer = csv.writer(file)
                                                        writer.writerow(header)  # Write only the header back
                                                
                                                # DUAL WRITE: MongoDB - Clear active predictions
                                                if DB_ENABLED:
                                                    try:
                                                        clear_active_predictions(video_id)
                                                        print(f"🗑️  Cleared active predictions for video {video_id} in MongoDB")
                                                    except Exception as e:
                                                        print(f"⚠️  MongoDB clear failed for active predictions: {e}")


                                            start_time2 = i
                                            end_time = (start_time2 + 15000)

                                            while (end_time > (int(time.time() * 1000))):
                                                time.sleep(1)


                                            new_data = []
                                            bS_data = []
                                            signals = pd.read_csv("signals_data.csv")
                                            PS = np.asanyarray(signals)
                                            # length_data = (len(PS))
                                            print("timestamp", int(PS[0, 3]))
                                            print("start_time", start_time2)
                                            for j in range(1, len(PS)):
                                                timestamp_value = int(PS[j, 3])

                                                if ((bs_start_time <= timestamp_value) and (temp_start >= timestamp_value)):
                                                        # print(f"+++++++++++++{PS[j]}")
                                                        bS_data.append(PS[j])

                                                if ((start_time2 <= timestamp_value) and (end_time >= timestamp_value)):
                                                        new_data.append(PS[j])

                                            # print("new_data", new_data)
                                            bs_df = pd.DataFrame(bS_data)
                                            bs_df.rename(columns={0: 'Time_series'}, inplace=True)
                                            bs_df.rename(columns={1: 'GSR'}, inplace=True)
                                            bs_df.rename(columns={2: 'HR'}, inplace=True)
                                            bs_df.rename(columns={3: 'timestamp'}, inplace=True)
                                            bs_df.rename(columns={4: 'time2'}, inplace=True)
                                            bs_df["video_id"] = video_id
                                            bs_df.to_csv("test/bs_data.csv")


                                            # print("new_data", new_data)
                                            new_df = pd.DataFrame(new_data)
                                            new_df.rename(columns={0: 'Time_series'}, inplace=True)
                                            new_df.rename(columns={1: 'GSR'}, inplace=True)
                                            new_df.rename(columns={2: 'HR'}, inplace=True)
                                            new_df.rename(columns={3: 'timestamp'}, inplace=True)
                                            new_df.rename(columns={4: 'time2'}, inplace=True)
                                            new_df["video_id"] = video_id
                                            # new_df["prev_window"] = [prediction[-1]] * len(new_df)
                                            new_df.to_csv("test/online_" + str(start_time2) + ".csv")

                                            if new_df.empty:
                                                print(
                                                    f"Warning: DataFrame new_df is empty. Skipping the remaining code for iteration {i}.")
                                                continue

                                            # read_file
                                            filename = pd.read_csv("test/online_" + str(start_time2) + ".csv")
                                            filename_bs = pd.read_csv("test/bs_data.csv")
                                            # print("filename", filename)

                                            # Calculate_change_point_score
                                            from cal_change_point import get_change_point_scores
                                            get_change_point_scores(filename, start_time2, window_size=50)
                                            score_df = pd.read_csv("score/" + str(start_time2) + "scores.csv")
                                            if score_df.empty:
                                                print(
                                                    f"Warning: DataFrame new_df is empty. Skipping the remaining code for iteration {i}.")
                                                break
                                            else:
                                                ##calculate_physiological_difference
                                                from cal_physiological_diff import get_signal_diff
                                                get_signal_diff(filename, filename_bs , start_time2, prediction)


                                                ###Predict_opportune_moment
                                                from model_prediction import get_model_prediction
                                                final_feature = pd.read_csv("final/windowdata.csv")
                                                v_no = video_id #final_feature['video_id'].iloc[0]

                                                if len(final_feature) > 3:
                                                    index_values = final_feature.index[
                                                                final_feature['Start_time'] == start_time2].tolist()
                                                    # print("index_values",index_values)
                                                    for k in range(len(index_values)):
                                                        # Get the previous two rows for each index value
                                                        current_index = index_values[k]
                                                        print("current_index", current_index)
                                                        if current_index >= 3:
                                                            previous_two_rows = final_feature.iloc[current_index - 3: current_index]
                                                            # Print or use the resulting DataFrame as needed
                                                            # previous_two_rows.to_csv("testrow.csv")
                                                            print("previous_two_rows", previous_two_rows)
                                                        else:
                                                            print("Not enough previous rows found for the condition.")

                                                        test = pd.DataFrame(previous_two_rows)
                                                        testX = test[
                                                                ['Score', 'GSR_diff', 'HR_diff', 'Previous_window', 'valence_acc_video', 'arousal_acc_video',]]
                                                        y_pred_class = get_model_prediction(testX, global_nearest_centroid_index, start_time2, v_no)
                                                        prediction.append(y_pred_class.item())
                                                        print(f"Predictions:{prediction}")

                                                        # time.sleep(5)

                        except pd.errors.EmptyDataError:
                            print(f"Warning: The copied file '{file_name}' is empty.")
                        except pd.errors.ParserError:
                            print(f"Warning: Unable to parse the copied file '{file_name}' as CSV.")
                    else:
                        print(f"Skipping processing because the count is not even.")

                else:
                    print(f"Warning: Source file '{source_path}' not found.")

def watch_folder(source_folder, destination_folder):
    event_handler = CSVHandler(source_folder, destination_folder)
    observer = Observer()
    observer.schedule(event_handler, path=source_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(2)

    except KeyboardInterrupt:
        observer.stop()

    observer.join()



# Example usage:
source_folder = "./downloaded"
destination_folder = "./csv_data"

watch_folder(source_folder, destination_folder)





