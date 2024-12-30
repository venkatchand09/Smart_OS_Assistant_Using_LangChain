from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

if os.getenv('OPENAI_API_KEY')=='NONE':
    llm_gpt = None
else:    
    llm_gpt = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0,api_key = os.getenv('OPENAI_API_KEY'))
