import tkinter as tk
from tkinter import messagebox
from fabric import Fabric
from data import Data

fabrics = {
	"lab": {"address": "labapic.company.com", "fabric": None, "login": False},
	"dc1": {"address": "dc1apic.company.com", "fabric": None, "login": False},
	"dc2": {"address": "dc2apic.company.com", "fabric": None, "login": False}}


def fab_select_change(fab = None):
	if fab is None:
		fab = variable.get()
	if fabrics[fab]['login']:
		user_entry['bg'] = 'green'
		user_entry.delete(0, tk.END)
		user_entry.insert(0, fabrics[fab]['fabric'].apic.username)
		pass_entry['bg'] = 'green'
		pass_entry.delete(0, tk.END)
	else:
		user_entry['bg'] = "white"
		user_entry.delete(0, tk.END)
		pass_entry['bg'] = "white"
		pass_entry.delete(0, tk.END)
	user_entry.focus_set()


def key_up(e):
	if e.char == "\r":
		if e.widget is user_entry:
			pass_entry.focus_set()
		elif e.widget is pass_entry:
			login_to_fabric()


def post_data():
	fab = fabrics[variable.get()]['fabric']
	data = Data(data_text.get("1.0", tk.END))
	fab.post(data.json)


def login_to_fabric():
	fab = variable.get()
	user = user_entry.get().strip()
	passwd = pass_entry.get().strip()
	passwd = None if passwd == "" else passwd
	if fab in fabrics and user != "" and passwd != "":
		if fabrics[fab]['fabric'] is None:
			fabrics[fab]['fabric'] = Fabric(fabrics[fab]['address'])
		fabrics[fab]['login'] = fabrics[fab]['fabric'].login(user, passwd)
		if fabrics[fab]['login']:
			user_entry['bg'] = 'green'
			pass_entry['bg'] = 'green'
			data_text.focus_set()
		else:
			user_entry['bg'] = 'red'
			pass_entry['bg'] = 'red'
			messagebox.showerror("Alert", "Authentication Failed!")
			user_entry.focus_set()


gui_main = tk.Tk()
gui_main.title("ACI Post")
gui_main.geometry("800x600")

variable = tk.StringVar(gui_main)
variable.set("fabric")
fab_select = tk.OptionMenu(gui_main, variable, *list(fabrics.keys()), command=fab_select_change)
fab_select.place(x=10, y=10)

user_entry = tk.Entry(gui_main, width=12)
user_entry.bind("<KeyRelease>", key_up)
user_entry.place(x=110, y=10)

pass_entry = tk.Entry(gui_main, show="~", width=12)
pass_entry.bind("<KeyRelease>", key_up)
pass_entry.place(x=230, y=10)

login_button = tk.Button(gui_main, text="Login", command=lambda: login_to_fabric())
login_button.place(x=350, y=10)

post_button = tk.Button(gui_main, text="Post", state="disabled", command=post_data)
post_button.place(x=730, y=10)

data_text = tk.Text(gui_main, width=110, height=24, bg="grey")
data_text.place(x=10, y=40)
