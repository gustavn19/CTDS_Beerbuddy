'''
This script will create embeddings for the user reviews using BERT model.
'''

from transformers import AutoTokenizer, AutoModel
import torch
import pandas as pd
import numpy as np
import sqlite3
import pickle

from get_data_from_db import get_df 

def main(save_embeddings=True):
    df = get_df()

    # Group by name
    # grouped_reviews = df.groupby("name")["review_text"].apply(list).to_dict()

    # Set device
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load pre-trained BERT model
    model = AutoModel.from_pretrained("bert-base-uncased").to(device)
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    def tokenize_reviews(reviews, max_length=128):
        """
        Tokenize reviews and prepare for BERT on MPS.
        """
        tokens = tokenizer(
            reviews,
            padding=True,            # Add padding to make sequences the same length
            truncation=True,         # Truncate sequences longer than max_length
            max_length=max_length,   # Limit sequence length
            return_tensors="pt"      # Return PyTorch tensors
        )
        # Move tensors to device (MPS)
        for key in tokens:
            tokens[key] = tokens[key].to(device)
        return tokens

    def generate_review_embeddings(reviews):
        """
        Generate BERT embeddings for a list of reviews.
        Returns a NumPy array of [CLS] token embeddings.
        """
        tokens = tokenize_reviews(reviews)
        with torch.no_grad():  # Disable gradient computation for faster inference
            outputs = model(**tokens)
        # Extract [CLS] token embeddings
        embeddings = outputs.last_hidden_state[:, 0, :]  # Shape: (num_reviews, embedding_dim)
        return embeddings.cpu().numpy()  # Move results back to CPU as a NumPy array

    # Dictionary to store review-level embeddings for each beer
    review_embeddings = {}

    for beer_id, reviews in grouped_reviews.items():
        if not reviews: # Skip beers with no reviews
            continue
        # Generate embeddings for all reviews of this beer
        review_embeddings[beer_id] = generate_review_embeddings(reviews)

    if save_embeddings:
        # Save review embeddings to a file
        save_path = "review_embeddings.pkl"
        with open(save_path, "wb") as f:
            pickle.dump(review_embeddings, f)
        print("Review embeddings have been saved to 'review_embeddings.pkl'.")
    else:
        print("Review embeddings have been computed but NOT saved.")

if __name__ == "__main__":
    main(save_embeddings=True)