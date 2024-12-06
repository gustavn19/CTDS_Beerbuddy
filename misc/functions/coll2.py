import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.metrics.pairwise import cosine_similarity

def predict_ratings_user_based(user_item_matrix, similarity_matrix):
   

    # Compute predictions
    similarity_sum = np.abs(similarity_matrix).sum(axis=1)[:, None]
    pred = pred = np.dot(similarity_matrix, user_item_matrix) / (similarity_sum + 1e-8)



    return pred


def collaborative_filtering(df, drop_cols = ["brewery", "subgenre", "abv", "sbert_embedding"]):
    #df_colab = df.drop(drop_cols, axis=1)
    df_colab = df
    #df_colab['rating'] = pd.to_numeric(df_colab['rating'], errors='coerce')  # Coerce invalid parsing to NaN
    #df_colab = df_colab.dropna(subset=['rating'])  # Drop rows where 'rating' is NaN


    user_item_matrix = df_colab.pivot_table(
    index="reviewer",     # Rows: Reviewers
    columns="name",       # Columns: Beer names
    values="rating",      # Values: Ratings
    fill_value=0          # Fill missing ratings with 0
    )
    

    user_means = user_item_matrix.replace(0, np.nan).mean(axis=1).fillna(0).to_numpy()
    
    print(user_means)
    user_item_np = np.where(user_item_matrix != 0, user_item_matrix - user_means[:, None], 0)

    user_item_matrix = pd.DataFrame(user_item_np, index=user_item_matrix.index, columns=user_item_matrix.columns)


    # Compute cosine similarity
    #cosine_similarity = compute_cosine_similarity_manual(utility_matrix.values)
    cosine_similarity_matrix = cosine_similarity(user_item_matrix)
    
    # Predict ratings
    predicted_ratings = predict_ratings_user_based(user_item_matrix, cosine_similarity_matrix)

    pr_df = pd.DataFrame(predicted_ratings, index=user_item_matrix.index, columns=user_item_matrix.columns)
   
    return pr_df, user_item_matrix, cosine_similarity_matrix
