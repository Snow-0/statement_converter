from datetime import datetime

# Input string representing date and time
date_string = "2023-01-15 08:30:00"

# Convert string to datetime object
dt_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

# Format datetime object as MM/DD/YY
formatted_date = dt_object.strftime("%m/%d/%y")

# Print the result
print("Formatted date:", formatted_date)
