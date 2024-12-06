# 🍺 Beer Recommendation System

Welcome to the **Beer Recommendation System** repository! This project was developed as part of the **02807 Computational Tools for Data Science** course at the Technical University of Denmark. The system provides personalized beer recommendations using advanced computational techniques and a robust dataset of beer reviews.

## 👩‍💻 Authors
- **Lucas Brylle**
- **Jacob Borregaard**
- **Jonathan Simonsen**
- **Gustav Louis Nielsen**

---

## 🌟 Project Overview

### 🎯 Motivation
Beer represents a rich world of flavors and styles. With thousands of beers and breweries globally, finding a beer that suits individual preferences can be daunting. This project aims to simplify the process by developing a system that not only recommends beers based on user preferences but also encourages exploration of new and exciting beer styles.

### ✨ Key Features
- **Personalized Recommendations**: Tailored suggestions based on user preferences.
- **Rich Dataset**: Data scraped from RateBeer.com, featuring over 1.15 million reviews covering 12,000 beers from 27 countries.
- **User-Centric Design**: Combines collaborative filtering and semantic analysis to ensure relevant and accurate recommendations.

---

## 🏗️ System Architecture

### 🛠️ Methods Used
1. **Natural Language Processing (NLP)**:
   - **Sentence-BERT (SBERT)**: Used to generate dense vector embeddings for beer reviews.
2. **Collaborative Filtering (CF)**:
   - Recommends beers by identifying similar user preferences based on ratings.
3. **Locality-Sensitive Hashing (LSH)**:
   - Efficient retrieval of similar beer reviews in high-dimensional spaces.
4. **Clustering (K-means)**:
   - Enhances the precision of LSH by creating smaller, more specific buckets of reviews.
5. **Dimensionality Reduction (t-SNE)**:
   - Used to visualize high-dimensional data.

### 🧰 Data Pipeline
1. **Web Scraping**:
   - Dynamic scraping of beer reviews and attributes from RateBeer.com using Selenium.
2. **Data Preprocessing**:
   - Filtering non-English reviews, handling duplicates, and normalizing data.
3. **Recommendation Pipeline**:
   - Embedding reviews with SBERT.
   - Bucketing using LSH.
   - Refining recommendations via clustering and collaborative filtering.

---
## 📊 Dataset
Our data can be found via this google drive: https://drive.google.com/file/d/1z6jXbr5YmATOfl35yrjt1qrfSd8kN3LJ/view?usp=drive_link
### 📜 Attributes
| Attribute       | Type   | Description                                   |
|------------------|--------|-----------------------------------------------|
| Name            | String | Name of the beer.                            |
| Brewery         | String | Name of the brewery.                         |
| Subgenre        | String | Beer category or type.                       |
| ABV             | Float  | Alcohol by volume (percentage).              |
| Location        | String | Reviewer’s location.                         |
| Rating          | Float  | User’s rating for the beer.                  |
| Average Rating  | Float  | Beer’s overall average rating.               |
| Reviewer        | String | Name of the reviewer.                        |
| Review Date     | Date   | Date of the review.                          |
| Review Text     | String | Detailed description of the beer.            |

### 🔍 Dataset Highlights
- **33,000 unique users**.
- **Detailed reviews** with a minimum of 75 words, ensuring high-quality content for analysis.

---

