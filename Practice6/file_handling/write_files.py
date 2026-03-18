with open("sample.txt", "w") as f:
    f.write("Hello\nThis is a test file\n")

with open("sample.txt", "a") as f:
    f.write("Appended line\n")

with open("sample.txt", "r") as f:
    print(f.read())
