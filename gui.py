import tkinter as tk
import json
from tkinter import messagebox
from fabric import Fabric
from data import Data, json_to_xml

file = open('fabrics.txt')
txt = file.read().strip()
file.close()
file_text = [o.split(':') for o in txt.strip().split('\n')]
fabrics = {o[0]:{'address': o[1].strip(), 'fabric': None, 'login': False} for o in file_text}


def login_changes(logged_in):
	if logged_in:
		color = "green"
		state = "normal"
	else:
		color = "white"
		state = "disabled"
	user_entry["bg"] = color
	pass_entry["bg"] = color
	post_button["state"] = state
	get_button["state"] = state


def fab_select_change(fab=None):
	if fab is None:
		fab = fabric_variable.get()
	login_state = "disabled" if fab == "fabric" else "normal"
	user_entry.config(state=login_state)
	pass_entry.config(state=login_state)
	login_button.config(state=login_state)
	if fab != "fabric":
		login_changes(fabrics[fab]["login"])
		if fabrics[fab]["login"]:
			user_entry.delete(0, tk.END)
			user_entry.insert(0, fabrics[fab]["fabric"].apic.username)
			pass_entry.delete(0, tk.END)
			path_entry.focus_set()
		else:
			user_entry.delete(0, tk.END)
			pass_entry.delete(0, tk.END)
			user_entry.focus_set()


def subtree_change(subtree = None):
	if subtree is None:
		subtree = subtree_variable.get()
	subtree_class_state = "disabled" if subtree == "No" else "normal"
	subtree_class_label.config(state=subtree_class_state)
	subtree_class_entry.config(state=subtree_class_state)


def key_up(e):
	if e.char == "\r":
		if e.widget is user_entry:
			pass_entry.focus_set()
		elif e.widget is pass_entry:
			login_to_fabric()


def get_data():
	fab = fabrics[fabric_variable.get()]['fabric']
	query = fab.query(path_entry.get())
	if include_variable.get() != "All":
		query.include = include_variable.get().lower()
	if subtree_variable.get() != "No":
		query.subtree = subtree_variable.get().lower()
	if subtree_class_entry.get().strip() != "" and query.subtree is not None:
		query.subtree_class = subtree_class_entry.get().strip()
	query.run()
	if query.data.count == 1:
		data = query.data.imdata[0]
	else:
		data = query.data.imdata
	if json_xml_variable.get() == "json":
		data_text.replace("1.0", tk.END, json.dumps(data, indent=2))
	else:
		data_text.replace("1.0", tk.END, json_to_xml(data))


def post_data():
	fab = fabrics[fabric_variable.get()]['fabric']
	data = data_text.get("1.0", tk.END)
	if data.strip()[0] in "[{":
		data = json.loads(data)
	if fab.post(data) == 200:
		messagebox.showinfo("Fabric Post", "Post was successful.")
	else:
		rsp = Data(fab.apic.response.text).attribute('text')
		messagebox.showerror("Fabric Post Failed", f"fabric post failed.\nResponse:\n{rsp}")


def login_to_fabric():
	fab = fabric_variable.get()
	user = user_entry.get().strip()
	passwd = pass_entry.get().strip()
	passwd = None if passwd == "" else passwd
	if fab in fabrics and user != "" and passwd != "":
		if fabrics[fab]['fabric'] is None:
			fabrics[fab]['fabric'] = Fabric(fabrics[fab]['address'])
		fabrics[fab]['login'] = fabrics[fab]['fabric'].login(user, passwd)
		login_changes(fabrics[fab]['login'])
		if fabrics[fab]['login']:
			path_entry.focus_set()
		else:
			user_entry['bg'] = 'red'
			pass_entry['bg'] = 'red'
			messagebox.showerror("Alert", "Authentication Failed!")
			pass_entry.select_range(0, tk.END)
			pass_entry.focus_set()


gui_main = tk.Tk()
gui_main.title("ACI Post")
gui_main.geometry("800x600")

fabric_variable = tk.StringVar(gui_main)
fabric_variable.set("fabric")
fab_select = tk.OptionMenu(gui_main, fabric_variable, *list(fabrics.keys()), command=fab_select_change)
fab_select.place(x=10, y=10)

user_entry = tk.Entry(gui_main, width=12)
user_entry.bind("<KeyRelease>", key_up)
user_entry.place(x=110, y=10)

pass_entry = tk.Entry(gui_main, show="~", width=12)
pass_entry.bind("<KeyRelease>", key_up)
pass_entry.place(x=230, y=10)

login_button = tk.Button(gui_main, text="Login", command=lambda: login_to_fabric())
login_button.place(x=350, y=10)
fab_select_change()

get_button = tk.Button(gui_main, text="Get", state="disabled", command=get_data)
get_button.place(x=675, y=10)

post_button = tk.Button(gui_main, text="Post", state="disabled", command=post_data)
post_button.place(x=730, y=10)

path_label = tk.Label(gui_main, text="Path:")
path_label.place(x=10, y=43)
path_entry = tk.Entry(gui_main, width=73)
path_entry.place(x=50, y=40)

json_xml_variable = tk.Variable(gui_main)
json_xml_variable.set("json")
json_xml_select = tk.OptionMenu(gui_main, json_xml_variable, *["json", "xml"])
json_xml_select.config(width=6)
json_xml_select.place(x=719, y=40)

include_label = tk.Label(gui_main, text="Include:")
include_label.place(x=10, y=72)
include_variable = tk.Variable(gui_main)
include_variable.set("All")
include_select = tk.OptionMenu(gui_main, include_variable, *["All", "Config", "Naming"])
include_select.config(width=8)
include_select.place(x=65, y=70)

subtree_label = tk.Label(gui_main, text="Subtree:")
subtree_label.place(x=152, y=72)
subtree_variable = tk.Variable(gui_main)
subtree_variable.set("No")
subtree_select = tk.OptionMenu(gui_main, subtree_variable, *["No", "Children", "Full"], command=subtree_change)
subtree_select.config(width=8)
subtree_select.place(x=210, y=70)
subtree_class_label = tk.Label(gui_main, text="Class:")
subtree_class_label.place(x=294, y=72)
subtree_class_entry = tk.Entry(gui_main, width=14)
subtree_class_entry.place(x=336, y=69)
subtree_change()

data_text = tk.Text(gui_main, width=110, height=24, bg="grey")
data_text.place(x=10, y=98)
