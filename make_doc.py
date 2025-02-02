import pandas as pd

df = pd.read_csv("data/s2_id_with_floodfw.csv")
result_df_combined = pd.read_csv("data/kmeans.csv")

# creating a csv with state, coordinates and the events and inertias
pd.DataFrame(pd.merge(df, result_df_combined, on='id')).to_csv('data/preprocessed.csv')
