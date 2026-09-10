print("5.---Number Analysis Tool---")
print("""Create a function that accepts a list and returns
        largest number
        smallest number
        total
        average
        even count
        odd count
        positive count
        negative 
        
        Do not use min(), max(), or sum()""")

numbers = [1,3,8,9,10]
def list_analysis(numbers):    
    # Initialize variables using the first element
    largest = numbers[0]
    smallest = numbers[0]

    total = 0
    even_count = 0
    odd_count = 0
    positive_count = 0
    negative_count = 0
    total_elements = 0

    # Process all numbers in a single pass
    for num in numbers:
        total += num
        total_elements += 1
        
        # Check largest and smallest
        if num > largest:
            largest = num
        if num < smallest:
            smallest = num
            
        # Check even and odd (integers only)
        if num % 2 == 0:
            even_count += 1
        else:
            odd_count += 1
                
        # Check positive and negative (0 is neither)
        if num > 0:
            positive_count += 1
        elif num < 0:
            negative_count += 1

    # Calculate average
    average = total / total_elements

    return (
        f"Largest: {largest}\n"
        f"Smallest: {smallest}\n"
        f"Total: {total}\n"
        f"Average: {average}\n"
        f"Even Count: {even_count}\n"
        f"Odd Count: {odd_count}\n"
        f"Positive Count: {positive_count}\n"
        f"Negative Count: {negative_count}"
    )

# calling function
print('Given List: ', numbers)
print(list_analysis(numbers))
