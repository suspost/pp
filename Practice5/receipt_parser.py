# Receipt Parser using regex
import re

text = open("raw.txt").read()

prices = re.findall(r"\d+\.\d{2}", text)
print("Prices:", prices)

dates = re.findall(r"\d{2}\.\d{2}\.\d{4}", text)
print("Dates:", dates)
