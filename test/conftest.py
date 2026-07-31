import os, sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# src/ so the modules under test can import each other as top-level packages
# (utils.constants, duplicate_image_audit.feature_extractor), and the project
# root so tests can use the src.* prefix.
for path in (os.path.join(PROJECT_ROOT, "src"), PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
