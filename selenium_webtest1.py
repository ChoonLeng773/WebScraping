from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.proxy import Proxy, ProxyType
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re

df = pd.read_csv("coursea_data.csv")
peek = df.head(10)
# print(peek)

gecko_path = "/Users/choonleng/Documents/Y3S1/BT4222/Webscrapping_trials/geckodriver"
path = "/Users/choonleng/Documents/Y3S1/BT4222/Webscrapping_trials/data"

udemy = "https://www.udemy.com/" # append the course id behind this
test_course = "289230" # course id 

coursera = "https://www.coursera.org/learn/"
course = "programming-languages-part-b" # need to convert the course name to this format
# review = "/reviews" # first page
review = "/reviews?page=7"
page_master = "?page="
# subsequent pages ?page=2 -> 2, 3 ... until cannot find page

# response = requests.get(coursera + course + review)

# html_soup = BeautifulSoup(response.content, 'html.parser')
# print(html_soup.title)

# html_lines = html_soup.split('\n')
# Print the first few lines
# for line in html_lines[:10]:
#     print(line)
# print(html_soup.prettify())
# reviewText
def scrapeOnePage(soup_obj):
    # maximally 25 reviews per page
    reviews = []
    reviewer = [] # name of person doing the review
    star_ratings = []
    review_date = [] # if it helps

    star_html = soup_obj.find_all("div", class_ = "_1mzojlvw") # take note, reviewCards share the same star class name
    review_html = soup_obj.find_all("div", class_ = "reviewText") # class name reviewText -> .contents gets the child -> review
    reviewer_html = soup_obj.find_all("p", class_ = "cds-119 reviewerName p-x-1s css-dmxkm1 cds-121") # class name _1nxhdv7 -> .contents gets the child -> reviewer
    print("length of star_html", len(star_html)) # 19
    # print("sample star : ", star_html[0].contents)
    print("length of review_html", len(review_html)) # 16
    print("length of reviewer_html", len(reviewer_html)) #16
    date_html = soup_obj.find_all("p", class_ = "cds-119 dateOfReview p-x-1s css-dmxkm1 cds-121") # class name _1nxhdv7 -> .contents gets the child -> reviewer
    # print(date_html)

    # there are 3 star objects before the actual reviews -> skip them -> see "https://www.coursera.org/learn/programming-languages-part-b/reviews?page=7"
    for i in range(0, 25): # 0 - 24
        if i == len(review_html):
            break # in case there are less than 25 reviews on this page

        # loop through to get the stars
        # print(star_html[i + 3].contents)
        # star_soup = BeautifulSoup(star_html[i + 3], 'html.parser') # for each star rating -> 3rd star onwards
        filled_star = star_html[i + 3].find_all("title") # filled star
        # print("filled star : ", filled_star)
        # filtered_titles = [title for title in filled_star if title.get('id') == 'FilledStar14c0e8ce-6327-404e-9721-c99375339db9']
        filtered_titles = [title for title in filled_star if title.get_text() == 'Filled Star']
        # print("filtered_titles : ", filtered_titles)
        x = len(filtered_titles) # content is children
        # print("number of stars", x)
        star_ratings.append(x)
        # loop through to get the review
        review_text = review_html[i].get_text()
        # print("text review", review_text)
        reviews.append(review_text)
        # loop through to get the reviewer
        reviewer_text = reviewer_html[i].get_text()
        # print("reviewer", reviewer_text)
        reviewer.append(reviewer_text)
        # loop through get the review date
        review_date_text = date_html[i].get_text()
        # print("review date", review_date_text)
        review_date.append(review_date_text)
    # create dataframe
    dataframe = pd.DataFrame({'star_ratings': star_ratings, 'review': reviews, 'reviewer': reviewer, 'review_date': review_date})
    return dataframe

# dataframe_yay = scrapeOnePage(html_soup)
# print(dataframe_yay)

# cds-119 m-y-2 text-secondary css-1diqjn6 cds-121

def getNumPages(soup_obj):
    # get the number of pages
    page_html = soup_obj.find_all("h2", class_ = "cds-119 m-y-2 text-secondary css-1diqjn6 cds-121") # class name page -> .contents gets the child -> page number
    # print(page_html)
    overview = page_html[0].get_text()
    num_reviews = extractNumber(overview)[2] # 3rd number is the number of reviews
    num_pages = num_reviews // 25 # 25 reviews per page
    remainder = num_reviews % 25 
    if remainder != 0:
        num_pages += 1
    return num_pages

def extractNumber(sentence):
    pattern = r'\d+'
    numbers = re.findall(pattern, sentence)
    numeric_values = [int(num) for num in numbers] # should be no float
    return numeric_values

# print(getNumPages(html_soup))

# dataframe_yay.to_csv("Coursera_Reviews.csv", index=True)

def convertCourseName(course_name):
    # replace spaces with dash
    course_name = course_name.replace(" ", "-")
    # convert to lower
    course_name = course_name.lower()
    # remove characters that are not alphanumeric
    course_name = re.sub(r'[^A-Za-z0-9]+', '-', course_name)
    print(course_name)
    return course_name 

def reviewScrapper(course_name):
    # get first page to determine the amount of pages
    web_course_name = convertCourseName(course_name)
    response = requests.get(coursera + web_course_name + "/reviews")
    # the most popular course on coursera has 399 functional pages of reviews
    html_soup = BeautifulSoup(response.content, 'html.parser')
    pages = getNumPages(html_soup)
    my_df = scrapeOnePage(html_soup)

    for i in range(2, pages + 1): # include the last page
        response = requests.get(coursera + web_course_name + "/reviews?page=" + str(i))
        html = BeautifulSoup(response.content, 'html.parser')
        new_df = scrapeOnePage(html)
        my_df = pd.concat([my_df, new_df], ignore_index=True) # supposedly faster than append
        # my_df = my_df.append(new_df, ignore_index=True)

    return my_df

# then loop through each course name in the dataframe to give us a good dataset
test_df = reviewScrapper("Programming Languages, Part B")
test_df.to_csv("Coursera_Reviews.csv", index=True)

""" prox = Proxy()
prox.proxy_type = ProxyType.MANUAL
prox.http_proxy = "http://JUSTgiveMEtheDataForResearchYo:5639"
prox.ssl_proxy = "http://JUSTgiveMEtheDataForResearchYo:5639" """

""" options = webdriver.FirefoxOptions()
options.add_argument("start-maximized")
# options.add_argument('--proxy-server=http://JUSTgiveMEtheDataForResearchYo:5639')
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('excludeSwitches', ['enable-logging'])
# options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')
options.headless = False
options.add_argument("--disable-extensions")

# Initialize the web driver with options
driver = webdriver.Firefox(options=options)

# do wtv we need to here
website = coursera + course + review # full weblink
driver.get(website)

show_review_button_class = "ud-btn ud-btn-medium ud-btn-secondary ud-heading-sm reviews--trigger-button-container--2E_X0"
css_rev_btn = f".{show_review_button_class.replace(' ', '.')}"

show_more_btn_class = "ud-btn ud-btn-medium ud-btn-secondary ud-heading-sm reviews-modal--show-more-reviews-button--3Erii reviews-modal--full-width-button--2drNv"
css_show_more_btn = f".{show_more_btn_class.replace(' ', '.')}"

# Use explicit wait to wait for the element with the specified class name
#wait = WebDriverWait(driver, 10)
#element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, show_review_button_class)))

# button_element = driver.find_element_by_css_selector(f".{show_review_button_class.replace(' ', '.')}")
# button_element = driver.find_elements(By.CLASS_NAME, show_review_button_class)
button_element = driver.find_element(By.CSS_SELECTOR, css_rev_btn)
print("length of the elements found: ", len(button_element))
button_element[0].click()

# inner button -> keep clicking to show all reviews
while True:
    try:
        # Locate the button element by its class name
        # button_element = driver.find_element_by_css_selector(f".{show_more_btn_class.replace(' ', '.')}")
        button_element = driver.find_elements(By.CLASS_NAME, show_more_btn_class)
        # Click the button
        button_element.click()
    except NoSuchElementException:
        # The button was not found, exit the loop
        break

tell_done = input("Done?") 
if tell_done == "yes":
    print("Done")

# Close the browser when done
driver.quit() """