import re
import os
import shutil
import zipfile
import winshell
from send2trash import send2trash
from langchain_core.tools import tool
from typing import Annotated
from typing import Annotated, Literal, List
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

##### To deal With File Operations like copy, move, delete, rename etc.
class FileOperations(object):

    def __init__(self,operation,file_names,file_paths,target_file_names,destination_directory):
        self.operation = operation
        self.file_names = file_names
        self.file_paths = file_paths
        self.target_file_names = target_file_names
        self.destination_directory = destination_directory
        self.logs = f'''Logs: '''
        if self.destination_directory and (not os.path.exists(self.destination_directory)):
            os.makedirs(self.destination_directory)
    

    def copy_files(self):
        for src in self.file_paths:
            shutil.copy(src, self.destination_directory)
            self.logs += f'''\n{src} is copied to {self.destination_directory}'''


    def copy_folders(self):
        for src, file in zip(self.file_paths,self.file_names):
            shutil.copytree(src, os.path.join(self.destination_directory,file),dirs_exist_ok=True)
            self.logs += f'''\n{src} is copied to {self.destination_directory}'''

    def move(self):
        for src in self.file_paths:
            shutil.move(src, self.destination_directory)
            self.logs += f'''\n{src} is moved to {self.destination_directory}'''

    def rename(self):
        for src,original_file,target_file in zip(self.file_paths,self.file_names,self.target_file_names):
            dst = os.path.join(os.path.dirname(src),target_file)
            os.rename(src, dst)
            self.logs += f'''\n{original_file} is renamed to {target_file}'''

    def delete_permanent(self):
        for path in self.file_paths:  
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            self.logs += f'''\n{path} is deleted permanently.'''    


    def delete_temporary(self):
        for path in self.file_paths:
            path = os.path.normpath(path)
            send2trash(path)
            self.logs += f'''\n{path} is deleted temporarily.''' 

    def zip_files(self):


        zip_path = os.path.join(self.destination_directory, self.target_file_names[0])
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in self.file_paths:
                zipf.write(file, arcname=os.path.basename(file))   
        self.logs += f'''\nThe files are zipped and saved into {zip_path}'''     


    def unzip_files(self):
        for zip_name in self.file_paths:
            with zipfile.ZipFile(zip_name, 'r') as zipf:
                zipf.extractall(self.destination_directory)
            self.logs += f'''\nThe file {zip_name} is unzipped and saved into {self.destination_directory}'''    


    def create_shortcut(self):
        for src,original_file,target_file in zip(self.file_paths,self.file_names,self.target_file_names):   
            path = os.path.join(self.destination_directory,target_file)
            winshell.CreateShortcut(
                Path=path,
                Target=src,
                Icon=(src, 0)
            )
            self.logs+= f'''\nShortcut is created for {original_file} in {self.destination_directory}.'''

    def execute(self):
        eval(f'self.{self.operation}')()
        return self.logs      
    
  
@tool('Files_Altering_Tool')
def alter_files(*,
operation : Annotated[Literal['copy_files','copy_folders','move','rename','delete_permanent','delete_temporary','zip_files','unzip_files','create_shortcut'],
                      '''The type of operation to do.
                         copy_files: To copy files
                         copy_folders: To copy folders
                         move : To move files or folders
                         rename : To rename files or folders
                         delete_permanent : To delete files or folders permanently
                         delete_temporary : To delete files or folders temporarily (send to recycle bin)
                         zip_files : to zip files or folders
                         unzip_files : to unzip file
                         create_shortcut : to create shortcuts for files.
                          
                            '''],
file_names : Annotated[List[str],''' The list of file names that the operation will be applied to. '''],   
file_paths : Annotated[List[str],''' The list of file paths corresponding to the file names. If there are files with duplicate names (i.e., the same name but located at different paths) and user wants them to be included, ensure that the duplicate file names are included in the file_names argument and their respective paths are listed in this argument. '''],
target_file_names : Annotated[List[str],'''The list of target file names.
                                          Applicable for operations rename, create shortcut and zip. 
                                          For rename, don't change the extension of the file. Ex: newname.pdf for original pdf file.
                                          For create shortcut, use .lnk extension.
                                          For zip operation, use .zip extension and there should be only one element in the list.

                             ''']=None,
destination_directory : Annotated[str,''' The directory where the altered files are saved.
                                  Applicable only for operations copy, move, zip, unzip and create shortcuts. All the altered files are saved in this directory.
                                  Default directory is given for the desktop directory.
                                  ''']=os.getenv('DESKTOP'),

)->str:
    '''

    This tool can copy, move, rename, delete, create shortcuts, zip, and unzip files or folders. 
    Update search list for the file user wants and always confirm with the user about the file they are going to alter and the specific change. 
    Always ask for destination folder if applicable. If the user do not mention any directory, use given default desktop directory.
    For delete operation, always ask to delete temporarily or permanently.
    The tool can only perform one operation on multiple files at a time, so you need to call it again for each additional operation.
    For cases where there are multiple input files, the specified operation will be performed separately on each file, except for the zip operation. When zipping files, all files in the list will be zipped together in a single operation.
    '''

    FileOperation = FileOperations(operation,file_names,file_paths,target_file_names,destination_directory)
    logs = FileOperation.execute()
    return logs




#### To deal with creation, modification and reading of different types of files.

@tool('File_Editor')
def file_editor(
    operation : Annotated[Literal['create','modify','read'],'''Choose the type of operation to perform on the file:
                                                            create : To create a new file or overwrite an existing one.
                                                            modify : To update an existing file by appending new content without erasing the current content.
                                                            read : To read the contents of the file.
                                                                '''],
    file_path : Annotated[str,'The path of the file to perform the operation on. For file creation, specify the path as "directory/file_name".'],
    content : Annotated[str,'The content to be written to the file. Defaults to "None" if operation is read.'] = None                                                    

)->str:
    
    ''' 
    This tool handles operations on text-based file formats like .txt, .py, .json, and more.
    It allows you to create, read, modify, and overwrite files.
    To overwrite an existing file, choose 'create' as the "operation" argument.
    Select 'modify' to append new content to an existing file without removing the old content.
    '''
    if operation=='read':
        with open(file_path, 'r') as file:
            return file.read()
    if content:    
        content = re.sub(r'\\+', r'\\', content)
        content += '\n'
        content = content.replace(r'\n', '\n')
        if operation=='create':
            with open(file_path, 'w') as file:
                file.write(content)
            return f'The file {file_path} is created/overwritten.' 
        if operation=='modify':
            with open(file_path, 'a') as file:
                file.write(content)
            return f'The file {file_path} is modified with new content.'
    else: 
        return f'No content is given.'       
