import pandas as pd
import numpy as np

def collaborative_filtering(df, drop_cols = ["brewery", "subgenre", "abv"]):
    df_colab = df.drop(drop_cols, axis=1)
    user_means = df_colab.groupby('reviewer')['rating'].mean()
    user_std = df_colab.groupby('reviewer')['rating'].std()
    df_colab['normalized_rating'] = df_colab.apply(lambda row: (row['rating'] - user_means[row['reviewer']]) / user_std[row['reviewer']] if user_std[row['reviewer']] > 0 else 0, axis=1)
    # TODO Tænk over om normalisering giver mening ift. at man måske bare godt kan lide alle øl?
    # For man har ikke alle personens anmeldelser kun dens anmeldelser af gode øl
    threshold = 3 # Threshold for like/hate
    df_colab["like/hate"] = df_colab["rating"].apply(lambda x: 1 if x >= threshold else 0)
    utility_matrix = df_colab.pivot_table(index='reviewer', columns='name', values='like/hate')
    # Fill missing values with NaN or 0 (depending on the approach you want to take)
    utility_matrix = utility_matrix.fillna(0)
    binary_matrix = utility_matrix.values
    user = binary_matrix[0,:]
    # Compute intersections
    intersection = np.dot(user, binary_matrix.T)

    # Compute union
    union = np.bitwise_or(user.reshape(1, -1).astype(int), binary_matrix.astype(int)).sum(axis=1)

    # Compute Jaccard similarity
    jaccard_similarity = intersection / union
    jaccard_similarity_df = pd.DataFrame(jaccard_similarity, index=utility_matrix.index, columns=['Jaccard Similarity'])

    # Get the top-k similar users for each user
    k = 5  # Number of neighbors
    top_k_neighbors = jaccard_similarity_df.nlargest(5, "Jaccard Similarity")
    return top_k_neighbors