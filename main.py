# Module: main
# Author: Kenneth Wheeler
# Created on: 08.10.2022
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from requests import get
from urllib.parse import urlencode, parse_qsl
import xbmcgui
import xbmcplugin

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.
_HANDLE = int(sys.argv[1])

#The way that Kodi functions as a plugin it runs everything from the top down each time the plugin is called
#this means we can put a variable at the top of the program to display all the current broadcasts we have available
#however this plugin gets closed every time an action is taken and reopened thus we need to remake the VIDEOS dictionary each time

#create a json variable out of the aws server so we are not pinging it constantly
aws_link = (get("https://rt1o4zk4ub.execute-api.us-west-2.amazonaws.com/prod/kodi/content")).json()
VIDEOS = {}

#Ceates a list of shows currently available for display and use throught the rest of the script
#its neccessary to have this top level so the rest of the program is able to call it
true_id_checklist = ['']
for i in aws_link['data']:
    true_id = (i['program_id']).split('_', 1)[0]
    if true_id not in true_id_checklist:
        VIDEOS[i['program_title']] = []
        true_id_checklist.append(true_id)


def pull_hls(x):
    try:
        hls_site = (get(x).json())['data']['media'][0]['url']
        return(hls_site)
    except:
        pass


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(_URL, urlencode(kwargs))    


def get_categories():
    pgm_id_checklist = ['']
    """
    Get the list of video categories.

    :return: The list of video categories
    :rtype: types.GeneratorType
    """

    print('get categories definition has been called')
    for name_of_show in VIDEOS:
        for id in aws_link['data']:
            if name_of_show == id['program_title'] and id['program_id'] not in pgm_id_checklist:
                VIDEOS[name_of_show].append({'name': id['date'], 'thumb': id['thumbnail'], 'genre': id['description']})
                pgm_id_checklist.append(id['program_id'])

    return VIDEOS.keys()


def get_videos(category):
    content_id_check_list = ['']
    """
    Get the list of videofiles/streams.

    :param category: Category name
    :type category: str
    :return: the list of videos in the category
    :rtype: list
    """
    print('get videos definition has been called')

    for name_of_show in VIDEOS:
        for id in aws_link['data']:
            if name_of_show == id['program_title'] and id['content_id'] not in content_id_check_list:
                VIDEOS[name_of_show].append({'name': id['date'], 'thumb': id['thumbnail'], 'video': id['path'], 'genre': id['description']})
                content_id_check_list.append(id['content_id'])

    for show_date in VIDEOS[category]:
        stream_link = pull_hls(show_date['video'])
        show_date['video'] = stream_link
    
    return VIDEOS[category]


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    This is the main menu that is displayed when we open the Victory Cannel add on
    """
    print('list categories definition has been called')
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_HANDLE, 'My Video Collection')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, 'videos')
    # Get video categories
    categories = get_categories()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category)
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': VIDEOS[category][0]['thumb'],
                          'icon': VIDEOS[category][0]['thumb'],
                          'fanart': VIDEOS[category][0]['thumb']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': category,
                                    'genre': VIDEOS[category][0]['genre'],
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', category=category)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    print('list videos definition has been called')
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.s
    xbmcplugin.setPluginCategory(_HANDLE, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, 'videos')
    # Get the list of videos in the category.
    videos = get_videos(category)
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': video['name'],
                                    'genre': video['genre'],
                                    'mediatype': 'video'})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', video=video['video'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    print('play video definition has been called')
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    print('router has started')
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    print('Hello World')
    router(sys.argv[2][1:])
