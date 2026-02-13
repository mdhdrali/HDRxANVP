import pandas as pd

# Load dataset
data = pd.read_csv("dataset/loan_data.csv")

# Show first 5 rows
data

# Show column names
print("\nColumns in dataset:")
print(data.columns)

# Show basic info
print("\nDataset Info:")
print(data.info())
