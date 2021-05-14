import utils as u
import math

def select_city(cities):
    # u.cls()

    print('Select a city', '\n')
    
    _print_city_options(cities)

    print()

    inp = input('Selection: ')

    if inp == '\\':
        # u.cls()
        return

    selected_city = u.try_cast(inp, int) - 1
    assert selected_city != None
    assert 0 <= selected_city <= len(cities)

    # u.cls()

    return selected_city

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


def _print_city_options(cities):
    half = math.ceil(len(cities) / 2)

    for i in range(half):
        print("{0: <50}".format(str(i + 1) + ". " + cities[i]['city']), end='')
        if i + half + 1 <= len(cities):
            print("{0}".format(str(i + half + 1) + ". " + cities[i + half]['city']))
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


def add_city(gm):
    """
    Adding a city to the dictionary

    Args:
        None

    Returns:
        None
    """

    u.cls()

    print('Enter city name to use the autocomplete functionality.')

    inp = input('Input: ')

    print()

    if inp == '\\':
        u.cls()
        return 0

    ac = gm.get_city_suggestions(inp)


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
            add_city(gm)
            return 0
        assert 0 <= sel <= len(s)

        selected_city = s[sel]
        return selected_city[1]

    else:
        u.cls()

        print('City could not be found :(')
        print('Enter in the Place ID below (https://developers.google.com/maps/documentation/javascript/place-id)', '\n')

        inp = input('Place ID: ')
        if inp == '\\':
            u.cls()
            return 0

        return inp

def add_place(gm, cities, override_city=None):
    """
    Adding a place to the dictionary

    Args:
        override_city::[int] 
            the ID of the city containing the place.  If not specified, the user will be prompted to select a city

    Returns:
        None
    """

    u.cls()
    
    if override_city == None: 
        print('Select a city')

        print()
        
        _print_city_options(cities)

        print()

        inp = input('Selection: ')

        if inp == '\\':
            u.cls()
            return 

        selected_city = u.try_cast(inp, int) - 1
        assert selected_city != None
        assert 0 <= selected_city <= len(cities)

        u.cls()

    else:
        selected_city = override_city

    city = cities[selected_city]

    print('Selected City: {}'.format(city.get('city')))
    print('Enter a place name to use the autocomplete functionality.')

    print()

    inp = input('Input: ')

    if inp == '\\':
        u.cls()
        return 

    # # TODO pull this constant out
    sugs = gm.get_place_suggestions(inp, location=[city['latitude'], city['longitude']])

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
        add_place(gm, cities, selected_city)
        return
    assert 0 <= selection <= 4

    # Geocode the place and fill in some info
    place = gm.geocode_place(ac=sugs[selection])
    place['city'] = city['city']
    place['city_id'] = city['place_id']
    return place

def add_album(gp, city, place, allow_add_another=True):
    """
    Download photos from a Google Photos album and add them to a place

    Args:
        override_city::[int] 
            the ID of the city containing the place.  If not specified, the user will be prompted to select a city

        override_place::[int]
            the ID of the place.  If not specified the user will be prompted to select a place

        allow_add_another::[bool]
            whether the user should be prompted to add another album to another place
    
    Returns:
        None
    """

    #Get album name
    album_name = u.rlinput('Search for albums: ', f"{city.city} -- {place.name}")

    if album_name == '\\':
        u.cls()
        return

    # #Get suggestions from Google Photos, limit to 5
    suggestions = gp.get_album_suggestions(gp.get_albums(), album_name, 5)

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
        add_album(gp, city=city, place=place)
        return
    assert 0 <= selection < len(suggestions)

    u.cls()
    print(suggestions[selection])

    return {
        "album_id": suggestions[selection][1],
        "place_id": place.place_id 
    }

def edit_city(city):
    """
    Editing the information of a city in the dictionary

    Args:
        override_city::[int] 
            the ID of the city containing the place.  If not specified, the user will be prompted to select a city

    Returns:
        None
    """

    u.cls()

    for k, v in city.__dict__.items():
        inp = u.rlinput('{}: '.format(k), str(v))
        
        inp_as_float = u.try_cast(inp, float)        
        if inp_as_float != None:
            #If the input is a number, save it as a float or int
            city.__dict__[k] = inp_as_float if '.' in inp else int(inp) 
            #if the input is a string, save it as such
        
        elif isinstance(v, str):
            city.__dict__[k] = inp
        
    return city

def edit_place(place):
    """
    Editing the information of a city in the dictionary

    Args:
        override_city::[int] 
            the ID of the city containing the place.  If not specified, the user will be prompted to select a city

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

def delete_city(self):
    """
    Deleting a city from the dictionary

    Args:
        None

    Returns:
        None
    """

    u.cls()

    print('Select a city to delete')
    
    print()
    
    _print_city_options()

    print()

    inp = input('Selection: ')

    if inp == '\\':
        u.cls()
        return

    selected_city = u.try_cast(inp, int) - 1
    assert selected_city != None
    assert 0 <= selected_city <= len(self.data['destinations'])

    #Delete the City from the dictionary
    del self.data['destinations'][selected_city]

    self.overwrite()

    u.cls()
