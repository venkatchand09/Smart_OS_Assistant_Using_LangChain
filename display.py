import tkinter as tk
import threading
import subprocess
from langchain_core.tools import tool
from typing import Annotated
import time

class SimpleGUI:
    def __init__(self):
        self.root = None
        self.text_widget = None
        self._thread = None
        self._stop_event = threading.Event()
        self._gui_running = False

    def _run_gui(self):
        # Initialize the GUI
        self.root = tk.Tk()
        self.root.title("Simple GUI")

        # Create a Text widget
        self.text_widget = tk.Text(self.root)
        self.text_widget.pack(fill=tk.BOTH, expand=True)  # Fill the entire window

        # Bind the window close event to a method
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start the Tkinter main loop
        self._gui_running = True
        self.root.mainloop()

    def _on_close(self):
        # Handle window close event
        print("GUI window closed manually.")
        self._gui_running = False
        self.root.quit()
        self.root = None

    def open(self):
        if self.root is not None:
            #print("GUI already open.")
            return

        # Create and start the GUI thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_gui)
        self._thread.start()
        #self.update('GUI opened.')
        time.sleep(1)
        print("GUI opened.")

    def update(self, text):
        if self.root is None or not self._gui_running:
            print("GUI is not open.")
            return

        # Use Tkinter's after method to safely update the GUI from the main thread
        self.root.after(0, self._update_text, text)

    def _update_text(self, text):
        if self.text_widget is not None:
            self.text_widget.insert(tk.END, text + "\n")
            self.text_widget.yview(tk.END)  # Scroll to the end

    def close(self):
        if self.root is None:
            print("GUI is not open.")
            return

        # Signal the GUI thread to stop
        self._stop_event.set()
        self.root.quit()
        self._thread.join()
        self.root.destroy()
        self.root = None
        self._thread = None
        self._gui_running = False


gui = SimpleGUI()


@tool('Get_GitHub_Instructions')
def github_push_instructions()->str:

    ''' 
    This tool gives instructions to push a project to github. When user asks to push a project into github, get instructions from this tool first and then proceed as instructed. Don't ask user to execute the git commnads himself. You do it with these instructions.
    '''

    inst = ''' When user asks to push a folder to github, you do the following         
Step 1: Obtain the folder directory `(dir)` to be pushed, along with the GitHub username `(username)` and repository name `(repo)`.
Step 2: Execute the following Git commands one after the other using the `run_command` tool, ensuring that `(dir)` is used as the `working_directory` argument for each command. Do not use `cd {dir}`—it's unnecessary. Push to the main branch unless user specified some other branch.
        1) git init
        2) git add .
        3) git commit -m "(message)"
        4) git branch -M main
        4) git remote add origin (url)
        5) git push -u origin main
If you encounter any uncertainties during execution, such as whether to add all files or specific ones, or which branch to use (main or another), consult with the user. If an error occurs in the terminal, analyze it and take the appropriate action. If you cannot resolve it, ask the user for guidance. Always execute the commands sequentially, one after the other.
           '''
    return inst


@tool('Run_Command')
def run_command(
 command:Annotated[str,'''Determine the command to execute in the powershell terminal based on the user's task requirements.'''],
 working_directory:Annotated[str,'''The directory where the command should be executed. Use this argument whenever you need to run a command in a directory other than the default. The default is none.''']=None
)->str:
    
    '''
    You can use this tool to get file names in directories, get data related to system and apps etc.(not limited to), anything you can do with commands.
    This tool executes a single command at a time in the powershell terminal. 
    Use it whenever a task can be accomplished solely through the powershell terminal. 
    Execute the commands yourself as much as possible without asking the user to do them manually. 
    Note that changes made by a command are not retained for subsequent commands. Therefore, if multiple objectives depend on each other, you need to provide all necessary commands in a single operation.       
    For example there is no use of cd dir. Instead pass directory as argument each time you execute command.
    For more complex tasks, such as pushing folders to GitHub, you may need the user's assistance.
    '''
    
    if working_directory:
        final_command = f'Set-Location -Path "{working_directory}"; {command}'
    else:
        final_command = command

    result = subprocess.run(['powershell', '-Command', final_command], capture_output=True, text=True)
    stdout, stderr = result.stdout, result.stderr

    printer = f'\ninput command: {command}\noutput:{stdout}\nerrors:{stderr if stderr else 'none'}\n'

    gui.open()
    gui.update(f"-----------------------------------------------------------------------------{printer}")
    return printer
