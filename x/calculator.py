import tkinter as tk

# Function to handle button clicks
def button_click(value):
    current = entry.get()
    entry.delete(0, tk.END)
    entry.insert(0, current + value)

# Function to clear the entry
def clear():
    entry.delete(0, tk.END)

# Function to evaluate the expression
def calculate():
    try:
        result = eval(entry.get())
        entry.delete(0, tk.END)
        entry.insert(0, str(result))
    except:
        entry.delete(0, tk.END)
        entry.insert(0, "Error")

# Create the main window
root = tk.Tk()
root.title("Calculator")

# Create the entry widget
entry = tk.Entry(root, width=30, borderwidth=5, justify="right", font=("Arial", 14))
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

# Button values
buttons = [
    "7", "8", "9", "/",
    "4", "5", "6", "*",
    "1", "2", "3", "-",
    "C", "0", "=", "+"
]

# Add buttons to the window
row, col = 1, 0
for button in buttons:
    if button == "=":
        btn = tk.Button(root, text=button, width=5, height=2, command=calculate)
    elif button == "C":
        btn = tk.Button(root, text=button, width=5, height=2, command=clear)
    else:
        btn = tk.Button(root, text=button, width=5, height=2, command=lambda b=button: button_click(b))
    btn.grid(row=row, column=col, padx=5, pady=5)
    col += 1
    if col > 3:
        col = 0
        row += 1

# Run the application
root.mainloop()
