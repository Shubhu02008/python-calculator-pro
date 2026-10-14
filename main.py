from calculator import calculate


def main():
    """Run the interactive command-line calculator."""
    print("===== Python Calculator Pro =====")

    while True:
        print("\nChoose an option:")
        print("1. Add")
        print("2. Subtract")
        print("3. Multiply")
        print("4. Divide")
        print("5. Evaluate an expression")
        print("0. Exit")

        choice = input("Your choice: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        if choice == "5":
            expression = input("Enter an expression: ")
            try:
                print("Result:", calculate(expression))
            except (ValueError, TypeError, IndexError, ZeroDivisionError) as error:
                print("Error:", error)
            continue

        operations = {
            "1": ("add", "add"),
            "2": ("subtract", "subtract"),
            "3": ("multiply", "multiply"),
            "4": ("divide", "divide"),
        }

        if choice not in operations:
            print("Invalid choice. Please choose 0, 1, 2, 3, 4, or 5.")
            continue

        operation, label = operations[choice]
        raw_numbers = input(
            f"Enter numbers to {label}, separated by spaces: "
        ).split()

        if not raw_numbers:
            print("Error: Please enter at least one number.")
            continue

        try:
            numbers = [float(value) for value in raw_numbers]
            if operation in {"subtract", "divide"} and len(numbers) < 2:
                print("Error: Please enter at least two numbers.")
                continue

            result = calculate(operation, numbers)
            print("Result:", result)
        except ValueError:
            print("Error: Please enter valid numbers.")
        except (TypeError, IndexError, ZeroDivisionError) as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
