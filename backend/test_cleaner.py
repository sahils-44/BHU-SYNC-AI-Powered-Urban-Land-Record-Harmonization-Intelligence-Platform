import pandas as pd

from services.cleaner import clean_dataset
from services.quality import calculate_quality_score


df = pd.read_csv("data/cadastral.csv")

print("\n===== ORIGINAL DATA =====")
print(df)

cleaned_df = clean_dataset(df)

print("\n===== CLEANED DATA =====")
print(cleaned_df)

score = calculate_quality_score(cleaned_df)

print("\n===== DATA QUALITY =====")
print(f"Quality Score: {score}%")