#Importing required libraries/packages
from bs4 import BeautifulSoup
import requests
import pandas as pd
import math
from datetime import datetime,timedelta
import re
from datetime import datetime, timedelta

#function that accepts a string in relative time format and returns a datetime 
def convert_relative_time(relative_time):
    if "hour" in relative_time:
        hours_ago = int(relative_time.split()[0])
        return datetime.now() - timedelta(hours=hours_ago)
    elif "day" in relative_time:
        days_ago = int(relative_time.split()[0])
        return datetime.now() - timedelta(days=days_ago)
    elif "week" in relative_time:
        weeks_ago = int(relative_time.split()[0])
        return datetime.now() - timedelta(weeks=weeks_ago)
    elif "month" in relative_time:
        months_ago = int(relative_time.split()[0])
        # Assuming a month has 30 days for simplicity
        return datetime.now() - timedelta(days=months_ago * 30)
    else:
        try:
            return datetime.strptime(relative_time, "%b %d, %Y")
        except ValueError:
            return None

import re
import re

#function that accepts a string and returns a cleaned-up version of that string
def clean_salary(salary_str):
    # Remove unwanted characters from the salary string
    print(salary_str)
    salary_str = salary_str.replace('Estimated:', '').replace('$', '').replace(',', '').strip()

    # Check if 'hourly' is present in the salary string
    is_hourly = 'hour' in salary_str.lower()
    is_k= 'K' in salary_str.upper()

    # Define regular expressions to handle different salary formats
    pattern_yearly_range = r'(\d{1,7}(?:,\d{7})*(?:\.\d+)?)(?:K)?\s*-\s*(\d{1,7}(?:,\d{7})*(?:\.\d+)?)(?:K)?\s*a\s*year'
    pattern_single_yearly = r'(\d{1,7}(?:,\d{7})*(?:\.\d+)?)(?:K)?\s*a\s*year'
    pattern_hourly_range = r'(\d{1,7}(?:,\d{7})*(?:\.\d+)?)(?:K)?\s*-\s*(\d{1,7}(?:,\d{7})*(?:\.\d+)?)(?:K)?\s*an\s*hour'
    pattern_single_hourly = r'(\d{1,7}(?:,\d{7})*(?:\.\d+)?)(?:K)?\s*an\s*hour'

    # Try to match each pattern to extract salary values
    match_yearly_range = re.search(pattern_yearly_range, salary_str, re.IGNORECASE)
    match_single_yearly = re.search(pattern_single_yearly, salary_str, re.IGNORECASE)
    match_hourly_range = re.search(pattern_hourly_range, salary_str, re.IGNORECASE)
    match_single_hourly = re.search(pattern_single_hourly, salary_str, re.IGNORECASE)

    if match_yearly_range:
        min_salary_str = match_yearly_range.group(1).replace(',', '')
        max_salary_str = match_yearly_range.group(2).replace(',', '')
        min_salary = float(min_salary_str)
        max_salary = float(max_salary_str)
        if is_k:
            min_salary *= 1000
            max_salary *= 1000
        return "USD {:,.2f} - {:,.2f} a year".format(min_salary, max_salary), min_salary, max_salary
    elif match_single_yearly:
        salary_str = match_single_yearly.group(1).replace(',', '')
        salary = float(salary_str)
        if is_k:
            salary *= 1000
        return "USD {:,.2f} a year".format(salary), salary, salary
    elif match_hourly_range:
        min_salary_str = match_hourly_range.group(1).replace(',', '')
        max_salary_str = match_hourly_range.group(2).replace(',', '')
        min_salary = float(min_salary_str)*40 * 52
        max_salary = float(max_salary_str)*40 * 52
        if is_k:
            min_salary *= 1000
            max_salary *= 1000
        return "USD {:,.2f} - {:,.2f} a year".format(min_salary, max_salary), min_salary, max_salary
    elif match_single_hourly:
        salary_str = match_single_hourly.group(1).replace(',', '')
        salary = float(salary_str)*40 * 52
        if is_k:
            salary *= 1000
        return "USD {:,.2f} a year".format(salary), salary, salary
    else:
        # If no salary value is found, return "N/A"
        return "N/A", None, None

#function that accepts a URL and returns the BeautifulSoup object
def scrape_page(url):
    # response = requests.get(url, params={"cursor": cursor})
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup

#function that accepts a BeautifulSoup object and a page number, and returns the URL for the next page
def get_cursor(soup, next_page_num):
    cursor = soup.find('a', {'class':'chakra-link css-1wxsdwr', 'aria-label': f'page {next_page_num}'})
    if cursor:
        return cursor.get('href')
    else:
        return None
        

#function that accepts a URL and a list of job post elements, and returns a list of URLs 
def get_job_links(url, list_elems):
    job_links = []
    for item in list_elems:
        job_key = item.div.get('data-jobkey')
        job_link = f'{url}&job={job_key}'
        job_links.append(job_link)
    return job_links


#function that accepts a page URL and a search keyword, and returns a list of dictionaries representing job post data for that page
def scrape_one_page(url, soup,key):
    ul = soup.find_all('ul', id='job-list')
    li = ul[0].find_all('li', {'class': 'css-0'})
    job_links = get_job_links(url, li)
    data_list = []
    for job_link in job_links:
        print(job_link)
        job = scrape_page(job_link)
        job_title = job.h2.text.strip()
        company = job.find('span', {'data-testid': 'viewJobCompanyName'}).text if job.find('span', {'data-testid': 'viewJobCompanyName'}) else "N/A"
        location = job.find('span', {'data-testid': 'viewJobCompanyLocation'}).text if job.find('span', {'data-testid': 'viewJobCompanyLocation'}) else "N/A"
        job_type = job.find('span', {'data-testid': 'viewJobBodyJobDetailsJobType'}).text if job.find('span', {'data-testid': 'viewJobBodyJobDetailsJobType'}) else "N/A"
        salary = job.find('span', {'data-testid': 'viewJobBodyJobCompensation'}).text if job.find('span', {'data-testid': 'viewJobBodyJobCompensation'}) else "N/A"
        posted_on = job.find('span', {'data-testid': 'viewJobBodyJobPostingTimestamp'}).text if job.find('span', {'data-testid': 'viewJobBodyJobPostingTimestamp'}) else ""
        job_qualification = job.find('div', {'data-testid': 'viewJobQualificationsContainer'})
        if job_qualification:
            ul_element = job_qualification.find('ul')
            if ul_element:
                job_qualification = list(ul_element.strings)
                job_qualification = [x.strip() for x in job_qualification]
                job_qualification = "\n".join(job_qualification)
            else:
                job_qualification = "N/A"
        else:
            job_qualification = "N/A"

        job_description = job.find('div', {'data-testid': 'viewJobBodyJobFullDescriptionContent'})
        if job_description:
            job_description = list(job_description.strings)
            job_description = [x.strip() for x in job_description]
            job_description = "\n".join(job_description)
        else:
            job_description = "N/A"   

        data = {
            'job_title': job_title,
            'company': company,
            'location': location,
            'job_type': job_type,
            'salary': salary,
            'posted_on': posted_on,
            'job_qualification': job_qualification,
            'job_description': job_description,
            'job_link': job_link,
            'job_site':"simply hired",
            'keyword' :key
        }
        posted_on_date = convert_relative_time(posted_on)
        if isinstance(posted_on_date, datetime):
            data['posted_on_date'] = posted_on_date.strftime("%Y-%m-%d")
        else:
            data['posted_on_date'] = "N/A" 

        print(data['posted_on_date'])    
        data_list.append(data)

    return data_list

job = 'Data Engineer'
location = 'USA'
data_up_to = 7  #last seven days

url = f'https://www.simplyhired.com/search?q={job}&l={location}&t={data_up_to}'
next_page = url

soup = scrape_page(url)
number_of_jobs = soup.find('div', {'data-testid':'headerSerpJobCount'}).p.text
number_per_page = len(soup.find_all('ul', {'id':'job-list'})[0]\
        .find_all('li', {'class':'css-0'}))
number_of_pages = math.ceil(int(number_of_jobs)/int(number_per_page))
print({'number_of_jobs': number_of_jobs, 'number_per_page': number_per_page, 'number_of_pages': number_of_pages})

i=1
df = pd.DataFrame(columns=['job_title', 'company', 'location', 'job_type', 'salary', 'posted_on', 'job_qualification', 'job_description'])
while next_page != None:
    print('Page Number:', i, ' Page Link: ', next_page)
    soup = scrape_page(next_page)
    page_data = scrape_one_page(next_page, soup,job)
    df = df.append(page_data)

    i = i+1
    next_page = get_cursor(soup, i+1)
    
print("Complete")
df['salary'], df['min_salary'], df['max_salary'] = zip(*df['salary'].apply(clean_salary))
df['rating'] = df['company'].str.extract(r'([0-9.]+)')
df['company'] = df['company'].str.replace(r'-\s*\d+\.\d+', '', regex=True).str.strip()

# Convert 'rating' column to numeric, set non-numeric values as "N/A"
df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna("N/A")

df.to_csv('simply_hired3.csv',index=False)
