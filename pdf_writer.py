import re
from fpdf import FPDF
from langchain_core.tools import tool
from typing import Annotated
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'PDF Title', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_text(self, content):
        for line in content.split(r'\n'):
            if line.startswith('## '):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, line[3:], 0, 1)
                self.ln(4)
            elif line.startswith('* '):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, line[2:], 0, 1)
                self.ln(2)
            elif re.match(r'\*\*.*\*\*', line):
                bold_text = re.findall(r'\*\*(.*?)\*\*', line)
                regular_text = re.split(r'\*\*.*?\*\*', line)
                self.set_font('Arial', '', 12)
                for i in range(len(bold_text)):
                    self.cell(0, 10, regular_text[i], 0, 'L')
                    self.set_font('Arial', 'B', 12)
                    self.cell(0, 10, bold_text[i], 0, 'L')
                    self.set_font('Arial', '', 12)
                self.cell(0, 10, regular_text[-1], 0, 1)
            else:
                self.set_font('Arial', '', 12)
                self.multi_cell(0, 10, line)
                self.ln(2)


@tool('PDF_Writing_Tool')
def create_and_write_pdf_file(*,
    file_name: Annotated[str, 'Name of the file to be created. For example, for a content related to cricket news, file name can be "cricket_news.pdf"'],
    file_directory: Annotated[str, '''The directory where the file is to be created. If the user mentions a specific directory, find the path of that directory.
                             For example, if the user says create file in folder 'text' in 'D' drive, then the directory is "D:\\text". If the user does not mention any directory use the default directory of desktop from default_paths.
                             '''] ,
    content: Annotated[str, "The content to be written in the file"]
) -> None:
    '''
    Creates a PDF file in a given directory and writes the given content into it.
    '''
    try:
        # Ensure the directory exists
        os.makedirs(file_directory, exist_ok=True)
        
        # Create the full file path
        file_path = os.path.join(file_directory, file_name)
        
        # Create and write to the PDF file
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        
        # Split content by lines and add each line to the PDF
        for line in content.split(r'\n'):
            pdf.multi_cell(0, 10, line)
        
        pdf.output(file_path)
        print(f"{file_name} is created and content written successfully and is in the directory {file_directory}.")
    except Exception as e:
        print(f"An error occurred: {e}")
