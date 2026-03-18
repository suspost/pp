import shutil
import os

shutil.copy("sample.txt", "sample_copy.txt")

if os.path.exists("sample_copy.txt"):
    os.remove("sample_copy.txt")
