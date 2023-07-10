import pandas as pd

# Read the Excel file
file_path = "machine learning jobs.xlsx"
df = pd.read_excel(file_path)

# Remove duplicates from the "Job title" column
df.drop_duplicates(subset="Job title", inplace=True)

# Save the updated file
updated_file_path = "updated machine learning jobs.xlsx"
df.to_excel(updated_file_path, index=False)

print("Duplicates removed and updated file saved successfully.")
