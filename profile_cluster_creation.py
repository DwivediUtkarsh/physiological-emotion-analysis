from sklearn.cluster import KMeans
import numpy as np
import pandas as pd


def  do_cluster_newdata(ds, input):

    newds = ds[f"{input}"]
    # print(f"newds:{newds}")
    xx = np.array(newds).reshape(-1, 1)
    print(f"newds:{newds.shape}")

    cluster = KMeans(n_clusters=4, random_state=0)
    cluster.fit(xx)
    Cluster_label = cluster.predict(xx)
    print(Cluster_label)

    ###Initialize lists for the three clusters
    cluster_0 = []
    cluster_1 = []
    cluster_2 = []
    cluster_3 = []
    ###Assign each data point to its respective cluster
    for i, cluster_label in enumerate(Cluster_label):
        if cluster_label == 0:
            cluster_0.append(newds.index[i])
        elif cluster_label == 1:
            cluster_1.append(newds.index[i])
        elif cluster_label == 2:
            cluster_2.append(newds.index[i])
        elif cluster_label == 3:
            cluster_3.append(newds.index[i])
    # Print the resulting clusters
    print("Cluster 0:", len(cluster_0), cluster_0)
    print("Cluster 1:", len(cluster_1), cluster_1)
    print("Cluster 2:", len(cluster_2), cluster_2)
    print("Cluster 3:", len(cluster_3), cluster_3)


    if (len(cluster_0)>1):
        mean_data_0 = newds.loc[cluster_0].mean()
        std_data_0 = newds.loc[cluster_0].std()
    else:
        mean_data_0 = newds.loc[cluster_0].mean()
        std_data_0 = 0

    if (len(cluster_1) > 1):
        mean_data_1 = newds.loc[cluster_1].mean()
        std_data_1 = newds.loc[cluster_1].std()
    else:
        mean_data_1 = newds.loc[cluster_1].mean()
        std_data_1 = 0

    if (len(cluster_2) > 1):
        mean_data_2 = newds.loc[cluster_2].mean()
        std_data_2 = newds.loc[cluster_2].std()
    else:
        mean_data_2 = newds.loc[cluster_2].mean()
        std_data_2 = 0

    if (len(cluster_3) > 1):
        mean_data_3 = newds.loc[cluster_3].mean()
        std_data_3 = newds.loc[cluster_3].std()

    else:
        mean_data_3 = newds.loc[cluster_3].mean()
        std_data_3 = 0

    # print("mean_data_0:", mean_data_0)
    # print("mean_data_1:", mean_data_1)
    # print("mean_data_2:", mean_data_2)
    # print("mean_data_3:", mean_data_3)

    newuser_vector_data = [mean_data_0 , std_data_0, mean_data_1, std_data_1, mean_data_2 , std_data_2, mean_data_3, std_data_3 ]

    return newuser_vector_data


def do_new_user_label(valence_arousal_vectors):
    cluster_centroid =[[0.13223871, 0.1163289,  0.12379743, 0.10381793, 0.13483915, 0.12861226,
                        0.13613065, 0.12001119], [0.32451873, 0.2192287,  0.36434825, 0.22801673, 0.35199746, 0.21530797,
                       0.31286902, 0.20634948]]

    actual_cluster_centroid = np.array(cluster_centroid).flatten().tolist()

    actual_cluster_centroid = np.array(actual_cluster_centroid)
    valence_arousal_vector = np.array(valence_arousal_vectors)

    print(f"actual_cluster_centroid: {actual_cluster_centroid}")
    print(f"new_user_vector:{valence_arousal_vector}")

    index = []
    positions = []
    new_vector = [None] * 8

    for i in range(0, len(valence_arousal_vector), 2):
        distances = []
        centroid_positions = []

        for j in range(0, len(actual_cluster_centroid), 2):
            # Ensure we are comparing different centroids
            if j not in positions:
                distance = np.linalg.norm(
                    np.array([actual_cluster_centroid[j], actual_cluster_centroid[j + 1]]) -
                    np.array([valence_arousal_vector[i], valence_arousal_vector[i + 1]])
                )
                print(f"Distance between centroid ({j}, {j + 1}) and vector ({i}, {i + 1}): {distance}")
                distances.append(distance)
                centroid_positions.append(j)

                # Find the nearest centroid index
        nearest_centroid_index = np.argmin(distances)
        nearest_position = centroid_positions[nearest_centroid_index]
        print(f"Nearest centroid index for element: {nearest_centroid_index}, nearest Position: {nearest_position}")

        # Assign specific positions based on nearest_position value
        if nearest_position == 0 or nearest_position == 8:
            index.append(nearest_centroid_index)
            positions.append(0)
            positions.append(8)
            new_vector[0] = valence_arousal_vector[i]
            new_vector[1] = valence_arousal_vector[i + 1]

        elif nearest_position == 2 or nearest_position == 10:
            index.append(nearest_centroid_index)
            positions.append(2)
            positions.append(10)
            new_vector[2] = valence_arousal_vector[i]
            new_vector[3] = valence_arousal_vector[i+1]

        elif nearest_position == 4 or nearest_position == 12:
            index.append(nearest_centroid_index)
            positions.append(4)
            positions.append(12)
            new_vector[4] = valence_arousal_vector[i]
            new_vector[5] = valence_arousal_vector[i + 1]

        elif nearest_position == 6 or nearest_position == 14:
            index.append(nearest_centroid_index)
            positions.append(6)
            positions.append(14)
            new_vector[6] = valence_arousal_vector[i]
            new_vector[7] = valence_arousal_vector[i + 1]

    # print(f"Final nearest centroid indices: {index}")
    print(f"Final positions: {positions}")
    print(f"Old vector:{valence_arousal_vector}")
    print(f"Final vector:{new_vector}")

    return new_vector





def nearest_cluster_allocation (valence_arousal_vectors_new_data):


    cluster_centroid = np.array([[0.13223871, 0.1163289, 0.12379743, 0.10381793, 0.13483915, 0.12861226,
                                  0.13613065, 0.12001119],
                                 [0.32451873, 0.2192287, 0.36434825, 0.22801673, 0.35199746, 0.21530797,
                                  0.31286902, 0.20634948]])

    # Ensure valence_arousal_vectors_new_data is also a numpy array
    valence_arousal_vectors_new_data = np.array(valence_arousal_vectors_new_data)

    distances = np.linalg.norm(cluster_centroid - valence_arousal_vectors_new_data, axis=1)

    # Find the index of the nearest centroid
    nearest_centroid_index = np.argmin(distances)
    print(f"distances: {distances}")
    print(f"The nearest cluster centroid is at index {nearest_centroid_index} with a distance of {distances[nearest_centroid_index]:.2f}")


    return nearest_centroid_index


    # if (nearest_centroid_index == 0):
    #     Cluster_0 = [1, 2, 3, 6, 9, 12, 18, 19, 23, 24, 25, 27, 28, 29, 30, 32, 33, 34, 36, 39, 41, 42]
    #     cluster_0.append(new_id)
    #     updated_cluster = cluster_0
    #
    #     # final_test_user = make_ground_truth(ds, updated_cluster,test_user,first_video)
    #     # final_test_user = final_test_user.drop(['P_id', 'video_id', 'Probe'], axis=1)
    #     print(f"updated_cluster:{updated_cluster}")
    #     cluster_no = 0
    #     centroid = cluster_centroid
    #     predictions = get_model_prediction(final_test_user, cluster_no,centroid,input,output)
    #
    # elif (nearest_centroid_index == 1):
    #     Cluster_1 = [4, 5, 7, 8, 10, 11, 13, 14, 15, 16, 17, 20, 21, 22, 26, 31, 35, 38, 40]
    #     cluster_1.append(new_id)
    #     updated_cluster = cluster_1
    #
    #     # final_test_user = make_ground_truth(ds, updated_cluster, test_user,first_video)
    #     # final_test_user = final_test_user.drop(['P_id', 'video_id', 'Probe'], axis=1)
    #     print(f"updated_cluster:{updated_cluster}")
    #     cluster_no = 1
    #     centroid = cluster_centroid
    #     predictions = get_model_prediction(final_test_user, cluster_no,centroid,input,output)
    #     # predictions = 0


