import pandas as pd
import numpy as np

# TODO inkorporer ratings på en smart måde
# TODO Lav hvor man ud fra en helt profil af ratings finder reccomendation

def apriori_reccomender(df, s1, beer_col = "name", group_col = "reviewer_profile", verbose = False):
    # Hacky way to only look a highly rated beers
    df_good = df[df["rating"] >= 2.5]
    
    # Get list of beer rated by each user
    profiles = [list(set(a[1][beer_col].tolist())) for a in list(df_good.groupby(group_col))]
    beers = set(list(np.concatenate(profiles).flat))
    # Pass 1: hash singletons
    df_beer_hash = pd.DataFrame(range(len(beers)), index = list(beers), columns =['hashcode'], dtype=int)

    # count the beers, store the count in hashed array index
    beer_count_arr = np.zeros((len(beers),1))

    for b in profiles:
        for beer in b:
                idx = df_beer_hash.loc[beer,'hashcode']
                beer_count_arr[idx] += 1
                
    ### find frequent beers with support > s1       
    freq_beers  = [df_beer_hash[df_beer_hash['hashcode']==x].index[0] for x in np.where(beer_count_arr > s1*len(profiles))[0]] 
    if verbose == True:
        print(f"Frequent beers with support > {s1}:")
        for beer in freq_beers:
            print(beer)
    
    # Hash freequent beers
    df_freq_beers_hash = pd.DataFrame(range(1,len(freq_beers)+1), index=freq_beers, columns=['hashcode'])

    # count the pairs using only frequent beers
    pair_mat_hashed = np.zeros((len(freq_beers)+1,len(freq_beers)+1))

    for b in profiles:
        cand_list = [beer for beer in b if beer in freq_beers]
        if len(cand_list)<2:
            continue
        for idx, beer1 in enumerate(cand_list):
            for beer2 in cand_list[idx+1:]:
                i = df_freq_beers_hash.loc[beer1,'hashcode'] 
                j = df_freq_beers_hash.loc[beer2,'hashcode'] 
                pair_mat_hashed[max(i,j),min(i,j)]+=1

    freq_pairs = [[str(df_freq_beers_hash[df_freq_beers_hash['hashcode'] == x].index[0]),
                   str(df_freq_beers_hash[df_freq_beers_hash['hashcode'] == y].index[0])]
                  for x, y in zip(*np.where(pair_mat_hashed > s1 * len(profiles)))]

    if verbose == True:
        print(f"Frequent pairs with support > {s1}:")
        for pair in freq_pairs:
            beer1, beer2 = pair
            print(beer1, "and", beer2)

    # Create dictionary to look up beers
    beer_pair_dict = {}
    for beer1, beer2 in freq_pairs:
        if beer1 not in beer_pair_dict:
            beer_pair_dict[beer1] = []
        if beer2 not in beer_pair_dict:
            beer_pair_dict[beer2] = []
        
        beer_pair_dict[beer1].append(beer2)
        beer_pair_dict[beer2].append(beer1)

    return beer_pair_dict


    