# dates.py
# Working with datetime

from datetime import datetime, timedelta

# Current date and time
now = datetime.now()
print("Current:", now)

# Create specific date
birthday = datetime(2005, 5, 10)
print("Birthday:", birthday)

# Format date
formatted = now.strftime("%Y-%m-%d %H:%M")
print("Formatted:", formatted)

# Time difference
difference = now - birthday
print("Days lived:", difference.days)

# Add 7 days
future = now + timedelta(days=7)
print("After 7 days:", future)
