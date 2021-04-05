#################################
##### Name: Taylor Faires
##### Uniqname: Fairest
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time

BASE_URL = 'https://www.nps.gov'
nps_html = requests.get('https://www.nps.gov/index.htm')
soup = BeautifulSoup(nps_html.text, 'html.parser')
mapquest_api = secrets.mapquest_api
CACHE_FILE_NAME = 'cacheNPS.json'
CACHE_DICT = {}

def load_cache():
    '''opens cache file to store information

    Parameters
    ----------
    None

    Returns
    ----------
    cache: json
    a json that stores previous search results
    '''    
    try:       
        cache_file = open(CACHE_FILE_NAME, 'r')        
        cache_file_contents = cache_file.read()        
        cache = json.loads(cache_file_contents)        
        cache_file.close()    
    except:        
        cache = {}    
    return cache

def save_cache(cache):
    ''' saves existing or new cache to contain previous searches and calls to the nps website
    
    Parameters
    ----------
    cache: json
    cache in which to write the search into

    Returns
    ----------
    None
    '''    
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)    
    cache_file.write(contents_to_write)    
    cache_file.close()

def make_url_request_using_cache(url, cache):
    ''' searches cache to see if search has been made before if search has been made, takes information from cache

    Parameters
    ----------
    url: str
    the url of the request being made

    cache: json
    the json file to search and see if url call has been made previously
    '''    
    if (url in cache.keys()): # the url is our unique key        
        print("Using cache")        
        return cache[url]   
    else:        
        print("Fetching")        
        time.sleep(1)        
        response = requests.get(url)        
        cache[url] = response.text        
        save_cache(cache)        
        return cache[url]

CACHE_DICT = load_cache()
class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category='No Category', name='No Name', address='No Address', zipcode= "No Zipcode", phone='No Phone'):
        
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
    
    def info(self):
        return f'{self.name} ({self.category}): {self.address} {self.zipcode}'


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_dict = {}
    state_dropdown = soup.find('ul', class_='dropdown-menu')
    state_list = state_dropdown.find_all('a')
    for state in state_list:
        state_name = state.contents[0].lower()
        state_url = BASE_URL + state.get('href')
        state_dict[state_name] = state_url
    return state_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    site_html = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(site_html, 'html.parser')
    name= soup.find('a', class_='Hero-title').contents[0]
    category = soup.find('span', class_='Hero-designation').contents
    category = str(category)
    remove_list = ['[', "'", "'", ']']
    for item in remove_list:
        if item in category:
            category = category.replace(item, "")
    city = soup.find('span', itemprop='addressLocality').contents[0]
    state_abr = soup.find('span', itemprop='addressRegion').contents[0]
    zipcode = soup.find('span', itemprop='postalCode').contents[0].strip()
    telephone = soup.find('span', itemprop='telephone').contents[0].strip()
    address = city + ', ' + state_abr

    return NationalSite(category, name, address, zipcode, telephone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    state_html = requests.get(state_url)
    soup = BeautifulSoup(state_html.text, 'html.parser')
    parks_html = soup.find('ul', id= 'list_parks')
    park_links = parks_html.find_all('h3')
    parks_list = []
    for park in park_links:
        link_add = park.find('a').get('href')
        full_link = BASE_URL + link_add
        park_inst = get_site_instance(full_link)
        parks_list.append(park_inst)
    return parks_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    mapquest_base = f'http://www.mapquestapi.com/search/v2/radius?maxMatches=10&key={mapquest_api}&ambiguities=ignore&outFormat=json&radius=10&origin='
    origin= site_object.zipcode
    map_url = mapquest_base + origin
    response = make_url_request_using_cache(map_url, CACHE_DICT)
    results = json.loads(response)

            
    return results


def format_parks_list(parks_list, search_term):
    '''Formats results from get_sites_for_state()

    Parameters
    ----------
    parks_list: list
        the return of get_sites_for_state()
    
    search_term: string
        the term entered in first_search()
    
    Returns:
        string
            a string instance of the results of get_sites_for_state()

    '''
    i = 1 
    parks_str = []
    for parks in parks_list:
        parks_str.append(f'[{i}] {parks.info()}')
        i += 1
    
    search_header = f'''
    ----------------------------------------
    list of national sites in {search_term}
    ----------------------------------------
    '''
    return search_header + '\n' + '\n'.join(parks_str)
    


def format_nearby(nearby_results, site_name):
    '''Formats results from get_nearby_places()

    Parameters
    ----------
    nearby_results: list
        the return of get_nearby_places()
    
    site_name: string
        the name of the site specified in second_search()
    
    Returns:
        string
            a string instance of the results of get_nearby_places()

    '''
    search_results = nearby_results['searchResults']
    nearby_dict = {}
    for location in search_results:
        name = location['fields']['name']
        if location['fields']['address']:
            address = location['fields']['address']
            city = location['fields']['city']
        else:
            address = 'no address'
            city = 'no city'
        if location['fields']['group_sic_code_name']:
            category = location['fields']['group_sic_code_name']
            key = name + f' ({category})'
            nearby_dict[key] = f'{address}, {city}'
        else:
            key = name + f' (no category)'
            nearby_dict[key] = f'{address}, {city}'
    nearby_list = []
    for k,v in nearby_dict.items():
        near_str = f'- {k}: {v}'
        nearby_list.append(near_str)

    search_header = f'''
    ----------------------------------------
    places near {site_name}
    ----------------------------------------
    '''
    return search_header + '\n' + '\n'.join(nearby_list)

def clear_results(parks_list):
    '''clears list of sites for new search

    Parameters
    ---------
    None

    Returns
    ---------
    None
    '''

    parks_list.clear()

def first_search(search_term):
    if search_term in state_dict.keys():
        parks_list.extend(get_sites_for_state(state_dict[search_term.lower()]))
        print(format_parks_list(parks_list, search_term))

def second_search():
    while True:
        print('Choose number for detail search or enter "back" or "exit"')
        search_term= input().lower()
        if search_term != 'exit':
            if search_term.isnumeric():
                search_term_int = int(search_term)
                if search_term_int > 0 and search_term_int < (len(parks_list) + 2):
                    parks_index = search_term_int - 1
                    nearby_results = get_nearby_places(parks_list[parks_index])
                    site_name = parks_list[parks_index].name
                    print(format_nearby(nearby_results, site_name))
                else:
                    print('Error, please enter a valid number')
            elif search_term == 'back':
                while True:
                    print('Enter a state name (e.g. North Carolina, north carolina)')
                    search_term = input()
                    search_term = search_term.lower()
                    if search_term != 'exit':
                        if search_term in state_dict.keys():
                            first_search(search_term)
                            break
                        else:
                            print('Error, please enter a state')
                    else:
                        print('goodbye')
                        break
        else:
            break




if __name__ == "__main__":
    parks_list = []
    state_dict = build_state_url_dict()
    while True:
        print('Enter a state name (e.g. North Carolina, north carolina)')
        search_term = input()
        search_term = search_term.lower()
        if search_term != 'exit':
            if search_term in state_dict.keys():
                first_search(search_term)
                second_search()
                break
            else:
                print("Error, enter a state")
        else:
            print('goodbye')
            break
