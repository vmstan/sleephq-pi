################################################################################################################
# Python3 script to run on the Raspberry Pi upload the latest data to SleepHQ / Dropbox                        #
# This is a work in progress!                                                                                  #
# v0.3                                                                                                         #
# Written by Erik Reynolds (https://github.com/grumpymaker/sleephq-pi)                                         #
################################################################################################################

import time
import zipfile
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Path to the configuration file
configFilePath = 'config.txt'

# Read the configuration file
with open(configFilePath, 'r') as file:
    lines = file.readlines()
    for line in lines:
        key, value = line.strip().split('=')
        if key == 'cpapDataDirectoryPath':
            cpapDataDirectoryPath = value
        elif key == 'o2DataDirectoryPath':
            o2DataDirectoryPath = value
        elif key == 'sleepUsername':
            sleepUsername = value
        elif key == 'sleepPassword':
            sleepPassword = value

# Check if variables were set correctly
if not all([cpapDataDirectoryPath, sleepUsername, sleepPassword]):
    print("ERROR: Configuration not set correctly. Check the config file.")
    exit()

# Create a zip file from the directory
zipFilePath = '/tmp/data.zip'
with zipfile.ZipFile(zipFilePath, 'w') as zipf:
    for root, _, files in os.walk(cpapDataDirectoryPath):
        for file in files:
            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), cpapDataDirectoryPath))

# Set the dataFilePath variable to the created zip file
dataFilePath = zipFilePath

driver = webdriver.Chrome()
driver.get('https://sleephq.com/users/sign_in')
time.sleep(5) # Let the user actually see something!

# Check to see if we're on the login page, else we're already logged in
if driver.current_url == 'https://sleephq.com/users/sign_in':
    print("Logging in...")
    username_input = driver.find_element(By.ID, 'user_email')
    password_input = driver.find_element(By.ID, 'user_password')
    submit_button = driver.find_element(By.TAG_NAME, 'button')

    username_input.send_keys(sleepUsername)
    time.sleep(2)
    password_input.send_keys(sleepPassword)
    time.sleep(2)
    submit_button.click()
    time.sleep(5) # give it a second to login and redirect

# We should be logged in now and on the dashboard page, grab the URL to check (and extract the teams ID)
dashboardURL = driver.current_url
print("Dashboard URL: " + dashboardURL)

# Check the dashboard URL to see if it matches the expected format (https://sleephq.com/account/teams/123456)
if not dashboardURL.startswith('https://sleephq.com/account/teams/'):
    print("ERROR: Unexpected URL format, expected https://sleephq.com/account/teams/123456")
    driver.quit()
    exit()

# Extract the teams ID from the end of the URL
teamID = dashboardURL.split('/')[-1]
print("teams ID: " + teamID)

# Now we can go to the upload page
driver.get('https://sleephq.com/account/teams/' + teamID + '/imports')

fileUploadField = driver.find_element(By.XPATH, '//input[@type="file" and @class="dz-hidden-input"]')
fileUploadField.send_keys(dataFilePath)
time.sleep(5) # give it a few to grab the file

print("Uploading the datafile...")
beginUploadButton = driver.find_element(By.ID, 'start-upload-button')
beginUploadButton.click()

# Give it 60 seconds to upload the file before quitting
time.sleep(60)
print("Done! Closing the browser...")
driver.quit()