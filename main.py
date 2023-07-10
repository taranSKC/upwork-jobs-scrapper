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


SEARCH_STRING = "React native"
encoded_string = quote(SEARCH_STRING)


jobs_data_list = []
file_path_ = 'data.xlsx'
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

    time.sleep(1)
    job_list_wrapper = WebDriverWait(driver, timeout=60, poll_frequency=1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test="job-tile-list"]')))
    print(job_list_wrapper, "job_list_wrapper")

    # section_elements = job_list_wrapper.find_elements(By.TAG_NAME, 'section')
    section_elements = WebDriverWait(job_list_wrapper, timeout=60).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, 'section'))
    )

    for section_element in tqdm(section_elements, desc="Processing jobs", unit="JOB"):

        if True:
            jobData = {
                "Job title": "",
                "Job Description": "",
                "Jobs Posted": 0,
                "Hiring rate": 0,
                "Job link": "",
                "Job duration": "",
                "Minimum Pay Rate": 0,
                "Maximum Pay Rate": 0,


            }
            #   Get Title of the Job
            header_wrapper = section_element.find_elements(
                By.CSS_SELECTOR, 'h3.job-tile-title')
            anchor_element = header_wrapper[0].find_element(
                By.CSS_SELECTOR, 'a')
            href = anchor_element.get_attribute('href')
            text = anchor_element.text

            response = scraper.get(href)
            # JOB Link
            jobData["Job link"] = href
            page = BeautifulSoup(response.content, 'html.parser')
            # JOB TITLE
            job_title = page.find('h1', class_='display-rebrand').text
            jobData["Job title"] = job_title

            # JOB DESCRIPTION
            job_description = page.find('div', class_='job-description').text
            jobData["Job Description"] = job_description

            # HIRING RATE
            client_about_wrapper = page.find(
                'ul', class_='cfe-ui-job-about-client-visitor')
            hire_rate_wrapper = client_about_wrapper.find(
                'li', attrs={'data-qa': 'client-job-posting-stats'})

            jobs_posted = hire_rate_wrapper.find('strong').text
            print(jobs_posted, "jobs_posted-0")
            if "jobs posted" in jobs_posted:
                jobs_posted = re.findall(
                    r'\d+', jobs_posted)[0] if len(re.findall(r'\d+', jobs_posted)) > 0 else 0
                print(jobs_posted, "jobs_posted-1")
                jobData["Jobs Posted"] = int(jobs_posted)
            # Hire rate in %age
            hire_percent_text = hire_rate_wrapper.find('div', class_='text-muted') or hire_rate_wrapper.find(
                'small', class_='text-muted') or hire_rate_wrapper.find('p', class_='text-muted')
            if hire_percent_text:
                hire_percent_text = hire_percent_text.text
                percentage = re.search(r'\d+%', hire_percent_text)
                if percentage:
                    percentage_value = percentage.group(0)
                    jobData['Hiring rate'] = percentage_value.replace("%", "")
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
                            prices_text = [price.text for price in all_prices]

                            _amounts = re.findall(
                                r'\$\d+\.\d+', " ".join(prices_text))
                            print(_amounts, "_amounts")
                            print(_amounts, "_amounts")
                            print(_amounts, "_amounts")
                            print(_amounts, "_amounts")
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

            excel_file_path = "data.xlsx"

            df.to_excel(excel_file_path, index=True)
            time.sleep(1)

    # Search for Next button, if it exist run the program again         #

    next_buttons = WebDriverWait(driver, timeout=60, poll_frequency=1).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button.up-pagination-item')))
    if len(next_buttons) > 0:

        for btn in next_buttons:
            if btn.text == "Next":
                if "disabled" in btn.get_attribute("class"):
                    print("The button is disabled.")
                else:
                    btn.click()
                    ScrapJobs()
                    break


# Set up Selenium

ScrapJobs()
