import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def predict_ratings_user_based(user_item_matrix, similarity_matrix):
    # Convert to a numpy array for computation
    user_item_matrix = user_item_matrix.values

    # Compute mean ratings for each user
    user_means = np.ma.masked_equal(user_item_matrix, 0).mean(axis=1).filled(0)
    
    # Center the matrix by subtracting user means
    ratings_diff = user_item_matrix - user_means[:, None]
    ratings_diff[np.isnan(ratings_diff)] = 0  # Replace NaN deviations with 0

    # Compute predictions
    similarity_sum = np.abs(similarity_matrix).sum(axis=1)[:, None]
    pred = user_means[:, None] + np.dot(similarity_matrix, ratings_diff) / (similarity_sum + 1e-8)



    return pred

def collaborative_filtering(df, drop_cols = ["brewery", "subgenre", "abv"]):
    df_colab = df.drop(drop_cols, axis=1)
    
    user_item_matrix = df.pivot_table(
    index="reviewer",     # Rows: Reviewers
    columns="name",       # Columns: Beer names
    values="rating",      # Values: Ratings
    fill_value=0          # Fill missing ratings with 0
    )
    

    # Compute cosine similarity
    #cosine_similarity = compute_cosine_similarity_manual(utility_matrix.values)
    cosine_similarity_matrix = cosine_similarity(user_item_matrix)
    

    predicted_ratings = predict_ratings_user_based(user_item_matrix, cosine_similarity_matrix)

    predicted_ratings_df = pd.DataFrame(
    predicted_ratings,
    index=user_item_matrix.index,
    columns=user_item_matrix.columns
    )
    # Predict ratings
    
    return predicted_ratings_df
