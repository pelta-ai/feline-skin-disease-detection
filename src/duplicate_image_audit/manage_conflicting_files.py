import os, re, glob

STEMS = [
    "1000010640_x16",
    "1af1e05f9bea841e74c3ef58a2aa86841c3b929c_jpeg",
    "flea_allergy-24-",
    "1000010696_x4",
    "54",
    "1000011983_x4",
    "A332365_1_En_4_Fig38_HTML_x4",
]

DELETE = True
pattern = re.compile(
    r"^(" + "|".join(re.escape(s) for s in STEMS) + r")_jpg\.rf\.[0-9a-zA-Z]+\.jpe?g$",
    re.IGNORECASE,
)

hits = []
for p in glob.glob("final_data/*/*/*.*"):
    if pattern.match(os.path.basename(p)):
        hits.append(p)

for p in sorted(hits):
    print(("DELETED  " if DELETE else "would delete  ") + p)
    if DELETE:
        os.remove(p)

print(f"\ntotal: {len(hits)} files")