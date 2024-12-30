## Setup Instructions

Follow these steps to set up the project on your local machine.

### Prerequisites

- Python 3.x
- Gemini API credentials

### 1. Clone the Repository

Clone the repository to your local machine using Git:

git clone https://github.com/Poornakgps/Smart-OS.git
cd smart-os

### 2. Create and Activate a Virtual Environment

Create and activate a virtual environment to isolate your project dependencies.

- **On Windows:**

python -m venv env
.\env\Scripts\activate

- **On macOS/Linux:**

python3 -m venv env
source env/bin/activate

### 3. Install Dependencies

Install the necessary libraries and dependencies using the `requirements.txt` file:

pip install -r requirements.txt

### 4. Add Credentials to `.env` File

Create a `.env` file in the root of your project directory and add the following credentials:

GOOGLE_API_KEY=your_google_api_key

GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_application_credentials

GOOGLE_PROJECT_ID=your_google_project_id

BRAVE_API_KEY=your_brave_api_key (required if you want to do web-search)

DESKTOP=path_to_your_desktop

DOWNLOADS=path_to_your_downloads

OPENAI_API_KEY = open ai api key (If you want to use gpt 3.5 model, otherwise not needed)

### 5. Run the Application

Start the application using Streamlit:

streamlit run app.py

### 6. Use the Streamlit App

In the Streamlit app, you'll find three options in the sidebar:

- **Fetch all files:** Click this to retrieve all necessary files.
- **Create Embeddings:** Click this to generate embeddings. (Note: This process may take 2-3 hours.)
 No need to do update files.

Complete these steps.

# Smart-OS

Smart-OS is a chatbot-driven application designed to control your operating system with ease. The core idea is to manage various OS functions through a chatbot interface. Here are some key features:

- **System Control**: Adjust system brightness, search for or open applications and files.
- **File Search with FAISS**: The application uses FAISS embeddings for efficient file search. Embeddings for all files on your laptop are created and saved locally, which speeds up file retrieval compared to traditional name-based search. To create embeddings for all files, use the 'Fetch all files' and 'Create Embeddings' options in the Streamlit app when running it for the first time. Use 'Update all files' to refresh embeddings if files are added, deleted, or modified.
- **Application Launching**: The app can open various applications. Once an app is opened for the first time, it will be faster to open subsequently as paths are saved.
- **Settings and Commands**: The app can open different system settings and has access to the PowerShell terminal for executing commands.
- **GitHub Integration**: Push folders to GitHub with proper instructions.
- **Web and YouTube Search**: Perform web searches using Brave Search and search for YouTube URLs using the LangChain-YouTube tool.
- **URL Operations**: Open URLs and download images from them.
- **File Creation**: Create files with different extensions, such as .txt, .py, .html, etc.
- **Tool Visibility**: In the Streamlit app, use the 'Show Tools' option to view the underlying tool calls during execution.

For detailed setup instructions, please refer to the [Setup Instructions](#setup-instructions) section in this repository.


