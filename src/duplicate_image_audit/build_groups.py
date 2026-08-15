"""
Build animal/source-level group IDs from the duplicate audit, for GroupKFold.

Nothing is deleted. Every image is assigned to a group; images that are
near-duplicates of each other (or share a source stem) land in the same group,
so GroupKFold keeps them on the same side of every split.

Usage:
    python build_groups.py --data-root new_data --audit-dir . --out group_ids.csv
"""

import argparse, csv, glob, json, os, re
from collections import defaultdict

RF = re.compile(r"_jpg\.rf\.[0-9a-f]+\.(jpg|jpeg|png)$", re.I)
AUG = re.compile(r"^aug_\d+_")
XN = re.compile(r"_x\d+$")
CROP = re.compile(r"_\d+$")


def source_stem(filename):
    """Collapse a Roboflow filename to its original source image identity."""
    s = RF.sub("", filename)
    s = re.sub(r"\.(jpg|jpeg|png)$", "", s, flags=re.I)
    s = AUG.sub("", s)          # aug_0_1257_jpeg  -> 1257_jpeg
    s = re.sub(r"_jpe?g$", "", s, flags=re.I)
    s = XN.sub("", s)           # 1000010640_x16   -> 1000010640
    return s


def capture_stem(filename):
    """Further collapse multi-crop siblings (foo_1, foo_2) to one capture."""
    return CROP.sub("", source_stem(filename))


class Union:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        root = x
        while self.p[root] != root:
            root = self.p[root]
        while self.p[x] != root:
            self.p[x], x = root, self.p[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True,
                    help="folder containing train/ val/ test/ subfolders")
    ap.add_argument("--audit-dir", default=".",
                    help="folder holding the *_duplicates*.json files")
    ap.add_argument("--audit-glob", default="*_duplicates_2.json",
                    help="which audit files to load from --audit-dir. The _2 "
                         "generation was built against final_data; the "
                         "unsuffixed generation was built against new_data. "
                         "Mixing generations is usually wrong.")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="max distance to treat as the same group")
    ap.add_argument("--out", default="group_ids.csv")
    args = ap.parse_args()

    # 1. Inventory every image on disk.
    records = []          # (split, cls, filename, relpath)
    for split in ("train", "val", "test"):
        sdir = os.path.join(args.data_root, split)
        if not os.path.isdir(sdir):
            continue
        for cls in sorted(os.listdir(sdir)):
            cdir = os.path.join(sdir, cls)
            if not os.path.isdir(cdir):
                continue
            for fn in sorted(os.listdir(cdir)):
                if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                    records.append((split, cls, fn, f"{split}/{cls}/{fn}"))

    print(f"images on disk: {len(records)}")
    by_split = defaultdict(int)
    per_class = defaultdict(lambda: defaultdict(int))
    for split, cls, _, _ in records:
        by_split[split] += 1
        per_class[split][cls] += 1
    for s in ("train", "val", "test"):
        print(f"  {s:6s} {by_split[s]}")

    # 2. Seed the union-find with filename-derived identity. This is free and
    #    exact, and catches every Roboflow augmentation sibling.
    uf = Union()
    for split, cls, fn, rel in records:
        uf.union(rel, f"capture::{cls}::{capture_stem(fn)}")

    # 3. Merge in the perceptual/embedding audit pairs.
    root_anchor = os.path.basename(os.path.normpath(args.data_root))
    on_disk = {rel for _, _, _, rel in records}
    merged = skipped_unparsed = skipped_missing = 0

    # Discover the audit files rather than assuming fixed names. A missing file
    # used to be skipped in silence, which is indistinguishable from "every pair
    # was above threshold" -- both report 0 merges.
    audit_files = sorted(glob.glob(os.path.join(args.audit_dir, args.audit_glob)))
    if not audit_files:
        present = sorted(glob.glob(os.path.join(args.audit_dir, "*.json")))
        raise SystemExit(
            f"ERROR: no audit files match '{args.audit_glob}' in "
            f"{os.path.abspath(args.audit_dir)}\n"
            + (f"  that folder does contain: {[os.path.basename(p) for p in present]}\n"
               f"  pass --audit-glob to select one of those, or point --audit-dir elsewhere."
               if present else "  that folder contains no .json files at all."))

    print(f"audit files loaded from {os.path.abspath(args.audit_dir)}:")
    for path in audit_files:
        print(f"  {os.path.basename(path)}")

    for path in audit_files:
        for row in json.load(open(path)):
            a, b = (tolocal(row["image_a"], root_anchor),
                    tolocal(row["image_b"], root_anchor))
            if not (a and b):
                skipped_unparsed += 1
                continue
            if a not in on_disk or b not in on_disk:
                skipped_missing += 1
                continue
            ca, cb = a.split("/")[1], b.split("/")[1]
            limit = args.threshold if ca == cb else 0.01
            if row["distance"] > limit:
                continue
            uf.union(a, b)
            merged += 1
    print(f"audit pairs merged at distance<={args.threshold}: {merged}")
    if skipped_unparsed:
        print(f"  WARNING: {skipped_unparsed} pairs had paths that do not "
              f"contain a '{root_anchor}' segment and were ignored")
    if skipped_missing:
        print(f"  note: {skipped_missing} pairs reference files not on disk")

    # 4. Emit group IDs.
    groups = {}
    rows_out = []
    for split, cls, fn, rel in records:
        root = uf.find(rel)
        gid = groups.setdefault(root, f"g{len(groups):05d}")
        rows_out.append((rel, split, cls, fn, gid))

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["relpath", "orig_split", "label", "filename", "group_id"])
        w.writerows(rows_out)

    print(f"\ndistinct groups: {len(groups)}")
    print(f"effective sample size = {len(groups)} "
          f"(vs {len(records)} files, ratio {len(records)/max(len(groups),1):.2f}x)")

    # 5. Groups per class. This is the number that decides your fold count.
    gpc = defaultdict(set)
    for rel, split, cls, fn, gid in rows_out:
        gpc[cls].add(gid)
    print("\ngroups per class:")
    for cls in sorted(gpc, key=lambda c: len(gpc[c])):
        print(f"  {cls:16s} {len(gpc[cls]):5d} groups")
    smallest = min(len(v) for v in gpc.values())
    print(f"\nsmallest class has {smallest} groups -> "
          f"max safe n_splits = {min(5, smallest)}")

    # 6. Label conflicts: one group carrying more than one label.
    glabels = defaultdict(set)
    for rel, split, cls, fn, gid in rows_out:
        glabels[gid].add(cls)
    conflicts = {g: v for g, v in glabels.items() if len(v) > 1}
    print(f"\nLABEL CONFLICTS: {len(conflicts)} groups carry >1 label")
    for g, labs in sorted(conflicts.items())[:30]:
        members = [r for r in rows_out if r[4] == g]
        print(f"  {g}: {sorted(labs)}  ({len(members)} files)")
        for m in members[:4]:
            print(f"      {m[1]}/{m[2]}/{m[3][:55]}")
    print("\nThese are the ONLY files needing a human decision. "
          "Everything else just gets grouped.")


def tolocal(winpath, anchor=None):
    """Convert the audit's absolute Windows path to split/cls/filename.

    The audit JSONs store absolute paths from whatever machine produced them, so
    we locate the dataset root by name and keep the three segments after it. The
    anchor is the --data-root basename; matching is case-insensitive and takes
    the LAST occurrence, so a parent folder that happens to share the name (e.g.
    C:/Data/.../final_data) cannot hijack the match.
    """
    parts = winpath.replace("\\", "/").split("/")
    anchors = [a.lower() for a in ([anchor] if anchor else []) + ["final_data", "new_data", "data"] if a]
    lower = [p.lower() for p in parts]
    for a in anchors:
        idx = [i for i, p in enumerate(lower) if p == a]
        if idx:
            i = idx[-1]
            if len(parts) >= i + 4:
                return "/".join(parts[i + 1:i + 4])
    return None


if __name__ == "__main__":
    main()