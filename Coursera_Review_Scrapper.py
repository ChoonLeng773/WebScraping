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

# coursera = "https://www.coursera.org/learn/"
# course = "programming-languages-part-b" # need to convert the course name to this format
# review = "/reviews" # first page
# review = "/reviews?page=7"
# page_master = "?page="
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

############################################################################
# initialising data structures
############################################################################

df = pd.read_csv("ccl_Coursera_Courses.csv")

failed_df = pd.DataFrame() # empty dataframe

def addFailureRow(row):
    global failed_df # since when python got global shyt
    failed_df[len(failed_df.index)] = row # appending properly

# df = df.append(new_row, ignore_index=True)

############################################################################
# For one page of reviews -> max 25 reviews
############################################################################

def scrapeOnePage(soup_obj, skipped_stars): # skipped_stars = 2 for single pages only, 3 for subsequent pages
    # maximally 25 reviews per page
    reviews = []
    reviewer = [] # name of person doing the review
    star_ratings = []
    review_date = [] # if it helps

    star_html = soup_obj.find_all("div", class_ = "_1mzojlvw") # take note, reviewCards share the same star class name
    review_html = soup_obj.find_all("div", class_ = "reviewText") # class name reviewText -> .contents gets the child -> review
    reviewer_html = soup_obj.find_all("p", class_ = "cds-119 reviewerName p-x-1s css-dmxkm1 cds-121") # class name _1nxhdv7 -> .contents gets the child -> reviewer
    # print("length of star_html", len(star_html)) # 19
    # print("sample star : ", star_html[0].contents)
    # print("length of review_html", len(review_html)) # 16
    # print("length of reviewer_html", len(reviewer_html)) #16
    date_html = soup_obj.find_all("p", class_ = "cds-119 dateOfReview p-x-1s css-dmxkm1 cds-121") # class name _1nxhdv7 -> .contents gets the child -> reviewer
    # print(date_html)

    # there are 3 star objects before the actual reviews -> skip them -> see "https://www.coursera.org/learn/programming-languages-part-b/reviews?page=7"
    for i in range(0, 25): # 0 - 24
        if i == len(review_html):
            # print("stopped index = ", i)
            break # in case there are less than 25 reviews on this page

        # loop through to get the stars
        # print(star_html[i + 3].contents)
        # star_soup = BeautifulSoup(star_html[i + 3], 'html.parser') # for each star rating -> 3rd star onwards
        filled_star = star_html[i + skipped_stars].find_all("title") # filled star
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
        reviewer_text = reviewer_html[i].get_text()[3:] # remove "By "
        # print("reviewer", reviewer_text)
        reviewer.append(reviewer_text)
        # loop through get the review date
        review_date_text = date_html[i].get_text()
        # print("review date", review_date_text)
        review_date.append(review_date_text)
    # create dataframe
    dataframe = pd.DataFrame({'star_ratings': star_ratings, 'review': reviews, 'reviewer': reviewer, 'review_date': review_date})
    return dataframe

def determinePageType(soup_obj):
    index = 0
    if soup_obj.find("div", class_ = "rc-TopRatings") is not None:
        index += 2
    if soup_obj.find("div", class_ = "_1srkxe1s XDPRating m-y-2") is not None:
        index += 1
    return index

############################################################################
# Specifically for the first page of reviews -> get parameters
############################################################################

def getNumPages(soup_obj):
    # get the number of pages
    page_html = soup_obj.find("h2", class_ = "cds-119 m-y-2 text-secondary css-1diqjn6 cds-121") # class name page -> .contents gets the child -> page number
    # find out why i am unable to find the page
    overview = page_html.get_text() #
    num_reviews = extractNumber(overview)[2] # 3rd number is the number of reviews
    num_pages = num_reviews // 25 # 25 reviews per page
    remainder = num_reviews % 25 
    if remainder != 0:
        num_pages += 1
    return num_pages

def extractNumber(sentence):
    pattern = r'\d+'
    numbers = re.findall(pattern, sentence)
    numeric_values = [int(num) for num in numbers] # should be no float + i must only have 3 numbers
    if len(numeric_values) > 3: # for 4.5k reviews or even 1 million reviews
        final_num_str = ""
        for elem in numeric_values[2:]:
            final_num_str += str(elem)
        numeric_values = numeric_values[:3] # only take the first 3 numbers
        numeric_values[2] = int(final_num_str) # replace the last number with the full number
    print("numeric_values = ", numeric_values)
    return numeric_values

############################################################################
# For all reviews pages in coursera for one course
############################################################################# 
# note : # the most popular course on coursera has 399 functional pages of reviews

def reviewScrapper(data_frame_row): # a df row is a series
    # get first page to determine the amount of pages
    course_url = "https://www.coursera.org" + data_frame_row['course_URL'] + "/reviews"
    response = requests.get(course_url)
    html_soup = BeautifulSoup(response.content, 'html.parser') # works
    pages = getNumPages(html_soup) # for one page -> pages = 1, 
    print("pages = ", pages)

    # get top two reviews
    # featured_review_section = html_soup.find("div", class_ = "rc-TopRatings") # only one such element -> must exist
    # my_df = scrapeTopTwoReviews(featured_review_section) #  # not required because top two reviews are included
    my_df = pd.DataFrame() # empty dataframe

    for i in range(1, pages + 1): # include the last page
        try:
            response = requests.get("https://www.coursera.org" + data_frame_row['course_URL'] + "/reviews?page=" + str(i))
            html = BeautifulSoup(response.content, 'html.parser')
            skip_index = determinePageType(html)
            new_df = scrapeOnePage(html, skip_index)
            my_df = pd.concat([my_df, new_df], ignore_index=True) # supposedly faster than append
        except requests.exceptions.ConnectionError:
            addFailureRow(data_frame_row)
            print("Connection error on page ", i)
        except requests.exceptions.Timeout:
            addFailureRow(data_frame_row)
            print("Request timed out. The server is taking too long to respond on page ", i)

        # beautiful soup errors 
        except AttributeError as e:
            # Handle the AttributeError
            addFailureRow(data_frame_row)
            print(f"AttributeError: {e} on page ", i)
        except IndexError as e:
            addFailureRow(data_frame_row)
            print(f"IndexError: {e} on page ", i)
        except ValueError as e:
            addFailureRow(data_frame_row)
            print(f"ValueError: {e} on page ", i)
        except KeyError as e:
            addFailureRow(data_frame_row)
            print(f"KeyError: {e} on page ", i)
        except TypeError as e:
            addFailureRow(data_frame_row)
            print(f"TypeError: {e} on page ", i)

        except:
            addFailureRow(data_frame_row)
            print("Error on page ", i)
            continue # ignore the error and just move on

    print("done with course : ", data_frame_row["course_title"])
    print("Dataframe => ", my_df.shape[0], " x ", my_df.shape[1])

    # append the other columns of this row to my_df : 7 more columns
    my_df["course_title"] = data_frame_row["course_title"]
    my_df["course_organization"] = data_frame_row["course_organization"]
    my_df["course_rating"] = data_frame_row["course_rating"]
    my_df["course_difficulty"] = data_frame_row["course_difficulty"]
    my_df["course_review_estimate"] = data_frame_row["course_review_count"]
    my_df["course_duration"] = data_frame_row["course_duration"]
    my_df["course_skills"] = data_frame_row["course_skills"]
    my_df["course_URL"] = data_frame_row["course_URL"] # for debugging purposes

    return my_df

############################################################################
# Run the review scraping function for all courses
############################################################################

def run(dataframe):
    df_return = pd.DataFrame() # empty dataframe
    # for each course
    for index, row in dataframe.iterrows():
        # scrape the reviews
        df_return = pd.concat([df_return, reviewScrapper(row)], ignore_index=True)
    return df_return


# temp_df = run(df.head(2)) # second one has 1 page only
temp_df = run(df) # run for all courses
# temp_df = reviewScrapper(df.iloc[1]) # check for one page
temp_df.to_csv('ccl_Course_Reviews.csv') # empty csv file
failed_df.to_csv('failed_courses.csv') # check for failures to scrape later

# not all courses have featured reviews -> need to check for this

############################################################################
# debugging single page courses
############################################################################

# debug_url = "https://www.coursera.org/learn/generative-ai-for-everyone/reviews"

# debug_df = reviewScrapper(df.iloc[2]) # check for one course = "Become a CBRS Certified Professional Installer by Google"
# debug_df.to_csv('debug.csv')


# response = requests.get(debug_url)
# html = BeautifulSoup(response.content, 'html.parser')
# new_df = scrapeOnePage(html, 2)

# new_df.to_csv('debug.csv') # empty csv file
# failed_df.to_csv('failed_courses.csv') # empty csv file

# notes on single page courses 
# They do not have an overall rating thing for their course -> 

############################################################################
# redundant methods
############################################################################

def scrapeTopTwoReviews(top_ratings_soup):
    reviews = []
    reviewer = []
    star_ratings = []
    review_date = [] 
    star_html = top_ratings_soup.find_all("div", class_ = "_1mzojlvw") 
    review_html = top_ratings_soup.find_all("div", class_ = "reviewText") 
    reviewer_html = top_ratings_soup.find_all("p", class_ = "cds-119 reviewerName p-x-1s css-dmxkm1 cds-121")
    date_html = top_ratings_soup.find_all("p", class_ = "cds-119 dateOfReview p-x-1s css-dmxkm1 cds-121")
    for i in range(0, 2): # only 2 reviews
        if i == len(review_html):
            break # in case there are less than 25 reviews on this page

        filled_star = star_html[i].find_all("title") # filled star
        filtered_titles = [title for title in filled_star if title.get_text() == 'Filled Star']
        x = len(filtered_titles) # content is children
        print("number of stars = ", x)
        star_ratings.append(x)
        review_text = review_html[i].get_text()
        print("text review = ", review_text)
        reviews.append(review_text)
        reviewer_text = reviewer_html[i].get_text()[3:] # remove "By "
        print("reviewer = ", reviewer_text)
        reviewer.append(reviewer_text)
        review_date_text = date_html[i].get_text()
        print("review date = ", review_date_text)
        review_date.append(review_date_text)
    # create dataframe
    dataframe = pd.DataFrame({'star_ratings': star_ratings, 'review': reviews, 'reviewer': reviewer, 'review_date': review_date})
    return dataframe


def convertCourseName(course_name):
    # replace spaces with dash
    course_name = course_name.replace(" ", "-")
    # convert to lower
    course_name = course_name.lower()
    # remove characters that are not alphanumeric
    course_name = re.sub(r'[^A-Za-z0-9]+', '-', course_name)
    print(course_name)
    return course_name 

############################################################################
# Code below was all of the measures taken to evade udemy bot detection
############################################################################

gecko_path = "/Users/choonleng/Documents/Y3S1/BT4222/Webscrapping_trials/geckodriver"
path = "/Users/choonleng/Documents/Y3S1/BT4222/Webscrapping_trials/data"

udemy = "https://www.udemy.com/" # append the course id behind this
test_course = "289230" # course id 

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