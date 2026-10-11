"""
Expense Tracker

Structure:
- Header frame: Title (left) + Analytics button (right)
- Input frame: Category / Amount / Date / Add button
- List frame: Expenses listbox + Total
- Controls frame: Delete / Save
- Filter frame: Date filter + Show/Clear
- Analytics opens a Toplevel window (charts use current displayed view)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
import csv
from datetime import datetime, date

# -------------------------
# Data storage
# -------------------------
expenses = []            # master list of expense dicts
displayed_expenses = []  # current view (full or filtered)

# -------------------------
# Utility: refresh listbox from a provided list
# -------------------------
def refresh_expense_list(source_list):
    """
    Refresh the listbox using the provided list of expenses.
    Update displayed_expenses to keep mapping (listbox index -> expense).
    """
    global displayed_expenses
    displayed_expenses = source_list.copy()
    expense_list.delete(0, tk.END)
    for e in displayed_expenses:
        line = f"{e['date']} ({e['weekday']}) — {e['category']} — RM{e['amount']:.2f}"
        expense_list.insert(tk.END, line)

# -------------------------
# Add expense
# -------------------------
def add_expense():
    category = category_entry.get().strip()
    amount_str = amount_entry.get().strip()
    date_str = date_entry.get().strip()

    if category == "":
        messagebox.showerror("Error", "Category cannot be empty.")
        return

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except:
        messagebox.showerror("Error", "Amount must be a positive number.")
        return

    if date_str == "":
        date_obj = date.today()
    else:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
            return

    expense = {
        "category": category,
        "amount": amount,
        "date": date_obj.isoformat(),
        "weekday": date_obj.strftime("%A")
    }

    expenses.append(expense)

    # After adding an item, show the unfiltered master list
    refresh_expense_list(expenses)
    update_total()
# -------------------------
# Calculate average daily expense for the current month
# -------------------------
def calculate_average_monthly_expense():
    """
    Calculate the average daily expense for the current month
    based on the master expenses list.
    """
    if not expenses:
        return 0.0

    today = date.today()
    current_year = today.year
    current_month = today.month

    # Filter expenses for the current month
    monthly_expenses = [
        e for e in expenses
        if datetime.strptime(e['date'], "%Y-%m-%d").year == current_year
        and datetime.strptime(e['date'], "%Y-%m-%d").month == current_month
    ]

    if not monthly_expenses:
        return 0.0

    total = sum(e['amount'] for e in monthly_expenses)

    # Count unique days with expenses
    unique_days = set(e['date'] for e in monthly_expenses)

    average = total / len(unique_days)
    return average
    
    # clear inputs
    category_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    date_entry.delete(0, tk.END)

# -------------------------
# Delete selected
# -------------------------
def delete_selected():
    sel = expense_list.curselection()
    if not sel:
        messagebox.showwarning("No selection", "Please select an expense to delete.")
        return
    idx = sel[0]
    selected = displayed_expenses[idx]
    confirm = messagebox.askyesno("Confirm Delete",
                                  f"Delete: {selected['date']} - {selected['category']} - RM{selected['amount']:.2f}?")
    if confirm:
        try:
            expenses.remove(selected)
        except ValueError:
            # fallback: match by fields
            for e in expenses:
                if e['date'] == selected['date'] and e['category'] == selected['category'] and e['amount'] == selected['amount']:
                    expenses.remove(e)
                    break
        # refresh view to master list after deletion
        refresh_expense_list(expenses)
        update_total()

# -------------------------
# Update total (for displayed_expenses)
# -------------------------
def update_total():
    total = sum(e['amount'] for e in displayed_expenses)
    total_label.config(text=f"Total: RM {total:.2f}")

# -------------------------
# CSV Save (master list)
# -------------------------
def save_csv():
    if not expenses:
        messagebox.showinfo("Info", "No expenses to save.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date","Weekday","Category","Amount"])
            for e in expenses:
                writer.writerow([e['date'], e['weekday'], e['category'], f"{e['amount']:.2f}"])
        messagebox.showinfo("Saved", f"Saved to: {path}")
    except Exception as ex:
        messagebox.showerror("Error", f"Save failed: {ex}")

# -------------------------
# Date filter functions
# -------------------------
def apply_date_filter():
    date_text = filter_date_entry.get().strip()
    if date_text == "":
        messagebox.showinfo("Info", "Enter date YYYY-MM-DD or click Clear.")
        return
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except:
        messagebox.showerror("Error", "Date must be YYYY-MM-DD.")
        return
    filtered = [e for e in expenses if e['date'] == date_text]
    if not filtered:
        messagebox.showinfo("No data", f"No expenses for {date_text}.")
    refresh_expense_list(filtered)
    update_total()

def clear_date_filter():
    filter_date_entry.delete(0, tk.END)
    refresh_expense_list(expenses)
    update_total()

# -------------------------
# Charting (used by analytics window)
# -------------------------
def show_chart_for_data(chart_type):
    if not displayed_expenses:
        messagebox.showinfo("Info", "No data to chart.")
        return
    # aggregate by category
    totals = {}
    for e in displayed_expenses:
        totals[e['category']] = totals.get(e['category'], 0) + e['amount']
    labels = list(totals.keys())
    amounts = list(totals.values())

    plt.figure(figsize=(6,5))
    if chart_type == "Pie":
        plt.pie(amounts, labels=labels, autopct="%1.1f%%")
        plt.title("Expenses by Category (Pie)")
    elif chart_type == "Bar":
        plt.bar(labels, amounts, color="skyblue")
        plt.title("Expenses by Category (Bar)")
        plt.ylabel("RM")
        plt.xticks(rotation=30)
    elif chart_type == "Line":
        plt.plot(labels, amounts, marker='o', linestyle='-', color='green')
        plt.title("Expenses by Category (Line)")
        plt.ylabel("RM")
        plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()

# -------------------------
# Analytics window
# -------------------------
def open_analytics_window():
    win = tk.Toplevel(root)
    win.title("Analytics")
    win.geometry("380x220")

    # Header
    tk.Label(win, text="Analytics", font=("Arial", 14, "bold")).pack(pady=8)

    # Chart type selection
    tk.Label(win, text="Chart Type:").pack(pady=(6,0))
    local_chart_cb = ttk.Combobox(win, values=["Pie","Bar","Line"], state="readonly")
    local_chart_cb.pack(pady=6)
    local_chart_cb.current(0)

    # Show chart
    def local_show():
        show_chart_for_data(local_chart_cb.get())
    tk.Button(win, text="Show Chart", command=local_show, bg="#2196F3", fg="white").pack(pady=6)

    # Quick note
    tk.Label(win, text="Charts reflect current view (date filter if applied).", font=("Arial",9)).pack(pady=6)

    # Close
    tk.Button(win, text="Close", command=win.destroy).pack(pady=6)

# -------------------------
# BUILD GUI (structured frames)
# -------------------------
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("520x760")

# ----- Header frame: title left, Analytics button right -----
header_frame = tk.Frame(root)
header_frame.pack(fill=tk.X, padx=12, pady=10)

title_label = tk.Label(header_frame, text="Daily Expense Tracker", font=("Arial", 18, "bold"))
title_label.pack(side=tk.LEFT)

# Analytics button on the right of header (top-right)
analytics_btn = tk.Button(header_frame, text="Analytics", command=open_analytics_window, bg="#FF9800", fg="white")
analytics_btn.pack(side=tk.RIGHT)

# ----- Input frame: category, amount, date, add button -----
input_frame = tk.LabelFrame(root, text="Add Expense", padx=10, pady=8)
input_frame.pack(fill=tk.X, padx=12, pady=(0,10))

tk.Label(input_frame, text="Category:").grid(row=0, column=0, sticky=tk.W)
category_entry = tk.Entry(input_frame, width=28)
category_entry.grid(row=0, column=1, padx=6, pady=4)

tk.Label(input_frame, text="Amount (RM):").grid(row=1, column=0, sticky=tk.W)
amount_entry = tk.Entry(input_frame, width=28)
amount_entry.grid(row=1, column=1, padx=6, pady=4)

tk.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W)
date_entry = tk.Entry(input_frame, width=28)
date_entry.grid(row=2, column=1, padx=6, pady=4)

add_btn = tk.Button(input_frame, text="Add Expense", command=add_expense, bg="#4CAF50", fg="white")
add_btn.grid(row=3, column=0, columnspan=2, pady=8)

# ----- List frame: listbox + scrollbar -----
list_frame = tk.LabelFrame(root, text="Expenses", padx=6, pady=6)
list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,10))

# scrollbar + listbox
scrollbar = tk.Scrollbar(list_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

expense_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=70, height=18)
expense_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=expense_list.yview)

# ----- Total label under list -----
total_label = tk.Label(root, text="Total: RM 0.00", font=("Arial", 12, "bold"))
total_label.pack(pady=(4,12))

# ----- Controls frame: delete + save -----
controls_frame = tk.Frame(root)
controls_frame.pack(fill=tk.X, padx=12, pady=(0,12))

delete_btn = tk.Button(controls_frame, text="Delete Selected", command=delete_selected, fg="white", bg="#F44336")
delete_btn.pack(side=tk.LEFT, padx=(0,8))

save_btn = tk.Button(controls_frame, text="Save Full List to CSV", command=save_csv, bg="#2196F3", fg="white")
save_btn.pack(side=tk.LEFT)

# ----- Filter frame: filter entry + show/clear -----
filter_frame = tk.LabelFrame(root, text="Filter", padx=6, pady=6)
filter_frame.pack(fill=tk.X, padx=12, pady=(0,12))

tk.Label(filter_frame, text="Filter by Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W)
filter_date_entry = tk.Entry(filter_frame, width=22)
filter_date_entry.grid(row=0, column=1, padx=6)

filter_show_btn = tk.Button(filter_frame, text="Show", command=apply_date_filter)
filter_show_btn.grid(row=0, column=2, padx=(6,4))

filter_clear_btn = tk.Button(filter_frame, text="Clear", command=clear_date_filter)
filter_clear_btn.grid(row=0, column=3)

# Initial view
refresh_expense_list(expenses)
update_total()

root.mainloop()