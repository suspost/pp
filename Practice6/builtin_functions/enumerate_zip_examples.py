names = ["Alice", "Bob", "Charlie"]
scores = [85, 90, 95]

for i, name in enumerate(names):
    print(i, name)

for name, score in zip(names, scores):
    print(name, score)
