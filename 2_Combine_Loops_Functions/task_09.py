
print("9. ---Prime Number Analyzer--- ")
print("""Take two numbers representing a range.
        Create functions to
                find prime numbers
                count primes
                calculate their sum
                display the largest prime found""")

def is_prime(n):
    """Helper function to check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def analyze_prime_range(start, end):
    # Ensure start is less than or equal to end
    if start > end:
        start, end = end, start

    # Collect primes in the given range
    primes = []
    for num in range(start, end + 1):
        if is_prime(num):
            primes.append(num)

    # Initialize tracking variables without using built-in functions
    prime_count = 0
    prime_sum = 0
    largest_prime = "None"

    # Process the primes to find count, sum, and largest
    for prime in primes:
        prime_count += 1
        prime_sum += prime
        # Since the loop moves upward, the last one found is automatically the largest
        largest_prime = prime

    # Prepare data rows
    output_data = [
                f"Prime Numbers Found: {primes}",
                f"Total Count of Primes: {prime_count}",
                f"Sum of Primes: {prime_sum}",
                f"Largest Prime Found: {largest_prime}"
                ]

    # Use map() to join each element onto a new line
    return "\n".join(map(str, output_data))

# --- Example Usage ---
# Finding primes between 10 and 50
start_input=int(input("Enter first number:"))
end_input=int(input("Enter another number: "))
#print(analyze_prime_range(10, 30))
print(analyze_prime_range(start_input, end_input))
