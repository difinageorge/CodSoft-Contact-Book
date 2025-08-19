import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json, os, uuid, re, csv

DATA_FILE = "contacts.json"

# ----------------------- Data Layer -----------------------
def load_contacts():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        messagebox.showwarning("Warning", "Corrupt data file. Starting fresh.")
        return []

def save_contacts():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error", f"Could not save data:\n{e}")

# ----------------------- Validation -----------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[+\d][\d\s\-()]{5,}$")  # simple, flexible

def validate_fields(name, phone, email):
    if not name.strip():
        messagebox.showwarning("Validation", "Name cannot be empty.")
        return False
    if phone.strip() and not PHONE_RE.match(phone.strip()):
        messagebox.showwarning("Validation", "Phone looks invalid.\nTip: include digits, +, -, () or spaces.")
        return False
    if email.strip() and not EMAIL_RE.match(email.strip()):
        messagebox.showwarning("Validation", "Email looks invalid.")
        return False
    return True

# ----------------------- UI Helpers -----------------------
def clear_form():
    name_var.set("")
    phone_var.set("")
    email_var.set("")
    address_txt.delete("1.0", tk.END)
    contact_list.selection_remove(contact_list.selection())
    add_btn.config(text="Add")
    status_var.set("Ready")

def populate_form(item_id):
    c = next((c for c in contacts if c["id"] == item_id), None)
    if not c: 
        return
    name_var.set(c["name"])
    phone_var.set(c["phone"])
    email_var.set(c["email"])
    address_txt.delete("1.0", tk.END)
    address_txt.insert(tk.END, c["address"])

def selected_id():
    sel = contact_list.selection()
    if not sel: 
        return None
    return contact_list.item(sel[0], "values")[0]  # id stored in hidden col

def refresh_list():
    query = search_var.get().strip().lower()
    for i in contact_list.get_children():
        contact_list.delete(i)
    for c in contacts:
        hay = f"{c['name']} {c['phone']} {c['email']} {c['address']}".lower()
        if query in hay:
            contact_list.insert(
                "", tk.END,
                values=(c["id"], c["name"], c["phone"], c["email"])
            )
    status_var.set(f"Showing {len(contact_list.get_children())} / {len(contacts)}")

# ----------------------- Actions -----------------------
def add_or_save():
    name = name_var.get()
    phone = phone_var.get()
    email = email_var.get()
    address = address_txt.get("1.0", tk.END).strip()

    if not validate_fields(name, phone, email):
        return

    sid = selected_id()
    if sid:
        # Update existing
        for c in contacts:
            if c["id"] == sid:
                c["name"] = name.strip()
                c["phone"] = phone.strip()
                c["email"] = email.strip()
                c["address"] = address
                break
        save_contacts()
        refresh_list()
        status_var.set("Contact updated ✅")
        add_btn.config(text="Add")
    else:
        # Add new
        new_c = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "address": address
        }
        contacts.append(new_c)
        save_contacts()
        refresh_list()
        status_var.set("Contact added ✅")

    clear_form()

def on_select(event):
    sid = selected_id()
    if sid:
        populate_form(sid)
        add_btn.config(text="Save")

def delete_contact():
    sid = selected_id()
    if not sid:
        messagebox.showinfo("Info", "Please select a contact to delete.")
        return
    c = next((c for c in contacts if c["id"] == sid), None)
    if not c:
        return
    if messagebox.askyesno("Confirm", f"Delete '{c['name']}'?"):
        contacts[:] = [x for x in contacts if x["id"] != sid]
        save_contacts()
        refresh_list()
        clear_form()
        status_var.set("Contact deleted 🗑️")

def export_csv():
    if not contacts:
        messagebox.showinfo("Info", "No contacts to export.")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Export Contacts to CSV"
    )
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name", "Phone", "Email", "Address"])
            for c in contacts:
                w.writerow([c["name"], c["phone"], c["email"], c["address"]])
        messagebox.showinfo("Export", "Contacts exported successfully ✅")
    except Exception as e:
        messagebox.showerror("Error", f"Export failed:\n{e}")

def import_csv():
    path = filedialog.askopenfilename(
        filetypes=[("CSV Files", "*.csv")],
        title="Import Contacts from CSV"
    )
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            headers = next(r, None)
            for row in r:
                if not row: 
                    continue
                name, phone, email, address = (row + ["", "", "", ""])[:4]
                if not name.strip():
                    continue
                # avoid dup by (name, phone, email)
                dup = next((c for c in contacts if c["name"] == name and c["phone"] == phone and c["email"] == email), None)
                if dup: 
                    continue
                contacts.append({
                    "id": str(uuid.uuid4()),
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "address": address.strip(),
                })
        save_contacts()
        refresh_list()
        status_var.set("Contacts imported from CSV 📥")
    except Exception as e:
        messagebox.showerror("Error", f"Import failed:\n{e}")

def new_contact():
    clear_form()
    add_btn.config(text="Add")
    status_var.set("Creating new contact…")

def copy_email():
    sid = selected_id()
    if not sid:
        messagebox.showinfo("Info", "Select a contact first.")
        return
    c = next((c for c in contacts if c["id"] == sid), None)
    if c and c["email"]:
        root.clipboard_clear()
        root.clipboard_append(c["email"])
        status_var.set("Email copied to clipboard 📋")

# ----------------------- Theme (Day/Night) -----------------------
DAY = {
    "bg": "#f6f8fa",
    "card": "#ffffff",
    "fg": "#1f2937",
    "muted": "#6b7280",
    "accent": "#2563eb",
    "danger": "#dc2626",
    "entry_bg": "#ffffff",
}

NIGHT = {
    "bg": "#0f172a",
    "card": "#111827",
    "fg": "#e5e7eb",
    "muted": "#94a3b8",
    "accent": "#60a5fa",
    "danger": "#f87171",
    "entry_bg": "#0b1220",
}

theme = DAY

def apply_theme():
    root.configure(bg=theme["bg"])
    for w in (header, form_frame, list_frame, actions_frame, bottom_bar):
        w.configure(bg=theme["bg"])
    for w in (card, form_card):
        w.configure(bg=theme["card"], highlightbackground=theme["muted"], highlightcolor=theme["muted"])
    title_lbl.configure(bg=theme["bg"], fg=theme["fg"])
    # Labels
    for lbl in (name_lbl, phone_lbl, email_lbl, address_lbl, search_lbl):
        lbl.configure(bg=theme["card"], fg=theme["fg"])
    # Entries
    for e in (name_ent, phone_ent, email_ent, search_ent):
        e.configure(bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
    address_txt.configure(bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
    # Buttons
    add_btn.configure(bg=theme["accent"], fg="white", activebackground=theme["accent"])
    new_btn.configure(bg=theme["card"], fg=theme["fg"], activebackground=theme["entry_bg"])
    del_btn.configure(bg=theme["danger"], fg="white", activebackground=theme["danger"])
    copy_btn.configure(bg=theme["card"], fg=theme["fg"])
    export_btn.configure(bg=theme["card"], fg=theme["fg"])
    import_btn.configure(bg=theme["card"], fg=theme["fg"])
    theme_btn.configure(bg=theme["card"], fg=theme["fg"])
    # Treeview styling
    style.configure("Treeview",
                    background=theme["card"],
                    fieldbackground=theme["card"],
                    foreground=theme["fg"])
    style.configure("Treeview.Heading",
                    background=theme["card"],
                    foreground=theme["muted"])
    style.map("Treeview",
              background=[("selected", theme["accent"])],
              foreground=[("selected", "white")])
    # Status
    status_lbl.configure(bg=theme["bg"], fg=theme["muted"])

def toggle_theme():
    global theme
    theme = NIGHT if theme is DAY else DAY
    theme_btn.configure(text="🌞 Day" if theme is NIGHT else "🌙 Night")
    apply_theme()

# ----------------------- App -----------------------
contacts = load_contacts()

root = tk.Tk()
root.title("📒 Contact Book")
root.geometry("860x560")
root.minsize(820, 520)

style = ttk.Style()
style.theme_use("clam")

# Header
header = tk.Frame(root, pady=8)
header.pack(fill="x")
title_lbl = tk.Label(header, text="Contact Book", font=("Segoe UI Semibold", 20))
title_lbl.pack(side="left", padx=12)

theme_btn = tk.Button(header, text="🌙 Night", font=("Segoe UI", 10), relief="flat", width=10, command=toggle_theme)
theme_btn.pack(side="right", padx=12)

# Main layout: left (form) + right (list)
card = tk.Frame(root, bd=1, relief="solid")
card.pack(fill="both", expand=True, padx=12, pady=8)

form_frame = tk.Frame(card, padx=12, pady=12)
form_frame.pack(side="left", fill="y")

form_card = tk.Frame(form_frame, bd=1, relief="solid", padx=12, pady=12)
form_card.pack(fill="y")

# --- Form fields
name_lbl = tk.Label(form_card, text="Name")
name_var = tk.StringVar()
name_ent = tk.Entry(form_card, textvariable=name_var, font=("Segoe UI", 11), width=28)

phone_lbl = tk.Label(form_card, text="Phone")
phone_var = tk.StringVar()
phone_ent = tk.Entry(form_card, textvariable=phone_var, font=("Segoe UI", 11), width=28)

email_lbl = tk.Label(form_card, text="Email")
email_var = tk.StringVar()
email_ent = tk.Entry(form_card, textvariable=email_var, font=("Segoe UI", 11), width=28)

address_lbl = tk.Label(form_card, text="Address")
address_txt = tk.Text(form_card, height=5, font=("Segoe UI", 11), width=28)

name_lbl.grid(row=0, column=0, sticky="w", pady=(0,4))
name_ent.grid(row=1, column=0, sticky="we", pady=(0,8))
phone_lbl.grid(row=2, column=0, sticky="w", pady=(0,4))
phone_ent.grid(row=3, column=0, sticky="we", pady=(0,8))
email_lbl.grid(row=4, column=0, sticky="w", pady=(0,4))
email_ent.grid(row=5, column=0, sticky="we", pady=(0,8))
address_lbl.grid(row=6, column=0, sticky="w", pady=(0,4))
address_txt.grid(row=7, column=0, sticky="we")

# Form actions
actions_frame = tk.Frame(form_frame, pady=10)
actions_frame.pack(fill="x")

add_btn = tk.Button(actions_frame, text="Add", font=("Segoe UI", 10, "bold"), relief="flat", width=12, command=add_or_save)
new_btn = tk.Button(actions_frame, text="New", font=("Segoe UI", 10), relief="flat", width=10, command=new_contact)
del_btn = tk.Button(actions_frame, text="Delete", font=("Segoe UI", 10), relief="flat", width=10, command=delete_contact)
copy_btn = tk.Button(actions_frame, text="Copy Email", font=("Segoe UI", 10), relief="flat", width=12, command=copy_email)

add_btn.grid(row=0, column=0, padx=4, pady=2, sticky="w")
new_btn.grid(row=0, column=1, padx=4, pady=2, sticky="w")
del_btn.grid(row=0, column=2, padx=4, pady=2, sticky="w")
copy_btn.grid(row=0, column=3, padx=4, pady=2, sticky="w")

# Right side: list + search
list_frame = tk.Frame(card, padx=12, pady=12)
list_frame.pack(side="right", fill="both", expand=True)

search_lbl = tk.Label(list_frame, text="Search")
search_var = tk.StringVar()
search_ent = tk.Entry(list_frame, textvariable=search_var, font=("Segoe UI", 11))

search_lbl.pack(anchor="w")
search_ent.pack(fill="x", pady=(0,8))
search_ent.bind("<KeyRelease>", lambda e: refresh_list())

# Treeview (contacts table)
cols = ("id", "name", "phone", "email")
contact_list = ttk.Treeview(list_frame, columns=cols, show="headings", height=16)
contact_list.heading("name", text="Name")
contact_list.heading("phone", text="Phone")
contact_list.heading("email", text="Email")
contact_list.column("id", width=0, stretch=False)     # hidden id
contact_list.column("name", width=220)
contact_list.column("phone", width=140)
contact_list.column("email", width=220)

scroll_y = ttk.Scrollbar(list_frame, orient="vertical", command=contact_list.yview)
contact_list.configure(yscrollcommand=scroll_y.set)

contact_list.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

contact_list.bind("<<TreeviewSelect>>", on_select)
contact_list.bind("<Double-1>", on_select)

# Bottom bar
bottom_bar = tk.Frame(root, pady=6)
bottom_bar.pack(fill="x")

export_btn = tk.Button(bottom_bar, text="Export CSV", font=("Segoe UI", 10), relief="flat", command=export_csv)
import_btn = tk.Button(bottom_bar, text="Import CSV", font=("Segoe UI", 10), relief="flat", command=import_csv)
status_var = tk.StringVar(value="Ready")
status_lbl = tk.Label(bottom_bar, textvariable=status_var, font=("Segoe UI", 9))

export_btn.pack(side="left", padx=12)
import_btn.pack(side="left")
status_lbl.pack(side="right", padx=12)

# Initial paint
apply_theme()
refresh_list()

root.mainloop()
