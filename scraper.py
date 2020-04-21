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
import mysql.connector

# Whatsapp Web Driver options.
WAoptions = Options()
WAoptions.add_argument("--window-size=1400,1000")
WAoptions.add_experimental_option("detach", True)
WAoptions.add_argument("user-data-dir=C:\\Users\\Rithari\\Desktop\\Scraper\\WAProfile") # To preserve the QR code scanning.
WAdriver = webdriver.Chrome(options=WAoptions)
WAdriver.get("https://web.whatsapp.com")


# Scraping Driver options.
options = Options()
prefs = {'download.default_directory' : "C:\\Users\\Rithari\\Documents\\argo\\", 'profile.default_content_setting_values.automatic_downloads': 1}
options.add_experimental_option('prefs', prefs)
options.add_experimental_option("detach", True)
options.add_argument("--window-size=1400,1000")
options.add_argument("user-data-dir=C:\\Users\\Rithari\\Desktop\\Scraper\\ScraperProfile") # To bypass random Argo errors...
driver = webdriver.Chrome(options=options)


# Feeding the connection arguments to establish a route to the database. Sensitive data.
assignment_db = mysql.connector.connect(
    host = "REDACTED",
    user = "REDACTED",
    passwd = "REDACTED",
    database = "REDACTED"
)

# Form data for logging in to the platform. Sensitive data.
login_data = {
    "utente": "REDACTED",
    "j_password": "REDACTED",
    "cod_scuola": "REDACTED"
}


# Navigate the webpage, find the login section and log in using login_data.
def site_login():
    driver.get("https://www.argofamiglia.it/")
    driver.find_element_by_class_name("accedibutton").click()
    driver.find_element_by_id("codice_scuola").send_keys(login_data["cod_scuola"])
    driver.find_element_by_id("utente").send_keys(login_data["utente"])
    driver.find_element_by_id("j_password").send_keys(login_data["j_password"])
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
            assignment.find_element_by_css_selector("a:not([style='FONT-WEIGHT: bold;'])")
        except WebDriverException:
            continue

        # Add the assignment's elements to the variables that will be submitted to a database. File is null in case there will be none in future checks.
        db_subject = assignment.find_element_by_xpath(".//*/table/tr[1]/td[2]").text 
        db_message = assignment.find_element_by_xpath(".//*/table/tr[2]/td[2]").text
        db_file = None

        # Due to the nature of how we check if an assignment is unread, those who demand enlistment also come through. Since only one specific one does, we filter it out temporarily.
        if db_message == "Esercizi per sondare il grado attuale di conoscenze. (Prof. REDACTED FOR PRIVACY)":
            return


        link_selector = "a[style='FONT-WEIGHT: bold;']"  # Used to locate any clickable links (URLs, Files).

        for assignment in assignment.find_elements_by_css_selector(link_selector):
            # If the clickable element is not a valid URL and isn't a whitespace, it is a file, so we download it and call our link replacement method.
            if not validators.url(assignment.text) and not assignment.text == '' and not assignment.text == ' ': 
                assignment.click()
                uploaded_file = upload_file(assignment.text)
                db_file = uploaded_file # Our new accessble to all link will be put in place of the internal hyperlink.
            else:
                # Due to how the platform works, even when there are none, the URL fields are always (for some reason) present and have a whitespace, we filter those out.
                if assignment.text == '' or assignment.text == '': 
                    db_url = None 
                else:
                    db_url = assignment.text

        whatsapp_web(db_subject, db_message, db_file, db_url)


# Make a simple POST request to our file hosting service and return a new link. Sensitive data.
def upload_file(filename):
    
    url = "https://lewd.cat/api/upload"
    file_path = (f"C:\\Users\\Rithari\\Documents\\argo\\{filename}")

    # Workaround to wait for the download to finish.
    while not os.path.exists(file_path):
        time.sleep(1)
    
    multipart_form_data = {
    'key': 'REDACTED',
    'action': (None, 'store'),
    'path': (None, '/path1')
    }
    files = {'file': open(file_path, 'rb')}

    r = requests.post(url, files=files, data=multipart_form_data)
    return r.json().get('url')

# Update the database with our modified assignments.
def update_db(db_subject, db_message, db_file, db_url):

    cursor = assignment_db.cursor()
    sql = "INSERT INTO Assignments (subject, message, file, url, sent) VALUES (%s, %s, %s, %s, %i)"
    val = (db_subject, db_message, db_file, db_url, True)
    cursor.execute(sql, val)

    assignment_db.commit()


# Post the modified assignments to our class WhatsApp group.
def whatsapp_web(db_subject, db_message, db_file, db_url):
    footer = "--------------------------------------------------\nSono un bot e questa azione e' avvenuta in via automatica. Per info o preoccupazioni consulta il gruppo di classe.\n Source: https://github.com/Rithari/ScuolaNext-Scraper/"


    text = f"Oggetto: {db_subject}\nMessaggio: {db_message}\nUrl: {db_url} \nFile: {db_file}\n\n{footer}"

    WebDriverWait(WAdriver, 10).until(EC.element_to_be_clickable((By.XPATH, '//span[contains(@title,"Bacheca Materie")]'))).click() # Look for group name.

    # Selenium takes new links as ENTER, thus sending them. Here we split the text into multiple parts and replace the newlines with SHIFT + ENTER (new line)
    for part in text.split('\n'):
        WebDriverWait(WAdriver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@spellcheck='true']"))).send_keys(part)
        ActionChains(WAdriver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.ENTER).key_up(Keys.SHIFT).perform()

    WebDriverWait(WAdriver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, '_35EW6'))).click() # Send the message off
    update_db(db_subject, db_message, db_file, db_url) # Update the database.


site_login()
navigate_to_assignments()