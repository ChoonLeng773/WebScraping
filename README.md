# WebScraping
Web-scraping code

### Steps
Webscraping of the user reviews of each course in coursera happens in two parts. 
Firstly, we will need the URL of each course so that we can efficiently navigate the pages
Secondly for each course, we will check the number of pages of reviews there are and loop through that extracted number of pages to scrape from. 
The results will then be combined as a pandas dataframe and output as a CSV file. 

This extracted data is then processed for a sentiment analysis project for professors. 

### Rationale
Why Coursera? Udemy restricts webscraping whatsoever of its "property", and other platforms do not have that many reviews for us to work with to derive a large high quality dataset. Procuring data from a paid course is good for our use case as the reviews are mostly direct and honest from paying customers. 
Also, i love coursera and have audited many courses to gain valuable knowledge off the site. 

### Legend
Go_learn_url.py is the code that extracts out the URL of all the courses that we are examining
Next web_scrape_test1.py is the code that extracts out all of the reviews for each individual course using the CSV that we have acquired before
ccl_coursera_data.csv is the file containing the URL and other course descriptions 


### End Note
Have fun!
