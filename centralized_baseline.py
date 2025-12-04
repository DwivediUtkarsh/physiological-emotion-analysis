from collections import Counter
import glob
from imblearn.over_sampling import SMOTE
import numpy as np
from natsort import natsorted, ns
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

def perform_classification(X_train,y_train,X_test,y_test):
	X_train, y_train = get_balanced_data(X_train,y_train)

	print(X_train.shape)
	print(X_test.shape)

	print("Train Label Distribution: "+str(Counter(y_train)))
	print("Test Label Distribution: "+str(Counter(y_test)))

	rf = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=0)
	rf.fit(X_train,y_train)
	predicted_rf = rf.predict(X_test)
	print(f1_score(y_test,predicted_rf,average='micro'))


def get_balanced_data(X,y):
	sm = SMOTE(random_state=42)
	print('Before Resampling dataset distribution %s' % Counter(y))
	X, y = sm.fit_resample(X, y)
	print('Resampled dataset distribution %s' % Counter(y))
	return X,y

def get_min_window_size_rest(query_subject):
	in_file = open("learned_window_size.txt","r+")
	window_sizes = []
	for lines in in_file:
		lines = lines.strip("\r\n")
		if(lines.split(",")[0]!=query_subject):
			window_sizes.append(float(lines.split(",")[1]))
	in_file.close()
	return min(window_sizes)

def create_sensor_data(time_list,data,window_size):
	window_size = int(window_size)
	data = np.asanyarray(data)
	#print(data)
	windowed_data = []
	start_time = []
	end_time = []
	for i in range(0,len(data)-window_size,window_size):
		windowed_data.append(np.mean(data[i:i+window_size,:],axis=0).tolist()) #Column-wise mean for each window
		start_time.append(time_list[i])
		end_time.append(time_list[i+window_size-1])
	windowed_data = np.asanyarray(windowed_data)

	return start_time,end_time,windowed_data

def is_change_present(label_list):
	if(len(Counter(label_list))>1):
		return True
	return False

def create_ml_data(sensor_file,annotations_file,window_size):

	print("Windowing sensor files")
	sensor_file = pd.read_csv(sensor_file)
	start_time,end_time,data = create_sensor_data(sensor_file['daqtime'],sensor_file[['bvp','gsr','rsp','skt','emg_zygo','emg_coru','emg_trap']],window_size)

	label_valence = []
	label_arousal = []

	print("Mapping annotation files")
	annotations_file = pd.read_csv(annotations_file)

	for i in range(len(start_time)):
		print("****"+str(i)+"****")
		valence_list = []
		arousal_list = []
		for j in range(len(annotations_file['jstime'])):
			#print("****"+str(j)+"****")
			if(annotations_file['jstime'][j]>=start_time[i] and annotations_file['jstime'][j]<=end_time[i]):
				valence_list.append(annotations_file['valence'][j])
				arousal_list.append(annotations_file['arousal'][j])
			elif(annotations_file['jstime'][j]>end_time[i]):
				break

		if(is_change_present(valence_list)):
			label_valence.append(1)
		else:
			label_valence.append(0)

		if(is_change_present(arousal_list)):
			label_arousal.append(1)
		else:
			label_arousal.append(0)

	assert len(label_valence) == len(label_arousal)

	assert len(label_valence) == len(data)

	return data, label_valence, label_arousal

def main():

	out_file = open("accuracy.csv","w+")
	out_file.write("Subject,Micro_F1_Valence,Micro_F1_Arousal"+"\n")

	sensor_data_directory = "../data/non-interpolated/physiological/"
	annotations_directory = "../data/non-interpolated/annotations/"

	file_list = glob.glob(sensor_data_directory+"*.csv")
	file_list = natsorted(file_list, key=lambda y: y.lower())
	
	for i in range(len(file_list)):
		query_subject = file_list[i].split("/")[-1].split(".")[0]
		print(query_subject)
		window_size = 1000.0#get_min_window_size_rest(query_subject)
		print("Window Size: "+str(window_size))

		X_test, y_test_valence, y_test_arousal = create_ml_data(file_list[i],annotations_directory+query_subject+".csv",window_size)
		X_train  = []
		y_train_valence = []
		y_train_arousal = []
		for j in range(len(file_list)):
			if(i!=j):
				print("Creating training data from: "+file_list[j].split("/")[-1].split(".")[0])
				data = []
				label_valence = []
				label_arousal = []
				data, label_valence, label_arousal = create_ml_data(file_list[j],annotations_directory+file_list[j].split("/")[-1].split(".")[0]+".csv",window_size)
				if(len(X_train)==0 and len(y_train_valence)==0 and len(y_train_arousal)==0):
					X_train = np.asanyarray(data)
					y_train_valence = np.asarray(label_valence)
					y_train_arousal = np.asarray(label_arousal)
				else:
					data = np.asanyarray(data)
					label_valence = np.asarray(label_valence)
					label_arousal = np.asarray(label_arousal)
					
					X_train = np.concatenate((X_train,data),axis=0)
					y_train_valence = np.concatenate((y_train_valence,label_valence))
					y_train_arousal = np.concatenate((y_train_arousal,label_arousal))
			
		print("Change Valence Classification")
		perform_classification(X_train,y_train_valence,X_test,y_test_valence)

		print("Change Arousal Classification") 
		perform_classification(X_train,y_train_arousal,X_test,y_test_arousal)
		
		out_file.write(query_subject+","+str(acc_valence)+","+str(acc_arousal)+"\n")
		out_file.flush()

	out_file.close()

if __name__ == '__main__':
	main()