# generators.py
# Iterator and Generator examples

# ----- Iterator example -----
numbers = [1, 2, 3]
my_iter = iter(numbers)

print(next(my_iter))  # 1
print(next(my_iter))  # 2
print(next(my_iter))  # 3

# ----- Custom Generator -----
def count_up_to(n):
    count = 1
    while count <= n:
        yield count
        count += 1

for number in count_up_to(5):
    print(number)

# ----- Generator Expression -----
squares = (x * x for x in range(5))
for s in squares:
    print(s)
