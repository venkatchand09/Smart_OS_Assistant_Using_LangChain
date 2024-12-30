import os
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai import HarmBlockThreshold, HarmCategory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()



llm_gem = ChatVertexAI(model="gemini-1.5-flash",
                   project=os.getenv('GOOGLE_PROJECT_ID'),
                   max_retries=4,
                   temperature = 0.0,
                   safety_settings = {
  HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_ONLY_HIGH,                     
  HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
  HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
  HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
  HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}
  ) 
