from langchain_experimental.utilities import PythonREPL
from langchain.agents import Tool
from langchain_community.tools import YouTubeSearchTool
from pydantic.v1 import BaseModel, Field
from langchain_core.tools import tool
from typing import Annotated, Literal, List
import wmi
import subprocess
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import webbrowser
import pythoncom
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()



#####  Python shell Tool
python_repl = PythonREPL()

repl_tool = Tool(
    name="python_repl",
    description='''A Python shell. Use this to execute python files and commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.
                To run python files pass the whole content in file as string. Add required print statements to get output. Don't use terminal to run python files unless user asked. Instead use this tool.
                ''',
    func=python_repl.run,
)



#### Youtube Tool
class YoutubeInputs(BaseModel):
    """Inputs to the wikipedia tool."""
    query: str = Field(
        description="A comma separated list, the first part contains a title/name and the second a number that is the maximum number of video results to return aka num_results. The second part is optional"
    )

youtube_tool = YouTubeSearchTool(
    args_schema=YoutubeInputs,
    return_direct=True,
)




#### Brightness Adjustment Tools

@tool('Brightness_Measurement_Tool')    
def get_brightness()->str:
    '''
    Measures the current brightness of the system. Helpful to increase or decrease brightness as required for client.
    '''
    pythoncom.CoInitialize()
    wmi_service = wmi.WMI(namespace='wmi')
    brightness_levels = wmi_service.WmiMonitorBrightness()
    brightness = brightness_levels[0].CurrentBrightness
    return f'The current brightness of the system is {brightness}'
    

@tool('Brightness_Changing_Tool')
def change_brightness(b:Annotated[int,'Brightness to set. It is to be a integer between 0 and 100.'])->str:

    '''
    Changes the Brightness of the system.
    
    '''
    pythoncom.CoInitialize()
    wmi_service = wmi.WMI(namespace='wmi')
    brightness_methods = wmi_service.WmiMonitorBrightnessMethods()[0]
    brightness_methods.WmiSetBrightness(int(b), 1) 
    return f"System Brightness is set to {b}" 



#### Tool to open any settings.
with open('settings.txt',"r") as f:
    settings_txt = f.readlines()
settings_dict = {s.split(',')[0]: s.split(',')[1].strip() for s in settings_txt}   
settings = list(settings_dict.keys())

@tool('Quick_Settings_Opener')
def settings_opener(
    setting : Annotated[Literal[tuple(settings)],''' The setting to open. Select from the given list of settings. 
                        If the user mentions a task but doesn't specify a settings name, select the relevant setting based on the task. Also, provide suggestions on how to perform the task and then open the appropriate setting.
                        For example if the user says they want to connect their headphones, suggest steps for connecting and open the "Bluetooth" settings.
                        Default is the main settings.
                        ''']='settings',
)->str:
    
    '''
    Quickly opens any specified setting or the setting related to a given task.
    '''
    command = settings_dict.get(setting,'none')
    if command=='none':
        return f'I am sorry. I am unable to open the asked settings.'
    try:
        subprocess.run(['start', command], shell=True)
        return f'Opened {setting} settings.'
    except Exception as e:
        return f'I am sorry. I am unable to open the asked settings due to {e}.'

   


#### Tool to download images with url
@tool('Download_Image')
def download_image(
image_url : Annotated[str,'The url of the image to download. Make sure it ends with proper image extension like .jpg, .png etc'],
image_name : Annotated[str,'The name of the image file. Make sure it ends with suitable extension like .jpg, .png etc'],
directory : Annotated[str,'The directory in which to download the image. Always ask for download directory. If user specifies no directory, select downloads directory from default_paths.']=os.getenv('DOWNLOADS'),
)->str:
    

    ''' 
    Downloads a image from a given url. 
    Always do the brave search first to get relevant image urls from brave search.
    For images, consider the urls from json which ends with proper extension like .jpg, .jpeg etc. if possible. And also consider url from thumbnails, properties urls from json response file.
    Sometimes it may give error, then try with different image urls.
    '''

    response = requests.get(image_url)
    file_name = os.path.join(os.path.normpath(directory),image_name)
    
    if response.status_code == 200:
       
        with open(file_name, "wb") as file:
            file.write(response.content)
        return f"Image {image_name} downloaded successfully and saved to {directory}"
    else:
        return f"Failed to download image. Status code: {response.status_code}"



##### Tool to do brave search
@tool('Brave_Search')
def brave_web_search(
    query : Annotated[str,'The query to search in the search engine.'],
    num_results:Annotated[int,'The number of search results to return.']=10,
    image : Annotated[Literal['True','False'],'Set it to True to do image search with given query. Default is False']='False',
    )->List[dict]:


    ''' 
    A search engine. Useful for when you need to answer questions about current events. Use this search engine to get any details aboute latest events and the things you are not updated at.
    Input should be a search query.
    Returns a json file containing search results.
    '''
    
    if eval(image):
        url = 'https://api.search.brave.com/res/v1/images/search'
    else:
        url = 'https://api.search.brave.com/res/v1/web/search'   
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': os.getenv('BRAVE_API_KEY')
    }
    params = {
        'q': query,
        'count': num_results
    }
    
    # Create a session object to persist settings across requests
    session = requests.Session()

    # Define a retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # A backoff factor to apply between attempts
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["HEAD", "GET", "OPTIONS"]  # HTTP methods to retry on
    )

    # Mount the retry strategy to the session
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Make the request with retry logic
    try:
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        # Process the JSON response
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}. Try again."
    



#### Tool to open url witha given browser.
@tool('Open_Url')
def open_url(
    url: Annotated[str, 'URL to open.'],
    browser_name: Annotated[str, 'The browser in which to open the given URL. Select None if no specific browser is given by the user.'] = None,
    browser_file_path: Annotated[str, 'The path to the browser executable file. Select None if no specific browser is given by the user.'] = None
) -> str:
    
    ''' 
    Opens a URL in a specified web browser. For the browser_file_path, search for only .exe files on the system. Don't consider shortcuts files(i.e .lnk files).
    Don't determine the URL on your own. Use other tools to find the correct URLs the user wants. For example, if the user wants to open a video, you can get the URL from the `youtube_tool` and then use this tool.
    Both bowser_name and browser_file_name should be passed to this tool in case to open url in specific browser.
    '''    
    
    try:
        if browser_file_path:
            browser_file_path = os.path.normpath(browser_file_path)
            webbrowser.register('browser', None, webbrowser.BackgroundBrowser(browser_file_path))
            webbrowser.get('browser').open(url)
            return f'The given url is opened in given browser.'
        else:
            webbrowser.get().open(url)
            return f'The given url is opened.'
    except:
        return f'Sorry, there is some error in opening url.'    
    
