import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from typing import Annotated, Literal, List
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from gemini_llm import llm_gem as llm
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


class Files_Handler():
    def __init__(self):
        self.all_files_path = 'all_files_index.pkl'
        self.faiss_all_files_path = 'faiss_index_all_files'
        self.default_paths_path = 'default_paths.pkl'
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.root_paths = [r"D:\\",r"C:\\"]
        self.faiss_all_files = None
        self.load_files()
        self.load_faiss_files()
        self.load_default_paths()


    def load_default_paths(self):
        if not os.path.exists(self.default_paths_path):
            self.default_paths = {}
            self.load_def_dir()
            
        else:
            with open(self.default_paths_path, 'rb') as f:
                self.default_paths = pickle.load(f)
                self.load_def_dir()

    def load_def_dir(self):
        if ('desktop' not in self.default_paths.keys()) and (os.getenv('DESKTOP')):
            self.default_paths['desktop'] = os.getenv('DESKTOP')
        if ('downloads' not in self.default_paths.keys()) and (os.getenv('DOWNLOADS')):
            self.default_paths['downloads'] = os.getenv('DOWNLOADS')            
        self.save_default_paths()


    def save_default_paths(self):
        with open(self.default_paths_path, 'wb') as f:
            pickle.dump(self.default_paths, f) 

    def load_files(self):
        if not os.path.exists(self.all_files_path):
            print('Fetch all files first and then retry.')

        else:
            with open(self.all_files_path, 'rb') as f:
                self.all_files_index = pickle.load(f)  
        self.all_files = list(self.all_files_index.keys()).copy()
  
    def save_files(self):
        with open(self.all_files_path, 'wb') as f:
            pickle.dump(self.all_files_index, f)

    def index_files_and_directories(self,root_paths):
        file_index = {}
        for root_path in root_paths:
            for root, dirs, files in os.walk(root_path):
                for name in files:
                    if name not in file_index.keys():
                        file_index[name] = []
                    file_index[name].append(os.path.join(root, name))
                for name in dirs:
                    if name not in file_index.keys():
                        file_index[name] = []
                    file_index[name].append(os.path.join(root, name))
        file_index['none']=['none',]                          
        return file_index
    

    def faiss_index_files_and_directories(self,files):
        batch_size = 1000  
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            if self.faiss_all_files is None:
                self.faiss_all_files = FAISS.from_texts(batch_files, self.embeddings)
            else:
                self.faiss_all_files.add_texts(batch_files)
                print('added')

    
    def load_faiss_files(self):
        if not os.path.exists(self.faiss_all_files_path):
            print('Fetch all files first and then retry.')
        else:
            self.faiss_all_files = FAISS.load_local(self.faiss_all_files_path, self.embeddings, allow_dangerous_deserialization=True) 

    def save_faiss_files(self):
        self.faiss_all_files.save_local(self.faiss_all_files_path)


    def check_updates(self):
        new_all_files_index = self.index_files_and_directories(self.root_paths)
        new_all_files = list(new_all_files_index.keys()).copy()
        updates = set(new_all_files) - set(self.all_files.copy())
        print(f'updates : {list(updates)}')
        self.all_files_index = new_all_files_index
        self.all_files = list(self.all_files_index.keys()).copy()
        self.save_files()
        self.faiss_index_files_and_directories(list(updates))
        self.save_faiss_files()
        return f'Update Done.'




files_handler = Files_Handler()



@tool('Default_paths')
def get_default_paths(
    operation: Annotated[
        Literal['get', 'add', 'modify', 'delete'], 
        '''Specifies the action to perform. Available options:
            'get'    : Retrieve all available apps and their paths.
            'add'    : Add a new app and its path to the default paths.
            'modify' : Update the path for an existing app in the default paths.
            'delete' : Remove an app and its path from the default paths.
        '''
    ],
    app_name: Annotated[
        str, 
        '''The name of the application (used as a key in the dictionary).
            - When adding a new app, include information about whether it's a shortcut or the original path in the app name.
              Example: 'skype_app_shortcut' for a shortcut (skype.lnk), 'skype_app_original' for the original executable (skype.exe).
            - For 'modify' and 'delete' operations, ensure the app name is already in the dictionary. 
              Use the 'get' operation to check available keys before modifying or deleting.
            - Defaults to 'None' when using the 'get' operation.
        '''
    ] = None,
    path: Annotated[
        str, 
        '''Applicable for 'add' and 'modify' operations. This will be the path associated with the app name in the dictionary.
        '''
    ] = None
) -> str:
    
    ''' 
    This tool manages a dictionary of default paths for applications and important directories that have been previously opened. 
    You can use this tool to quickly retrieve paths for frequently used apps, allowing them to be opened faster.
    
    When the user requests to open an app, first use the "get" operation to check if the app is already stored in the default paths. 
    If found, open it directly; if not, utilize other tools like `update_search_list` and `files_opening_tool` to locate and open the app. 
    After opening the app, confirm with the user if it was opened correctly. If so, store the app name and path using the "add" operation. 
    
    For important directories like Desktop or Downloads, which are manually added by the user, the tool will only check their availability 
    and open them as needed. No modifications to these directories should be made by the tool.

    Remember when user asks to open any app or important directories like (Desktop, downloads etc.), you have to consider this tool first among others.
    '''
    if operation == 'get':
        available = f'The readily available apps/files and their paths are:\n'
        available += ('\n').join([f'{k} : {v}' for k, v in files_handler.default_paths.items()])
        return available
    
    if operation in ['add', 'modify']:
        if app_name is None:
            return 'App name is not given.'
        if path is None:
            return 'Path for app is not given.'
        path = os.path.normpath(path)
        files_handler.default_paths[app_name] = path 
        files_handler.save_default_paths()
        return f'The app is successfully updated in default paths.'
    
    if operation == 'delete':
        if app_name is None:
            return 'App name is not given.'
        del files_handler.default_paths[app_name]
        files_handler.save_default_paths()
        return f'The app is successfully deleted from default paths.'


############ Tool to refine search lists.
search_list = ['none',]
def empty_search_list():
    search_list.clear()
    search_list.append('none')

class LineListOutputParser(BaseOutputParser[List[str]]):
    """Output parser for a list of lines."""

    def parse(self, text: str) -> List[str]:
        lines = text.strip().split("\n")
        return list(filter(None, lines))      
     

@tool('Update_SearchList_Tool')
def update_search_list(
name : Annotated[str,'''The name of the file or directory the user asked for. This name is used for generating multiple names for searching in the available files from database. 
                 If the user doesn't mention any particular file or folder name, you can assume name by the task user want to do. For example if user wants to open some web search app, the name can be web search app.
                 Do not request assistance from the user unless you have already encountered a failure.'''],
n:Annotated[Literal['10','30'],'''The number of files/apps to retrive for each file/app the multi retriver generated. Choose 10 if user specifies file/app name. Choose 30 if user specified task name or user not sure about exact name.'''],
is_app : Annotated[Literal['True', 'False'],''' Set it to "True" if you are searching for app or browser (which can launch). Defaults to "False". ''']="False",                
)->List[str]:
    """
    Don't
    Updates the search list for the file, directory, folder or app based on the user query. 
    Whenever user asks to open for a file or directory, update the search list first using this tool instead of opening file directly.
    You can also use this tool for searching only if user don't know the exact name of file or folder. Otherwise do search with search tool.
    """
    output_parser = LineListOutputParser()
    

    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Your task is to generate five 
        different names of the given file name or directory name user asked to open or search for, to retrieve relevant files from a vector 
        database. By generating multiple names on the user asked file name, your goal is to help
        the user to retrieve the file the user intended. 
        If the user didn't specify a particular file or app name, you can generate different file/app names based on the task. For example for a web search app, the names can be "chrome", "microsoft edge", "opera" etc.
        Provide these alternative file names separated by newlines.
        User asked file or directory name: {question}""",
    )

    llm_chain = QUERY_PROMPT | llm | output_parser
    
    retriever = MultiQueryRetriever(
             retriever=files_handler.faiss_all_files.as_retriever(search_kwargs={"k": int(n)}), llm_chain=llm_chain, parser_key="lines"
                )  
    docs =retriever.invoke({'question':name})
    files_ = [doc.page_content for doc in docs]
    files = []
    for f in files_:
        if f not in files_handler.all_files:
            continue
        if eval(is_app):
            if (len(f)<4) or (f[-4:] not in ['.exe', '.lnk']):
                continue
        files.append(f)     
    empty_search_list()
    search_list.extend(files)
    paths = [files_handler.all_files_index.get(k,'none') for k in search_list]
    print('logs: The search list is updated.')
    return f'The available files and their paths are {[(a,k) for a,k in zip(search_list,paths)]}.'





#### Tool for searching files    
@tool('File_Searching_Tool')    
def search_files(
    name : Annotated[str,'''The name of object the user wants to search. '''],
)->str:     
    
    '''
Implements a search algorithm to find and display files or directories based on the name provided by the user. 
Use this tool only when the user requests to search for a specific file or folder by name. Do not use this tool for opening files or directories.
After obtaining the list of available files from this tool, display them neatly, each separated by a new line, and ask the user if they want to open any of these files.
    '''
    retriever = files_handler.faiss_all_files.as_retriever(search_kwargs={"k": 100})
    docs = retriever.invoke(name)
    files = [doc.page_content for doc in docs]
    paths = [files_handler.all_files_index.get(k,'none') for k in files]
    ans = f'The available files and their paths are:\n{('\n').join([f'{a} : {k}' for a,k in zip(files,paths)])}.'
    print(f'logs: {ans}')
    return ans

    

#### Tool to open file
@tool('File_Opening_Tool')
def open_file_or_dir(
    file_path : Annotated[str,'''Choose the final file or directory or app path to open from the available files. Choose file path as argument, not file name. Single file name may contain multiple paths, choose the appropriate one.
                        Ensure that the file type matches the user's request. For instance, if the user wants to open a PDF file, select a file with a ".pdf" extension. 
                        Important Point : If the user asks to open a app, select file either with ".exe" and ".lnk" extensions. If you find .lnk extension open directly otherwise think and open suitable one. 
                        For task specified files/apps, it's better you ask user to choose from the available files and apps. While showing available apps, don't display all the files. Display the unique files with the main file name the user can open.
                        No need to show options if the user specifies a file/app name instead of task unless user is not satisfied. You can open the file with relevant extension.
                        Select "none", if nothing from the list matches.
                          '''],
    file_name : Annotated[str,'''The file or directory or app name.'''],
    from_default_paths : Annotated[Literal['True', 'False'],''' Set it to "True" if you are opening file/app using default_paths. Defaults to "False". ''']="False",                 
                     
    )->str:
        
    """
    Opens a file or folder. Ensure that search list is updated before trying to open file or folder or directory with this tool.
    """
    if file_path == 'none':
        return f'Sorry, I am not able to find the given file. If you are sure that the file or directory exists, can you give some hint above where file or directory can be. The available files are {search_list}'
    else:
        try:
            os.startfile(file_path)
            if eval(from_default_paths):
                return f"Opened: {file_name}, path: {file_path} from default paths."
            return f"Opened: {file_name}, path: {file_path}. You can add it to default_paths if it is a app which is not in default_paths and user satisfies with this."
        except Exception as e:
            return f"Failed to open: {file_name}, path: {file_path}"
