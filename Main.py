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
from selenium.common.exceptions import TimeoutException
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
import pathlib
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from datetime import datetime
from flask import send_file
from io import BytesIO
import io
import os


#For production
import chromedriver_autoinstaller

user_data_dir = tempfile.mkdtemp()
script_dir = os.path.dirname(os.path.abspath(__file__))
download_path = os.path.join(script_dir, 'orderOperations')
downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(download_path, exist_ok=True)

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


def get_logiwa_file(job_code=None, date=None, client=None, progress_callback=None):

    chromedriver_path = chromedriver_autoinstaller.install()
    service = Service(chromedriver_path)

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    #For develpment
    # chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    #For production
    # chrome_options.binary_location = "/usr/bin/chromium"
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    # service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    if progress_callback:
        progress_callback("🔐 Logging in to Logiwa...")

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

    if progress_callback:
        progress_callback("🔄 Redirecting to order operations...")    
    
    driver.get("https://app.logiwa.com/en/WMS/OrderCarrierManagement")

    time.sleep(20)  

    print("Anda el print")
    if job_code is not None:
        if progress_callback:
            progress_callback("🧑🏼‍💻 Filtering by job code...")  
        job_input = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/form/div/div[1]/div[2]/div[8]/div[2]/input")
        job_input.send_keys(job_code)
        print("Llego hasta job code")

    time.sleep(10)

    if client is not None:
        if progress_callback:
            progress_callback("📩 Filtering by client...")  
        wait = WebDriverWait(driver, 15)
        client_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/form/div/div[1]/div[2]/div[14]/div[2]/div/button")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", client_button)
        client_button.click()
        time.sleep(1) 
        client_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/form/div/div[1]/div[2]/div[14]/div[2]/div/ul/li[1]/div/input"))
        )
        client_input.clear()
        client_input.send_keys(client)
        client_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/form/div/div[1]/div[2]/div[14]/div[2]/div/ul/li[1]/div/input")))
        client_input.send_keys(client)
        client_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li[contains(@class, 'ui-sortable')]//label[contains(., '{client}')]")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", client_option)
        client_option.click()
        print("Llego hasta client")

    time.sleep(3)

    search_btn = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[1]/button[1]")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
    search_btn.click()

    time.sleep(5)

    if progress_callback:
            progress_callback("📁 Downloading file...")  

    download_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "/html/body/div[1]/div[2]/div/div/div[3]/div[2]/div[1]/div/div[5]/div/table/tbody/tr/td[1]/table/tbody/tr/td[1]/div/span"
        ))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_btn)
    driver.execute_script("arguments[0].click();", download_btn)

    time.sleep(10)
    wait_for_download_to_finish(download_path)
    time.sleep(10)

    driver.quit()
    
    latest_file = get_latest_file(download_path)

    if latest_file:
        print(f"[DEBUG] Latest downloaded file: {latest_file}")
        
        with open(latest_file, "rb") as f:
            file_bytes = f.read()

        os.remove(latest_file)  # Cleanup to avoid saving locally
        return BytesIO(file_bytes)
    else:
        print(f"[ERROR] No files found in the directory {download_path}")
        return None


def process_file(file, progress_callback=None):

    if progress_callback:
            progress_callback("🧩 Generating consolidated report...")  

    if not file:
        print("No file to process.")
        return None

    if isinstance(file, io.BytesIO):
        try:
            file.seek(0)
            df = pd.read_excel(file)
        except Exception as e:
            print("Error reading in-memory Excel file:", e)
            return None
    elif isinstance(file, str):
        ext = os.path.splitext(file)[1].lower()
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file)
        elif ext == '.csv':
            df = pd.read_csv(file)
        else:
            print("Unsupported file format.")
            return None
    else:
        print("Invalid file type.")
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
            barcode.get_barcode_class('code128')(logiwa_order, writer=ImageWriter()).save(logiwa_filename)
            df.at[idx, "Logiwa Barcode"] = f'<img src="{absolute_path}.png" style="max-height:95px; max-width:300px; width:200px;" />'
        else:
            df.at[idx, "Logiwa Barcode"] = ''

        # Job Barcode
        job_code = str(row["Job Code"])
        if pd.notna(job_code) and job_code.strip() != "":
            job_filename = os.path.join(barcode_dir, f"job_{idx}")
            absolute_path = pathlib.Path(job_filename).resolve().as_uri()
            barcode.get_barcode_class('code128')(logiwa_order, writer=ImageWriter()).save(logiwa_filename)
            df.at[idx, "Job Barcode"] = f'<img src="{absolute_path}.png" style="max-height:80px; max-width:250px;" />'
        else:
            df.at[idx, "Job Barcode"] = ''

    print(f"Processed DataFrame with barcode image paths:\n{df.head()}")

    return df
