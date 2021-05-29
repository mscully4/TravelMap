import utils as u
import math
from pyfiglet import Figlet

def print_figlet(text):
    u.cls()
    print(Figlet(font='slant').renderText(text))

def print_menu():
    u.cls()

    print_figlet("Travel Map")
    print('Main Menu')

    print('0. To Exit')
    print('1. Enter a new destination')
    print('2. Enter a new place')
    print('3. Add an album to a place')
    print('4. Edit a destination')
    print('5. Edit a place')
    print('6. Delete a destination')
    print('7. Delete a place')
    print('8. Add Photos')
    print('9. Add Album Cover')

    print()

def print_single_list(sugs):
    print('0. Go Back')
    for i, sug in enumerate(sugs):
        print(f"{i+1}. {sug}")

def print_double_list(lst):
    half = math.ceil(len(lst) / 2)

    print('0. Go Back')
    for i in range(half):
        print("{0: <50}".format(str(i + 1) + ". " + lst[i].name), end='')
        if i + half + 1 <= len(lst):
            print("{0}".format(str(i + half + 1) + ". " + lst[i + half].name))
        else:
            print()

def get_selection(minimum, maximum):
    selection = input('Selection: ')

    if selection in "*\\":
        return selection

    selection = u.try_cast(selection, int) 
    assert selection != None
    assert minimum <= selection <= maximum

    return selection

def get_input(msg, default=None):
    print(msg)
    if default:
        return u.rlinput("Input: ", default)

    return input('Input: ')

def ask_yes_no_question(text):
    return input(text).lower() in ('y', 'yes')

def edit_obj(obj):
    """
    Editing the information of a destination in the dictionary

    Args:
        override_destination::[int] 
            the ID of the destination containing the place.  If not specified, the user will be prompted to select a destination

    Returns:
        None
    """

    for k, v in obj.__dict__.items():
        inp = u.rlinput('{}: '.format(k), str(v))
        
        inp_as_float = u.try_cast(inp, float)        
        if inp_as_float != None:
            #If the input is a number, save it as a float or int
            obj.__dict__[k] = inp_as_float if '.' in inp else int(inp) 
            #if the input is a string, save it as such
        
        elif isinstance(v, str):
            obj.__dict__[k] = inp
        
    return obj