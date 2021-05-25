import utils as u
import math
import asyncio

def select_destination(destinations):
    # u.cls()

    print('Select a destination', '\n')
    
    _print_destination_options(destinations)

    print()

    inp = input('Selection: ')

    if inp == '\\':
        # u.cls()
        return

    if inp == "*":
        return inp

    selected_destination = u.try_cast(inp, int) - 1
    assert selected_destination != None
    assert 0 <= selected_destination <= len(destinations)

    # u.cls()

    return selected_destination

def select_place(places):
    # u.cls()

    print('Select a place', '\n')

    _print_place_options(places)

    print()

    sel = input('Selection: ')

    if sel == '\\':
        # u.cls()
        return

    selected_place = u.try_cast(sel, int) - 1
    assert selected_place != None
    #If the user selects 0, go back
    if selected_place == -1:
        # u.cls()
        select_place(places)
        return 0 
    assert 0 <= selected_place < len(places)

    u.cls()

    return selected_place


def _print_destination_options(destinations):
    half = math.ceil(len(destinations) / 2)

    for i in range(half):
        print("{0: <50}".format(str(i + 1) + ". " + destinations[i]['name']), end='')
        if i + half + 1 <= len(destinations):
            print("{0}".format(str(i + half + 1) + ". " + destinations[i + half]['name']))
        else:
            print()

def _print_place_options(places):
    half = math.ceil(len(places) / 2)

    for i in range(half):
        print("{0: <35}".format(str(i + 1) + ". " + places[i]['name']), end='')
        if i + half + 1 <= len(places):
            print("{0}".format(str(i + half + 1) + ". " + places[i + half]['name']))
        else: 
            print()


def add_destination(gm):
    """
    Adding a destination to the dictionary

    Args:
        None

    Returns:
        None
    """

    u.cls()

    print('Enter destination name to use the autocomplete functionality.')

    inp = input('Input: ')

    print()

    if inp == '\\':
        u.cls()
        return 0

    ac = gm.get_destination_suggestions(inp)


    if ac:
        s = [(i['description'], i['place_id']) for i in ac]

        print("0. Go Back")
        for x in range(len(s)):
            print("{}. {}".format(x + 1, s[x][0]))

        print()
        sel = input('Selection (leave blank to go back): ')

        # Try to convert to int, if fails raise error
        sel = u.try_cast(sel, int) - 1
        assert sel != None
        # If the user selects 0, go back to the input screen
        if sel == -1:
            u.cls()
            add_destination(gm)
            return 0
        assert 0 <= sel <= len(s)

        selected_destination = s[sel]
        return selected_destination[1]

    else:
        u.cls()

        print('destination could not be found :(')
        print('Enter in the Place ID below (https://developers.google.com/maps/documentation/javascript/place-id)', '\n')

        inp = input('Place ID: ')
        if inp == '\\':
            u.cls()
            return 0

        return inp

def add_place(gm, destination):
    """
    Adding a place to the dictionary

    Args:
        override_destination::[int] 
            the ID of the destination containing the place.  If not specified, the user will be prompted to select a destination

    Returns:
        None
    """

    print('Selected Destination: {}'.format(destination.name))
    print('Enter a place name to use the autocomplete functionality.')

    print()

    inp = input('Input: ')

    if inp == '\\':
        u.cls()
        return 

    # # TODO pull this constant out
    sugs = gm.get_place_suggestions(inp, location=[destination.latitude, destination.longitude])

    print()

    print('0. Go Back')
    for i, sug in enumerate(sugs):
        print("{}. {}".format(i + 1, sug['structured_formatting'].get('main_text', "") + " " + sug['structured_formatting'].get('secondary_text', "")))

    print()

    selection = input('Selection: ')

    if selection == '\\':
        u.cls()
        return 0

    selection = u.try_cast(selection, int) - 1
    assert selection != None
    if selection == -1:
        u.cls()
        add_place(gm, destination)
        return
    assert 0 <= selection <= 4

    # Geocode the place and fill in some info
    return gm.geocode_place(ac=sugs[selection])


def override_album():
    return input('Use existing Album ID? (y/n): ').lower() in ('y', 'yes')

def ask_true_false_question(text):
    return input(text).lower() in ('y', 'yes')

async def add_album(gp, destination, place, albums, allow_add_another=True):
    """
    Download photos from a Google Photos album and add them to a place

    Args:
        override_destination::[int] 
            the ID of the destination containing the place.  If not specified, the user will be prompted to select a destination

        override_place::[int]
            the ID of the place.  If not specified the user will be prompted to select a place

        allow_add_another::[bool]
            whether the user should be prompted to add another album to another place
    
    Returns:
        None
    """

    #Get album name
    album_name = u.rlinput('Search for albums: ', f"{destination.name} -- {place.name}")

    if album_name == '\\':
        u.cls()
        return

    # #Get suggestions from Google Photos, limit to 5
    if not gp.done:
        await gp.albums
    albums = gp.albums
    suggestions = gp.get_album_suggestions(albums, album_name, 5)

    print()

    print("0. To Go Back")
    for i, suggestion in enumerate(suggestions):
        print('{}. {}'.format(i + 1, suggestion[0]))

    print()

    inp = input('Selection: ') 

    if inp == '\\':
        u.cls()
        return

    #Decrement by 1 since Python indexs at 0
    selection = u.try_cast(inp, int) - 1
    assert selection != None
    #If the user entered 0, go back
    if selection == -1:
        u.cls()
        add_album(gp, destination=destination, place=place)
        return
    assert 0 <= selection < len(suggestions)

    album_id = suggestions[selection][1]

    return gp.get_album_info(album_id)

    # u.cls()

    # return {
    #     "place_id": place.place_id,
    #     "destination_id": destination.destination_id,
    #     "album_id": suggestions[selection][1],
    #     "title": metadata.get('title'),
    #     'cover_photo_id': metadata.get('coverPhotoMediaItemId')
    # }

def edit_destination(destination):
    """
    Editing the information of a destination in the dictionary

    Args:
        override_destination::[int] 
            the ID of the destination containing the place.  If not specified, the user will be prompted to select a destination

    Returns:
        None
    """

    u.cls()

    for k, v in destination.__dict__.items():
        inp = u.rlinput('{}: '.format(k), str(v))
        
        inp_as_float = u.try_cast(inp, float)        
        if inp_as_float != None:
            #If the input is a number, save it as a float or int
            destination.__dict__[k] = inp_as_float if '.' in inp else int(inp) 
            #if the input is a string, save it as such
        
        elif isinstance(v, str):
            destination.__dict__[k] = inp
        
    return destination

def edit_place(place):
    """
    Editing the information of a destination in the dictionary

    Args:
        override_destination::[int] 
            the ID of the destination containing the place.  If not specified, the user will be prompted to select a destination

    Returns:
        None
    """

    u.cls()

    for k, v in place.__dict__.items():
        inp = u.rlinput('{}: '.format(k), str(v))
        
        inp_as_float = u.try_cast(inp, float)        
        if inp_as_float != None:
            #If the input is a number, save it as a float or int
            place.__dict__[k] = inp_as_float if '.' in inp else int(inp) 
            #if the input is a string, save it as such
        
        elif isinstance(v, str):
            place.__dict__[k] = inp
        
    return place
