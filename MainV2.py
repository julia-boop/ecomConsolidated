#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#IMPORTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import pandas as pd
import smtplib
import os
import gspread
import openpyxl
import tempfile
import time
import base64
import re
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime, timedelta
import smtplib
import glob
from email.message import EmailMessage
from email.utils import formataddr
import mimetypes
import os
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import os
import pathlib
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from weasyprint import HTML
from datetime import datetime

#For production
# import chromedriver_autoinstaller
# chromedriver_path = chromedriver_autoinstaller.install()
# service = Service(chromedriver_path)

user_data_dir = tempfile.mkdtemp()
script_dir = os.path.dirname(os.path.abspath(__file__))
download_path = os.path.join(script_dir, 'orderOperations')
downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(download_path, exist_ok=True)


chrome_options = Options()
#chrome_options.add_argument("--headless")  
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
#For develpment
chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

#For production
# chrome_options.binary_location = "/usr/bin/chromium"
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "directory_upgrade": True,
    "safebrowsing.enabled": True
})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#GET LOGIWA FILE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def wait_for_download_to_finish(download_path, timeout=1200):
    """
    Waits until the download folder has no .crdownload or .part files (indicating download in progress).
    """
    seconds = 0
    while seconds < timeout:
        files = os.listdir(download_path)
        if any(file.endswith(('.crdownload', '.part')) for file in files):
            time.sleep(1)
            seconds += 1
        else:
            return True
    raise TimeoutError("Download did not complete within timeout.")

def get_latest_file(directory):
    valid_extensions = ('.xlsx', '.xls', '.csv')  # add .csv if needed
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(valid_extensions)
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def get_logiwa_file():

    driver.get("https://app.logiwa.com/en/Login")

    username_field = driver.find_element(By.ID, "UserName")
    password_field = driver.find_element(By.ID, "Password")

    print(username_field)
    print(password_field)

    time.sleep(3)

    user = os.getenv("LOGIWA_USERNAME")
    password = os.getenv("LOGIWA_PASSWORD")

    username_field.send_keys(user)
    password_field.send_keys(password)

    login_button = driver.find_element(By.ID, "LoginButton")
    login_button.click()

    time.sleep(3)

    login_handle = None

    try:
        login_handle = driver.find_element(By.CSS_SELECTOR, ".bootbox-body")
    except Exception as e:
        print("No login handle needed")

    if login_handle:
        buttons = driver.find_elements(By.CLASS_NAME, "btn-success")
        for b in buttons:
            text = b.text
            if text == "Ok":
                b.click()
                time.sleep(3)
    else:
        print("No login handle needed")
    
    driver.get("https://app.logiwa.com/en/WMS/OrderCarrierManagement")

    time.sleep(3)

    date_input = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/form/div/div[2]/div/div[2]/div[2]/div/input")
    today = datetime.today()

    if today.weekday() == 0:  
        start_date = today - timedelta(days=3)  
    else:
        start_date = today - timedelta(days=1) 
    start_date_str = start_date.strftime("%m.%d.%Y")
    today_str = today.strftime("%m.%d.%Y")
    date_input_string = f"{start_date_str} 00:00:00 - {today_str} 23:59:59"
    # date_input_string = "07.03.2025 00:00:00 - 07.07.2025 23:59:59"
 
    date_input.send_keys(date_input_string)

    # job_input = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/form/div/div[1]/div[2]/div[8]/div[2]/input")
    # job_input.send_keys("J1304579")

    search_btn = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[1]/button[1]")
    search_btn.click()

    time.sleep(5)

    download_btn = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/div[2]/div[1]/div/div[5]/div/table/tbody/tr/td[1]/table/tbody/tr/td[1]/div/span")    
    download_btn.click()

    time.sleep(10)
    wait_for_download_to_finish(download_path)
    time.sleep(10)

    driver.quit()
    
    latest_file = get_latest_file(download_path)

    if latest_file:
        print(f"Latest download file: {latest_file}")
        return latest_file
    else:
        print(f"No files found in the directory {download_path}")
        return

file = get_logiwa_file()

# file = "/Users/juliacordero/Documents/Python/EcomContent/orderOperations/cincin.xlsx"


def process_file(file):
    if not file:
        print("No file to process.")
        return None

    if file.endswith('.xlsx') or file.endswith('.xls'):
        df = pd.read_excel(file)
    elif file.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        print("Unsupported file format.")
        return None

    df.columns = [col.strip() for col in df.columns]

    print(df.columns)
    print(df.head())

    # Step 1: Filter by "Order Type"
    order_type_col = 'Order Type'
    df[order_type_col] = df[order_type_col].astype(str).str.strip().str.title()
    df = df[df[order_type_col].isin(["E-Commerce Order", "Shopify Order"])]

    # Step 2: Filter by "Order Status"
    order_status_col = 'Order Status'
    df[order_status_col] = df[order_status_col].astype(str).str.strip().str.title()
    df = df[df[order_status_col].isin(["Entered", "Started", "Picked", "Partially Picked", "Approved", "Partially Packed"])]
    

    # Step 3: Format "Job Code"
    job_code_col = 'Job Code'
    df[job_code_col] = df[job_code_col].astype(str).apply(lambda x: x.split(" ")[0])
    df[job_code_col] = df[job_code_col].replace("nan", "")
    df = df[~df[job_code_col].isna() & (df[job_code_col].astype(str).str.strip() != '')]



    df = df.sort_values(by=["Client", "Job Code", "Customer Order #"]).reset_index(drop=True)

    # Step 4: Keep only specified columns
    keep_columns = [
        "Client",
        "Logiwa Order #",
        "Customer Order #",
        "Customer",
        "Job Code"]
    df = df[keep_columns]

    # Step 5: Generate barcode images and store <img> tags
    barcode_dir = 'barcodes'
    os.makedirs(barcode_dir, exist_ok=True)

    # Add barcode columns
    df.insert(df.columns.get_loc("Logiwa Order #") + 1, "Logiwa Barcode", "")
    df.insert(df.columns.get_loc("Job Code") + 1, "Job Barcode", "")

    for idx, row in df.iterrows():
        # Logiwa Barcode
        logiwa_order = str(row["Logiwa Order #"])
        if pd.notna(logiwa_order) and logiwa_order.strip() != "":
            logiwa_filename = os.path.join(barcode_dir, f"logiwa_{idx}")
            absolute_path = pathlib.Path(logiwa_filename).resolve().as_uri()
            barcode.get('code128', logiwa_order, writer=ImageWriter()).save(logiwa_filename)
            df.at[idx, "Logiwa Barcode"] = f'<img src="{absolute_path}.png" style="max-height:95px; max-width:300px; width:200px;" />'
        else:
            df.at[idx, "Logiwa Barcode"] = ''

        # Job Barcode
        job_code = str(row["Job Code"])
        if pd.notna(job_code) and job_code.strip() != "":
            job_filename = os.path.join(barcode_dir, f"job_{idx}")
            absolute_path = pathlib.Path(job_filename).resolve().as_uri()
            barcode.get('code128', job_code, writer=ImageWriter()).save(job_filename)
            df.at[idx, "Job Barcode"] = f'<img src="{absolute_path}.png" style="max-height:80px; max-width:250px;" />'
        else:
            df.at[idx, "Job Barcode"] = ''

    print(f"Processed DataFrame with barcode image paths:\n{df.head()}")

    return df

def generate_pdf_reports_per_client(df, output_dir='reports'):
    os.makedirs(output_dir, exist_ok=True)

    css = """
    <style>
        @page {
            size: A4 landscape;
            margin: 20mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 16px;
        }
        h2 {
            text-align: center;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            table-layout: fixed;
        }
        th, td {
            border: 1px solid #ddd;
            text-align: center;
            padding: 8px;
        }
        th {
            background-color: #f2f2f2;
        }
        .barcode {
            font-family: 'Code 128', monospace;
        }
        th:nth-child(2), td:nth-child(2) {
            width: 150px;
        }
        th:nth-child(3), td:nth-child(3) {
            width: 300px;
        }
        thead {
            display: table-header-group;
        }
    </style>
    """

    for client, client_df in df.groupby("Client"):
        safe_client_name = client.replace(" ", "_").replace("/", "-")
        output_html = os.path.join(output_dir, f"{safe_client_name}_report.html")
        output_pdf = os.path.join(output_dir, f"{safe_client_name}_report.pdf")

        html_table = client_df.to_html(index=False, escape=False)
        full_html = f"""
        <html>
        <head>
        {css}
        </head>
        <body>
            <h2>E-Commerce Orders - {client} - {datetime.today().strftime('%m-%d-%Y')}</h2>
            {html_table}
        </body>
        </html>
        """

        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"HTML report saved at {output_html}")

        try:
            HTML(output_html).write_pdf(output_pdf)
            print(f"PDF report saved at {output_pdf}")
        except Exception as e:
            print(f"Error converting HTML to PDF for {client}: {e}")

# Example usage:
processed_df = process_file(file)
if processed_df is not None:
    generate_pdf_reports_per_client(processed_df)


def send_reports_via_email(
    to_email,
    subject,
    body="test",
    reports_folder='reports'
):
    """
    Sends all PDFs in the reports folder as attachments via email.
    """
    # Compose the email
    msg = EmailMessage()
    msg['From'] = formataddr(('E-Commerce Reports', os.getenv("SENDER_EMAIL")))
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    # Attach all PDF files in the reports folder
    pdf_files = glob.glob(os.path.join(reports_folder, '*.pdf'))
    if not pdf_files:
        print("No PDF reports found to attach.")
        return

    for pdf_path in pdf_files:
        with open(pdf_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(pdf_path)
            msg.add_attachment(
                file_data,
                maintype='application',
                subtype='pdf',
                filename=file_name
            )
            print(f"Attached {file_name}")

    # Send the email
    try:
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT")) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(os.getenv("SENDER_EMAIL"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
            print(f"Email sent to {to_email} with {len(pdf_files)} attachments.")
    except Exception as e:
        print(f"Error sending email: {e}")


send_reports_via_email(
    # to_email='595RPV344J@hpeprint.com',
    to_email='jcordero@the5411.com',
    subject='E-Commerce Order Packing Lists',
)
