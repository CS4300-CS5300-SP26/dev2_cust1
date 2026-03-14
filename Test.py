 while True:
        print("\nOperations: + | - | * | /  (or 'q' to quit)")
 
        try:
            a = input("Enter first number: ").strip()
            if a.lower() == "q":
                break
            a = float(a)
 
            op = input("Enter operator (+, -, *, /): ").strip()
            if op.lower() == "q":
                break
 
            b = input("Enter second number: ").strip()
            if b.lower() == "q":
                break
            b = float(b)
 
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
 
        if op == "+":
            result = add(a, b)
        elif op == "-":
            result = subtract(a, b)
        elif op == "*":
            result = multiply(a, b)
        elif op == "/":
            result = divide(a, b)
        else:
            print(f"Unknown operator '{op}'. Use +, -, *, or /")
            continue
 
        print(f"Result: {a} {op} {b} = {result}")
 
    print("Goodbye!")
 
if __name__ == "__main__":
    calculator()