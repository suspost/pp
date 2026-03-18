import os

os.makedirs("test_dir/sub_dir", exist_ok=True)

print(os.listdir("."))

print(os.getcwd())
