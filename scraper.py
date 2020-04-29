from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import validators
import time
import requests
import os
from configparser import ConfigParser
import tkinter
from tkinter import messagebox
import sys

# Load the config 
configReader = ConfigParser()
configReader.read('config.ini')

if not os.path.exists('config.ini'):
    # This code is to hide the main tkinter window
    root = tkinter.Tk()
    root.withdraw()
    messagebox.showinfo("Error", "You must set up a config.ini file.\nCheck out the GitHub repo for a guide.")
    exit("No config file.")
    

config = {
    "Upload_Key" : configReader.get('main', 'key'),
    "Username" : configReader.get('main', 'utente'),
    "Password" : configReader.get('main', 'password'),
    "School_Code" : configReader.get('main', 'codice_scuola'),
    "Download_Directory" : configReader.get('main', 'download_dir'),
    "Group_Name" : configReader.get('main', 'group_name')
}


# Whatsapp Web Driver options.
WAoptions = Options()
WAoptions.add_argument("--window-size=1400,1000") # Of this size to make sure no mobile-size design changes happen.
WAoptions.add_experimental_option("detach", True)
WAoptions.add_argument("user-data-dir=./WAProfile") # To preserve the QR code scanning.
WAdriver = webdriver.Chrome(options=WAoptions)
WAdriver.get("https://web.whatsapp.com")


# Scraping Driver options.
options = Options()
prefs = {'download.default_directory' : config["Download_Directory"], 'profile.default_content_setting_values.automatic_downloads': 1}
options.add_experimental_option('prefs', prefs)
options.add_experimental_option("detach", True)
options.add_argument("--window-size=1400,1000") # Of this size to make sure no mobile-size design changes happen.
options.add_argument("user-data-dir=./ScraperProfile") # To bypass some Argo errors.
driver = webdriver.Chrome(options=options)


# Navigate the webpage, find the login section and log in using our config file.
def site_login():
    driver.get("https://www.argofamiglia.it/")
    driver.find_element_by_class_name("accedibutton").click()
    driver.find_element_by_id("codice_scuola").send_keys(config["School_Code"])
    driver.find_element_by_id("utente").send_keys(config["Username"])
    driver.find_element_by_id("j_password").send_keys(config["Password"])
    driver.find_element_by_name("submit").click()
    

# Navigate to the assignments panel.
def navigate_to_assignments():
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "_idJsp47"))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "bacheca"))).click()
    WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.ID, "sheet-bacheca:tree:scuola"))).click()
    time.sleep(2) # Complement with a bad wait to allow the "loading" popup to disappear.
    scrape_assignments()
        

# Get all assignments, filter them by unread, check for any URLs and files.
def scrape_assignments():

    assignments = driver.find_elements_by_css_selector("fieldset[style*='87CEEB']")

    for assignment in assignments:

        # Bad handling but hopefully temporary: Only let unread fieldsets (assignments) through. 
        try:
           internalLink = assignment.find_element_by_css_selector("a:not([style='FONT-WEIGHT: bold;'])")
        except WebDriverException:
            continue

        # Filter out the assignments that have the "enlistment" functionality.
        if not internalLink.text == "conferma presa visione":
            return

        # Add the assignment's elements to the variables that will be submitted to the group. File is null in case there will be none in future checks.
        subject = assignment.find_element_by_xpath(".//*/table/tr[1]/td[2]").text 
        message = assignment.find_element_by_xpath(".//*/table/tr[2]/td[2]").text
        file = None

        link_selector = "a[style='FONT-WEIGHT: bold;']"  # Used to locate any clickable links (URLs, Files).

        for assignment in assignment.find_elements_by_css_selector(link_selector):
            # If the clickable element is not a valid URL and isn't a whitespace, it is a file, so we download it and call our link replacement method.
            if not validators.url(assignment.text) and not assignment.text == '' and not assignment.text == ' ': 
                assignment.click()
                uploaded_file = upload_file(assignment.text)
                file = uploaded_file # Our new accessble to all link will be put in place of the internal hyperlink.
            else:
                # Due to how the platform works, even when there are none, the URL fields are always (for some reason) present and have a whitespace, we filter those out.
                if assignment.text == '' or assignment.text == '': 
                    url = None 
                else:
                    url = assignment.text

        internalLink.click() # Mark the assignment as read

        whatsapp_web(subject, message, file, url)


# Make a simple POST request to our file hosting service and return a new link.
def upload_file(filename):
    
    url = "https://lewd.cat/api/upload"
    file_path = config["Download_Directory"] + filename

    # Workaround to wait for the download to finish.
    while not os.path.exists(file_path):
        time.sleep(1)
    
    multipart_form_data = {
    'key': config["Upload_Key"],
    'action': (None, 'store'),
    'path': (None, '/path1')
    }
    files = {'file': open(file_path, 'rb')}

    r = requests.post(url, files=files, data=multipart_form_data)
    return r.json().get('url')

# Post the modified assignments to our class WhatsApp group.
def whatsapp_web(subject, message, file, url):
    footer = "--------------------------------------------------\nSono un bot e questa azione e' avvenuta in via automatica."


    text = f"Oggetto: {subject}\nMessaggio: {message}\nUrl: {url} \nFile: {file}\n\n{footer}"

    WebDriverWait(WAdriver, 10).until(EC.element_to_be_clickable((By.XPATH, f'//span[contains(@title,"{config["Group_Name"]}")]'))).click() # Look for group name.

    # Selenium takes new links as ENTER, thus sending them. Here we split the text into multiple parts and replace the newlines with SHIFT + ENTER (new line)
    for part in text.split('\n'):
        WebDriverWait(WAdriver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@spellcheck='true']"))).send_keys(part)
        ActionChains(WAdriver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.ENTER).key_up(Keys.SHIFT).perform()

    WebDriverWait(WAdriver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, '_35EW6'))).click() # Send the message off


site_login()
navigate_to_assignments()
