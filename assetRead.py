import pandas as pd

df = pd.read_csv('assetTypes.csv')
print(df['Item Category'].head)