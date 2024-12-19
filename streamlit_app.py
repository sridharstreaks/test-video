import streamlit as st
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time  # To allow time for JavaScript to execute
import requests
import json
import requests
from lxml import html

payload = {
'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
'Accept-Language': 'da, en-gb, en',
'Accept-Encoding': 'gzip, deflate, br',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
'Referer': 'https://www.google.com/'
}

############################################### Functions used to fetch inital links ####################################################

def movie_search(keyword): #gives search results for each search #1
    url=f"https://www.movies-da.net/mobile/search?find={keyword.replace(' ','+')}&per_page=1"
    response = requests.get(url)
    if response.status_code==200:
        dictionary={}
        time.sleep(2)
        # Save the response as an HTML file
        tree = html.fromstring(response.content)
        for i in range (0,int(tree.xpath("count(//div[@class='f']//a)"))):
            dictionary[tree.xpath("//div[@class='f']//a/@title")[i]]=tree.xpath("//div[@class='f']//a/@href")[i]
        return dictionary
    else:
        return []
    
def movie_selection(dictionary): #movie/quality selector #2
    if dictionary:
        options = list(dictionary.keys())
        selection = st.pills("Select Preffered", options, selection_mode="single")
        selected_movie_link= dictionary.get(selection)
        st.markdown(f"Your selected options: {selection}.")
        return selected_movie_link

#def recommendation_engine(): #3.1
#    recommendations={}
#    for i in range (0,int(tree.xpath("count(//div[@class='f']//a)"))):
#        recommendations[tree.xpath("//div[@class='f']//a/@title")[i]]=tree.xpath("//div[@class='f']//a/@href")[i]
#    return recommendations

def movie_quality(selected_movie_link): #3
    if selected_movie_link.strip():
        url=selected_movie_link
        response = requests.get(url)
        if response.status_code==200:
            dictionary={}
            # Save the response as an HTML file
            tree = html.fromstring(response.content)
            for i in range (0,int(tree.xpath("count(//ul[@class='sitelinks'])"))):
                dictionary[tree.xpath("//ul[@class='sitelinks']//a//b/text()")[i]]=tree.xpath("//ul[@class='sitelinks']//a/@href")[i]
            selected_quality=movie_selection(dictionary)
            #recommendations=recommendation_engine
            #print(recommendations)
            return selected_quality

def stream_link_fetcher(selected_quality): #4
    url=selected_quality
    response = requests.get(url)
    if response.status_code==200:
        # Save the response as an HTML file
        tree = html.fromstring(response.content)
        if tree.xpath("//div[@class='f']//a[@class='dwnLink']/@href"):
            return stream_link_fetcher(tree.xpath("//div[@class='f']//a[@class='dwnLink']/@href")[0])
        elif tree.xpath("//div[@class='downLink']//a[@class='dwnLink']/@href"):
            return url

######################################## End of Initial Links Extraction ##########################################################

######################################### Stream Link Extraction #######################################################

def process_browser_logs_for_network_events(logs): #process and fetch only relevant log file
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if log.get('method') == 'Network.responseReceived' and log.get('params', {}).get('response', {}).get('mimeType') == 'text/html':
            return log


def get_website_content(url): #uses selenium to mimic a click
    driver = None
    try:
        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode (optional)
        chrome_options.add_argument('--disable-gpu')  # Disable GPU for headless mode
        chrome_options.add_argument('--window-size=1920,1200') # Set Chrome window Size
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        # For local Development                          
        #service = Service('C:\\ChromeDriver_Path')  # Replace with your ChromeDriver path
        #driver = webdriver.Chrome(service=service, options=chrome_options)
        st.write(f"DEBUG:DRIVER:{driver}")
        driver.get(url)
        time.sleep(5)
        html_doc = driver.page_source
        download_button = driver.find_element(By.XPATH, "//a[@class='dwnLink']")  # Adjust XPath to match your case
        download_button.click()
        logs = driver.get_log("performance")
        driver.quit()
        return logs
    except Exception as e:
        print(f"DEBUG:INIT_DRIVER:ERROR:{e}")
    finally:
            if driver is not None: driver.quit()
    return None


def process_browser_logs_for_network_events(logs): #process and fetch only relevant log file
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if log.get('method') == 'Network.responseReceived' and log.get('params', {}).get('response', {}).get('mimeType') == 'video/mp4':
            #st.write(type(log)) for debugging
            return log
        
#extract the streamlink from logs
def extract_url(log):
    # Safely navigate the nested dictionary to get the 'url' value
    return log.get('params', {}).get('response', {}).get('url', None)


# -------------------------------------- Page & UI/UX Components -------------------------------------

# Streamlit app
st.title("Streaks Movies - Stream or Download Movies")

# Text input for user
keyword = st.text_input("Search for your fav movie below:", placeholder="Type here and press Enter...")

clicked = st.button("Load Page Content",type="secondary")

if clicked:
    dictionary = movie_search(keyword)

    selected_movie_link = movie_selection(dictionary)

    selected_quality = movie_quality(selected_movie_link)

    final_link = stream_link_fetcher(selected_quality)

    logs = get_website_content(final_link)

    log = process_browser_logs_for_network_events(logs)

    streamlink = extract_url(log)

    st.video(streamlink)
    time.sleep(5)
    st.link_button("Save to Device",streamlink,type="primary")
