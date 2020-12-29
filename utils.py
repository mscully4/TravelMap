import os
import readline 
import json

def write_json_file(file_name, data):
    with open(file_name, 'w') as fh:
        json.dump(data, fh, sort_keys=True, indent=4)

def read_json_file(file_name):
    with open(file_name, 'r') as fh:
        return json.loads(fh.read())

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def clr_line():
    print("\033[A                             \033[A")

def try_cast(val, type_):
    try:
        return type_(val)
    except Exception as e: 
        return None

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)  # or raw_input in Python 2
   finally:
      readline.set_startup_hook()