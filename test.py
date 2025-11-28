def get_lists():
    list_one = [1, 2, 3]
    list_two = ['a', 'b', 'c']
    # Return both lists separated by a comma.
    # Python internally treats this as a tuple (list_one, list_two)
    return list_one, list_two

# Call the function and unpack the results into two variables
numbers = get_lists()

print(f"Numbers: {numbers}")
print(f"Letters: {letters}")
