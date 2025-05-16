import requests
from bs4 import BeautifulSoup
import re

url = "https://papers.gceguide.cc/"

#Add config stuff

# accounting-(9-1)-(0985)/2021/0985_s21_ms_11.pdf
response = requests.get(url)

print("Status code:", response.status_code)
response.encoding = "utf-8"
soup = BeautifulSoup(response.text, 'html.parser') # Parse the text as html

# In between a and level, match any non-word character (i.e., symbol — not letter/digit/underscore)
alevel_regex = r"^.*a(?:[\W_]|%20)?Level.*"

alevel_pattern = re.compile(alevel_regex, re.IGNORECASE)
links = soup.find_all('a')
for link in links:
    if alevel_pattern.search(link.get('href')):
        print(link.get('href'))

if alevel_pattern.search("A%level"):
    print("success")
print('Done')

