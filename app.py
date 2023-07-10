import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import requests
from tqdm import tqdm
from urllib.request import Request, urlopen
import cloudscraper
import pandas as pd
import re
import os
from urllib.parse import quote


jobs_data_list = []


def extract_average_pay_rate(_string):

    # Define the regular expression pattern
    pattern = r"\$(\d+(\.\d+)?)"

    # Find the match in the string
    match = re.search(pattern, _string)

    if match:
        # Extract the price from the matched group
        price = match.group(1)

        return price
    else:

        return "NA"


def extract_total_spent(string__):

    # Define the regular expression pattern
    pattern = r"\$(\d+\.?\d*)([KkMmBb]?)"

    # Find the match in the string
    match = re.search(pattern, string__)

    if match:
        # Extract the price and scale from the matched groups
        price = match.group(1)
        scale = match.group(2)

        # Convert the price to a numeric value
        if scale.lower() == 'k':
            price = float(price) * 1000
        elif scale.lower() == 'm':
            price = float(price) * 1000000
        elif scale.lower() == 'b':
            price = float(price) * 1000000000

        return price
    else:
        print("No price found.")
        return 0


def extract_member_since(_string):
    pattern = r"Member since (\w{3} \d{1,2}, \d{4})"

# Find the match in the string
    match = re.search(pattern, _string)

    if match:
        # Extract the date from the matched group
        date = match.group(1)

        return date
    else:

        return ""


def start_scrapping():

    SEARCH_STRING = search_input.get()
    encoded_string = quote(SEARCH_STRING)

    file_path_ = SEARCH_STRING+" jobs" + '.xlsx'
    if os.path.exists(file_path_):
        # Delete the file
        os.remove(file_path_)
        print(f"The file '{file_path_}' has been deleted.")
    else:
        print(f"The file '{file_path_}' does not exist.")

    scraper = cloudscraper.create_scraper()

    chrome_options = Options()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    driver_service = Service('./chromedriver.exe')
    driver = webdriver.Chrome(service=driver_service, options=chrome_options
                              )

    # Replace with your desired website URL
    # driver.get('https://www.upwork.com/ab/account-security/login') # for login
    driver.get('https://www.upwork.com/nx/jobs/search/?q='+encoded_string +
               '&sort=recency&t=0&client_hires=1-9,10-&proposals=5-9,10-14,15-19,20-49&duration_v3=months,semester,ongoing&payment_verified=1&hourly_rate=20-')  # for login

    def ScrapJobs():
        try:
            dynamic_text.config(
                text=str(len(jobs_data_list))+" " + "Jobs scrapped")

            # time.sleep(1)
            job_list_wrapper = WebDriverWait(driver, timeout=60, poll_frequency=1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test="job-tile-list"]')))

            # section_elements = job_list_wrapper.find_elements(By.TAG_NAME, 'section')
            section_elements = WebDriverWait(job_list_wrapper, timeout=60).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'section'))
            )

            for section_element in tqdm(section_elements, desc="Processing jobs", unit="JOB"):

                if section_element:
                    jobData = {
                        "Job title": "",
                        "Job Description": "",
                        "Jobs Posted": 0,
                        "Hiring rate": 0,
                        "Job link": "",
                        "Job duration": "",
                        "Minimum Pay Rate": 0,
                        "Maximum Pay Rate": 0,
                        "Member since": "",
                        "Client Country": "",
                        "Total spent": "",
                        "Avgerage Pay rate": "NA",
                        "Total paid hours": 0,
                        "Posted on": ""
                    }
                    #   Get Title of the Job
                    header_wrapper = section_element.find_elements(
                        By.CSS_SELECTOR, 'h3.job-tile-title')
                    anchor_element = header_wrapper[0].find_element(
                        By.CSS_SELECTOR, 'a')
                    href = anchor_element.get_attribute('href')
                    text = anchor_element.text

                    # POSTED ON
                    posted_on = section_element.find_element(
                        By.CSS_SELECTOR, 'span[data-test="UpCRelativeTime"]')
                    if posted_on:
                        jobData['Posted on'] = posted_on.text

                    response = scraper.get(href)
                    # JOB Link
                    jobData["Job link"] = href
                    page = BeautifulSoup(response.content, 'html.parser')
                    # JOB TITLE
                    job_title = page.find('h1', class_='display-rebrand').text
                    jobData["Job title"] = job_title

                    # JOB DESCRIPTION
                    job_description = page.find(
                        'div', class_='job-description')
                    if job_description:
                        job_description = job_description.text
                        jobData["Job Description"] = job_description

                    # HIRING RATE
                    client_about_wrapper = page.find(
                        'ul', class_='cfe-ui-job-about-client-visitor')
                    if client_about_wrapper:
                        hire_rate_wrapper = client_about_wrapper.find(
                            'li', attrs={'data-qa': 'client-job-posting-stats'})

                        jobs_posted = hire_rate_wrapper.find('strong')

                        if jobs_posted:
                            jobs_posted = jobs_posted.text

                            if "jobs posted" in jobs_posted:
                                jobs_posted = re.findall(
                                    r'\d+', jobs_posted)[0] if len(re.findall(r'\d+', jobs_posted)) > 0 else 0

                                jobData["Jobs Posted"] = int(jobs_posted)

                    # Client Country
                    client_about_wrapper = page.find(
                        'ul', class_='cfe-ui-job-about-client-visitor')
                    country_wrapper = client_about_wrapper.find(
                        'li', attrs={'data-qa': 'client-location'})

                    client_country = country_wrapper.find('strong').text

                    jobData["Client Country"] = client_country

                    # TOTAL SPENT
                    client_about_wrapper = page.find(
                        'ul', class_='cfe-ui-job-about-client-visitor')
                    spent_tags = client_about_wrapper.find_all('li')
                    for tag in spent_tags:
                        total_spent_box = tag.find(
                            'strong', attrs={'data-qa': 'client-spend'})
                        if total_spent_box:
                            total_spent_text = extract_total_spent(
                                total_spent_box.text)
                            jobData['Total spent'] = total_spent_text
                            break

                    # AVERAGE PAY RATE
                    client_about_wrapper = page.find(
                        'ul', class_='cfe-ui-job-about-client-visitor')
                    avg_pay_rate_tags = client_about_wrapper.find_all('li')
                    for tag in avg_pay_rate_tags:
                        avg_pay_rate_box = tag.find(
                            'strong', attrs={'data-qa': 'client-hourly-rate'})

                        if avg_pay_rate_box:
                            avg_pay_rate_text = extract_average_pay_rate(
                                avg_pay_rate_box.text)
                            jobData['Avgerage Pay rate'] = avg_pay_rate_text

                            # Total hours paid
                            hours_paid = tag.find(
                                'div', attrs={'data-qa': 'client-hours'}) or tag.find(
                                'span', attrs={'data-qa': 'client-hours'}) or tag.find(
                                'p', attrs={'data-qa': 'client-hours'})
                            if hours_paid:
                                hours_paid_text = hours_paid.text
                                jobData['Total paid hours'] = hours_paid_text.replace(
                                    ",", "", 3).replace("s", "", 3).replace("hour", "", 3)

                            break

                    # Hire rate in %age
                    hire_percent_text = hire_rate_wrapper.find('div', class_='text-muted') or hire_rate_wrapper.find(
                        'small', class_='text-muted') or hire_rate_wrapper.find('p', class_='text-muted')
                    if hire_percent_text:
                        hire_percent_text = hire_percent_text.text
                        percentage = re.search(r'\d+%', hire_percent_text)
                        if percentage:
                            percentage_value = percentage.group(0)
                            jobData['Hiring rate'] = percentage_value.replace(
                                "%", "")
                    # JOB DURATION
                    job_detail_wrapper = page.find(
                        'ul', class_='cfe-ui-job-features')
                    li_tags = job_detail_wrapper.find_all('li')
                    for li in li_tags:
                        duration_text = li.find('small', class_='text-muted') if li.find(
                            'small', class_='text-muted') else li.find('p', class_='text-muted')
                        if duration_text:
                            if "Duration" in duration_text.text:
                                duration = li.find('strong').text
                                jobData["Job duration"] = duration
                                break

                    # MEMBER SINCE
                    client_about_ = page.find(
                        'div', class_='cfe-about-client-v2')
                    small_tags = client_about_.find_all(
                        'small', class_='text-muted')
                    for tag in small_tags:
                        if "Member" in tag.text:
                            member_since_data = extract_member_since(tag.text)
                            jobData['Member since'] = member_since_data
                            break
                    # PAY RATE
                    job_detail_wrapper = page.find(
                        'ul', class_='cfe-ui-job-features')
                    li_tags = job_detail_wrapper.find_all('li')
                    for li in li_tags:
                        pay_rate_text = li.find('small', class_='text-muted') if li.find(
                            'small', class_='text-muted') else li.find('p', class_='text-muted')
                        if pay_rate_text:
                            if "Hourly" in pay_rate_text.text:
                                if "$" in li.find('strong').text:
                                    pay_rate = li.find('strong').text
                                    payrates = li.find('div', class_='d-flex')

                                    all_prices = li.find_all('strong')
                                    prices_text = [
                                        price.text for price in all_prices]

                                    _amounts = re.findall(
                                        r'\$\d+\.\d+', " ".join(prices_text))

                                    if len(_amounts) == 1:
                                        jobData['Minimum Pay Rate'] = _amounts[0].replace(
                                            "$", "")
                                    if len(_amounts) == 2:
                                        jobData['Minimum Pay Rate'] = _amounts[0].replace(
                                            "$", "")
                                        jobData['Maximum Pay Rate'] = _amounts[1].replace(
                                            "$", "")

                                    # jobData["Job duration"] = duration
                                    break

                    # ---------++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    jobs_data_list.append(jobData)
                    df = pd.DataFrame.from_records(
                        jobs_data_list,

                    )

                    excel_file_path = file_path_

                    df.to_excel(excel_file_path, index=True)
                    # time.sleep(1)

            # Search for Next button, if it exist run the program again         #

            next_buttons = WebDriverWait(driver, timeout=60, poll_frequency=1).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button.up-pagination-item')))
            if len(next_buttons) > 0:

                for btn in next_buttons:
                    if btn.text == "Next":
                        if "disabled" in btn.get_attribute("class"):
                            print("Scrapping Done")
                        else:
                            btn.click()
                            ScrapJobs()
                            break

        # Set up Selenium
        except Exception as e:
            print("error happended",e)
            ScrapJobs()

    ScrapJobs()


def cancel_button_clicked():

    # Display a message box
    messagebox.showinfo("Cancel", "Bye Bye")

    # Close the modal
    window.destroy()


window = tk.Tk()
window.title("Scrapper")
window.geometry("350x350")

label = tk.Label(window, text="Type job name to scrap:")
label.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

search_input = tk.Entry(window, width=40)
search_input.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


# Create a save button
save_button = tk.Button(window, text="Start", command=start_scrapping)
save_button.place(relx=0.3, rely=0.6, anchor=tk.CENTER)

# Create a cancel button
cancel_button = tk.Button(window, text="Cancel", command=cancel_button_clicked)
cancel_button.place(relx=0.7, rely=0.6, anchor=tk.CENTER)

dynamic_text = tk.Label(window, text="")
dynamic_text.place(relx=0.5, rely=0.8, anchor=tk.CENTER)

# Run the main event loop
window.mainloop()
