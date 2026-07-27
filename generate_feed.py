import requests
from bs4 import BeautifulSoup

url = "https://www.cert-in.org.in/s2cMainServlet?pageid=VLNLIST02&year=2026"

html = requests.get(url).text

soup = BeautifulSoup(html,"lxml")

# parse rows
