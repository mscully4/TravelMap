import utils as u
import math

def select_city(cities):
    u.cls()

    print('Select a city', '\n')
    
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

    return selected_city

def select_place(places):
    u.cls()

    print('Select a place', '\n')

    _print_place_options(places)

    print()

    sel = input('Selection: ')

    if sel == '\\':
        u.cls()
        return

    selected_place = u.try_cast(sel, int) - 1
    assert selected_place != None
    #If the user selects 0, go back
    if selected_place == -1:
        u.cls()
        select_place(places)
        return 0 
    assert 0 <= selected_place < len(places)

    u.cls()

    return selected_place


def _print_city_options(cities):
    half = math.ceil(len(cities) / 2)

    for i in range(half):
        print("{0: <50}".format(str(i + 1) + ". " + cities[i]['entry']['city']), end='')
        if i + half + 1 <= len(cities):
            print("{0}".format(str(i + half + 1) + ". " + cities[i + half]['entry']['city']))
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

        # # Check if the selected city is already in the dictionary
        # assert selected_city[1] not in self.cities

        # gc = self.geocode_city(selected_city[1])
        # gc['places'] = []

        # self.data['destinations'].append(gc)
        # self.cities.append(gc['place_id'])

        # u.cls()

    else:
        u.cls()

        print('City could not be found :(')
        print('Enter in the Place ID below (https://developers.google.com/maps/documentation/javascript/place-id)', '\n')

        inp = input('Place ID: ')
        if inp == '\\':
            u.cls()
            return 0

        return inp

        # gc = self.geocode_city(inp)

        # gc['places'] = []

        # self.data['destinations'].append(gc)
        # self.cities.append(gc['place_id'])

        # u.cls()

    # self.edit_city(len(self.cities) - 1)

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

    print('Selected City: {}'.format(city['entry']['city']))
    print('Enter a place name to use the autocomplete functionality.')

    print()

    inp = input('Input: ')

    if inp == '\\':
        u.cls()
        return 

    # # TODO pull this constant out
    sugs = gm.get_place_suggestions(inp, location=[city['entry']['latitude'], city['entry']['longitude']])

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
    place['city'] = city['entry']['city']
    place['city_id'] = city['place_id']
    # place['images'] = []
    return place
    # if place['place_id'] not in self.places:
    #     place['city'] = city['city']
    #     place['images'] = []
    #     self.data['destinations'][selected_city]['places'].append(place) 

    #     # Allow user to edit autocomplete information
    #     self.edit_place(selected_city, len(self.data['destinations'][selected_city]['places']) - 1)
    
    #     search_albums = input('Search for albums? (y/n): ')

    #     u.cls()
        
    #     if search_albums.lower() == 'y':
    #         # Allow the user to link a GP album to the place
    #         self.add_album(selected_city, len(self.data['destinations'][selected_city]['places']) - 1, allow_add_another=False)

    #     add_another = input('Add Another? (y/n): ')

    #     u.cls()
        
    #     if add_another.lower() == 'y':
    #         self.add_place(override_city=selected_city)
    
    # u.cls()

def add_album(cities, places, override_city=None, override_place=None, allow_add_another=True):
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

    #Throw an error if override_city == None and override_place != None
    assert not (override_city == None and override_place != None)

    #Get City
    if override_city == None:     
        selected_city = _select_city(cities)
    
    else:
        selected_city = override_city

    # u.cls()

    # #Get Place
    # if override_place == None:
    #     u.cls()

    #     print('Select a place', '\n')

    #     self.print_place_options(selected_city)

    #     print()

    #     sel = input('Selection: ')

    #     if sel == '\\':
    #         u.cls()
    #         return

    #     selected_place = u.try_cast(sel, int) - 1
    #     assert selected_place != None
    #     #If the user selects 0, go back
    #     if selected_place == -1:
    #         u.cls()
    #         self.add_album()
    #         return 0 
    #     assert 0 <= selected_place < len(self.data['destinations'][selected_city]['places'])

        

    # else:
    #     assert isinstance(override_place, int)
    #     selected_place = override_place

    # u.cls()

    # if self.data['destinations'][selected_city]['places'][selected_place].get('albumId', None) != None:
    #     print("Album already exists for this place!")

    # #Get album name
    # album_name = u.rlinput('Search for albums: ', self.data['destinations'][selected_city].get('city', "") + " -- " + self.data['destinations'][selected_city]['places'][selected_place].get('name', ""))

    # if album_name == '\\':
    #     u.cls()
    #     return

    # #Get suggestions from Google Photos, limit to 5
    # suggestions = self.gp.get_album_suggestions(self.gp.get_albums(), album_name, 5)

    # print()

    # print("0. To Go Back")
    # for i, suggestion in enumerate(suggestions):
    #     print('{}. {}'.format(i + 1, suggestion[0]))

    # print()

    # inp = input('Selection: ') 

    # if inp == '\\':
    #     u.cls()
    #     return

    # #Decrement by 1 since Python indexs at 0
    # selection = u.try_cast(inp, int) - 1
    # assert selection != None
    # #If the user entered 0, go back
    # if selection == -1:
    #     u.cls()
    #     self.add_album(override_city=selected_city, override_place=selected_place)
    #     return
    # assert 0 <= selection < len(suggestions)

    # u.cls()

    # #TODO: Should probably also clean out the directory in S3
    # self.data['destinations'][selected_city]['places'][selected_place]['albumId'] = suggestions[selection][1]
    # self.overwrite()

    # if allow_add_another:
    #     upload_another = input('Add Another Album? (y/n): ')

    #     u.cls()
    #     if upload_another.lower() == 'y':
    #         self.add_album(override_city=selected_city)