from functools import reduce

nums = [1, 2, 3, 4, 5]

squared = list(map(lambda x: x**2, nums))
print(squared)

even = list(filter(lambda x: x % 2 == 0, nums))
print(even)

total = reduce(lambda x, y: x + y, nums)
print(total)
