from datetime import datetime

import pandas as pd
from keras.models import load_model
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import numpy as np
# import mysql.connector
# from mysql.connector import errorcode
import time
from tensorflow.keras.models import load_model
from keras.layers import PReLU
import os

# MongoDB integration - dual write (CSV + DB)
try:
    from db_models import insert_prediction, insert_active_prediction
    DB_ENABLED = True
except ImportError as e:
    DB_ENABLED = False
    print(f"⚠️  MongoDB not available for predictions: {e}")
def create_dataset(dataset, look_back=1):
    dataX = []
    # Convert dataset to numpy array
    dataset = np.array(dataset)
    for i in range(len(dataset)-look_back+1):
        a = dataset[i:(i+look_back), 0:6]
        dataX.append(a)
        # dataY.append(dataset[(i + look_back)-1, 5])
    return np.array(dataX)
def get_model_prediction(test, nearest_centroid_index, starttime, v_no, user_id=None, session_id=None):

    loaded_model = load_model(f"3_pwindow_lstm_model{nearest_centroid_index}.h5",
                              custom_objects={ 'PReLU': PReLU })
    loaded_model.summary()



    path = './annotation_interface/public/'
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, "pred.csv")


    if not os.path.exists(file_path):
        with open(file_path, "w") as out_file:
            out_file.write("starttime,V_no,Probe\n")


    path2 = './Predictions/'
    out_file2 = open(path2 + "predict.csv", "a")


    # Reshape the new data
    look_back = 3  # Adjust if necessary
    testX = create_dataset(test, look_back)
    testX = np.array(testX, dtype=np.float32)
    testX = np.reshape(testX, (testX.shape[0], look_back, testX.shape[2]))


    # now = datetime.now()
    y_preds = loaded_model.predict(testX)  # , verbose=0)
    # now2 = datetime.now()
    # time_difference = now2 - now
    # difference_in_milliseconds = time_difference.total_seconds() * 1000
    # print("time taken for profile creation", difference_in_milliseconds)

    y_pred_class = np.argmax(y_preds, axis=1)
    print(f"Predicted Classes: {y_pred_class}")

    prev_window_labels = ["HH", "HL", "LH", "LL"]
    # Map numerical predictions to labels
    y_pred_labels = [prev_window_labels[class_idx] for class_idx in y_pred_class]
    print(f"Predicted Labels:==> {y_pred_labels}")

    print("start",starttime)
    print("prediction", y_pred_labels)
    # manual_pred_flag = 0

    # DUAL WRITE: CSV files (existing functionality)
    out_file2.write(
            f"{starttime},{v_no},"
            f"{y_pred_labels[0]}\n"
        )

    with open(file_path, "a") as out_file:
        out_file.write(
            f"{starttime},{v_no},"
            f"{y_pred_labels[0]}\n"
        )

    # DUAL WRITE: MongoDB (new functionality) - now with user_id and session_id
    if DB_ENABLED:
        try:
            # Permanent prediction log
            insert_prediction(starttime, v_no, y_pred_labels[0], nearest_centroid_index, user_id, session_id)
            # Active prediction for frontend
            insert_active_prediction(starttime, v_no, y_pred_labels[0], user_id, session_id)
            log_msg = f"📊 Inserted prediction to MongoDB: {y_pred_labels[0]}"
            if user_id:
                log_msg += f" (user: {user_id})"
            print(log_msg)
        except Exception as e:
            print(f"⚠️  MongoDB insert failed for prediction: {e}. CSV backup intact.")

    y_pred_class = np.array([1])
    return y_pred_class