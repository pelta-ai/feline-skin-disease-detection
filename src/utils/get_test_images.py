import pandas as pd
g = pd.read_csv("src/duplicate_image_audit/group_ids.csv")
print(g[g.orig_split == "test"].groupby("label").size())