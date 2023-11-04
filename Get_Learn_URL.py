from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

# Lists to store the scraped data in
course_title = []
course_organization = []
course_URL = []
course_rating = []
course_difficulty = []
course_duration = []
course_review_count = []
course_skills = []

############################################################################
# Testing done for one page
############################################################################

# my_url = "https://www.coursera.org/courses?productTypeDescription=Courses" # filter by courses,  ?page=1 first page

# test_url = "https://www.coursera.org/courses?productTypeDescription=Courses&page=1&index=prod_all_products_term_optimization"
# response = requests.get(test_url)
# html_soup = BeautifulSoup(response.content, 'html.parser')
# url = html_soup.find_all(href=True)
""" filtered_elements = [element for element in url if element.find('a', id='cds-react-aria-344-product-card-title')]
print(len(filtered_elements))
filtered_elements = [element for element in url if element.find('a', class_='cds-119 cds-113 cds-115 cds-CommonCard-titleLink css-si869u cds-142')]
print(len(filtered_elements)) """
# url = html_soup.find_all('div', class_ = 'cds-ProductCard-gridCard') # whole card = cds-ProductCard-gridCard : header = cds-ProductCard-header
# print("number of cards on the first page = ", len(url))

# Trial on one card
# card = url[0]

# print("the type of each card is ", type(url[0].find_all(href=True)))
# for card in url:
  # each card should have only one href
  # print(card.find(href=True).get("href"))
  # print([element.get("href") for element in card.find_all(href=True)])


############################################################################
# For all course pages in coursera
############################################################################

# for tallying data
total_courses = 0

def scrapeCourseraCourses(coursera_url, start_page, end_page): # num_pages needs to be manually sourced
  for i in range(start_page, end_page + 1): # inclusive of the last page
    try:
      page_url = coursera_url + "&page=" + str(i) + "&index=prod_all_products_term_optimization"
      page = requests.get(page_url)
      soup = BeautifulSoup(page.content, 'html.parser')
      scrapePage(soup, i)
    except requests.exceptions.ConnectionError:
      print("Connection error on page ", i)
    except requests.exceptions.Timeout:
      print("Request timed out. The server is taking too long to respond on page ", i)
    except AttributeError as e:
      # Handle the AttributeError
      print(f"AttributeError: {e} on page ", i)
    except:
      print("Error on page ", i)
      continue

############################################################################
# For all courses in a page (Max 12)
############################################################################

def scrapePage(page, page_count):
  list_of_cards = page.find_all('div', class_ = 'cds-ProductCard-gridCard')
  print("number of cards on page ", page_count, " = ", len(list_of_cards))
  global total_courses # some global variable nonsense
  total_courses += len(list_of_cards) # be careful of global variables
  # for each card in the page
  for card in list_of_cards:
    scrapeCard(card)

############################################################################
# Function for scraping one page
############################################################################

def scrapeCard(card):
  card_header = card.find("div", class_ = "cds-ProductCard-header")
  card_body = card.find("div", class_ = "cds-ProductCard-body")
  card_footer = card.find("div", class_ = "cds-ProductCard-footer")

  headers = headerExtract(card_header)
  course_title.append(headers["title"])
  course_organization.append(headers["organization"])
  course_URL.append(headers["link"])

  skills = skillsExtract(card_body)
  course_skills.append(skills)

  footers = footerExtract(card_footer)
  course_rating.append(footers["ratings"])
  course_review_count.append(footers["num_reviews"])
  course_difficulty.append(footers["difficulty"])
  course_duration.append(footers["duration"])
  # returns nothing, merely updates the global lists

############################################################################
# subfunctions for scraping one page
############################################################################

def headerExtract(card_header):
  course_link = card_header.find(href=True).get("href")
  course_org = card_header.find("p", class_ = "cds-119 cds-ProductCard-partnerNames css-dmxkm1 cds-121").get_text() # course organization: Stanford University
  course_title = card_header.find("h3", class_ = "cds-119 cds-CommonCard-title css-e7lgfl cds-121").get_text() # course title: Machine Learning
  return {"title" : course_title, "organization" : course_org, "link" : course_link}

def skillsExtract(card_body): # String returned
  # check if the body even exists in the card, else "" empty strings
  skills = ""
  if card_body is not None: 
    skills = card_body.find("div", class_ = "cds-CommonCard-bodyContent").get_text()[20:] # skills: xxd
    # might want to remove Skills: from the string -> since we are looking to reduce dimensionality

  return skills

def footerExtract(card_footer):
  ratings_dict = ratingsExtract(card_footer.find("div", class_ = "cds-CommonCard-ratings")) # {rating : 1.2, num_reviews : 4.5k reviews}
  meta_data_list = card_footer.find("div", class_ = "cds-CommonCard-metadata").get_text().split(" · ") # "Beginner · Course · 1 - 4 Weeks"
  difficulty = meta_data_list[0]
  course_type = meta_data_list[1] # redundant for our use case
  duration = meta_data_list[2]
  ratings_dict["difficulty"] = difficulty
  ratings_dict["duration"] = duration
  return ratings_dict # {rating : 1.2, num_reviews : 4500, difficulty : Beginner, duration : 1 - 4 Weeks}

def ratingsExtract(card_ratings):
  # RATINGS BAR IS NOT GUARNTEED TO EXIST
  ratings = ""
  reviews_count = 0

  page_element_rating = card_ratings.find("p", class_ = "cds-119 css-11uuo4b cds-121") # ratings: 4.5/5 cds-CommonCard-metadata
  page_element_review_count = card_ratings.find("p", class_ = "cds-119 cds-Typography-base css-dmxkm1 cds-121")

  if page_element_rating is not None:
    ratings = page_element_rating.get_text()

  if page_element_review_count is not None:
    rating_string = page_element_review_count.get_text()
    # text = "(72.9k reviews)"
    # print("rating_string = ", rating_string)
    string_num = re.findall(r'\d+\.\d+|\d+', rating_string)[0] # only one number
    if "k" in rating_string:
      reviews_count = int(float(string_num) * 1000) 
    else:
      reviews_count = int(string_num)

  return {"ratings" : ratings, "num_reviews" : reviews_count} # str, int

############################################################################
# Run the function
############################################################################

target_url = "https://www.coursera.org/courses?productTypeDescription=Courses"
first_page_num = 1 # 1
last_page_num = 84 # 4

scrapeCourseraCourses(target_url, first_page_num, last_page_num)

print("total courses captured = ", total_courses)

############################################################################
# Save to CSV 
############################################################################
# scrapeCard(card)
# scrapePage(html_soup)

courses_df = pd.DataFrame({'course_title': course_title,
                          'course_organization': course_organization,
                          'course_URL': course_URL,
                          'course_rating':course_rating,
                           'course_difficulty':course_difficulty,
                           'course_duration':course_duration,
                           'course_review_count':course_review_count,
                           'course_skills':course_skills})
# courses_df = courses_df.sort_values('course_title')

# here we take each lists we generated by scrapping and made a dataframe out of it isung pandas library.
# print(courses_df.head())

courses_df.to_csv('ccl_Coursera_Courses.csv') # empty csv file
