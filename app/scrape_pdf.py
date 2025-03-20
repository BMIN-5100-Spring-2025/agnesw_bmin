import requests
import re
from PyPDF2 import PdfReader

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# }

pdf_url = "https://www.accessdata.fda.gov/cdrh_docs/pdf24/K240369.pdf"

# Create a session to handle requests and potential redirects
session = requests.Session()
session.max_redirects = 100

# Download the PDF file
response = session.get(pdf_url)

# Save the PDF locally
pdf_filename = "document.pdf"
with open(pdf_filename, "wb") as f:
    f.write(response.content)
print("PDF downloaded successfully.")

# Read the downloaded PDF
reader = PdfReader(pdf_filename)

# Extract text from all pages
full_text = ""
for page in reader.pages:
    extracted_text = page.extract_text()
    if extracted_text:  # Ensure text is not None
        full_text += extracted_text + "\n"

# Define regex pattern to find FDA K-numbers (e.g., K240369)
k_number_pattern = r"K\d{6}"

# Find all matches in the extracted text
k_numbers = re.findall(k_number_pattern, full_text)

# Print extracted K-numbers
if k_numbers:
    print("Extracted K-numbers:", k_numbers)
else:
    print("No K-numbers found in the document.")
