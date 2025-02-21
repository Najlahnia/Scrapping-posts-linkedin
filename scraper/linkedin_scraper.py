from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import time
import random

# Fonction pour initialiser le navigateur et se connecter à LinkedIn
def scrape_linkedin_feed(username, password, page_url='https://www.linkedin.com/feed/'):
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    browser = webdriver.Chrome(options=chrome_options)
    time.sleep(random.uniform(6, 11))
    browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')
    time.sleep(random.uniform(4, 10))
    email_field = browser.find_element(By.ID, 'username')
    email_field.send_keys(username)
    password_field = browser.find_element(By.ID, 'password')
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    time.sleep(random.uniform(8, 12))
    browser.get(page_url)
    print("Le navigateur est ouvert. Vous pouvez interagir avec lui.")
    return browser

# Fonction pour faire défiler le fil d'actualités
def scroll_linkedin_feed(browser, max_scrolls=None):
    SCROLL_PAUSE_TIME = random.uniform(1, 8)
    SCROLL_COMMAND = "window.scrollTo(0, document.body.scrollHeight);"
    GET_SCROLL_HEIGHT_COMMAND = "return document.body.scrollHeight"
    time.sleep(random.uniform(8, 12))
    last_height = browser.execute_script(GET_SCROLL_HEIGHT_COMMAND)
    scrolls = 0
    no_change_count = 0
    while True:
        browser.execute_script(SCROLL_COMMAND)
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = browser.execute_script(GET_SCROLL_HEIGHT_COMMAND)
        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0
        if no_change_count >= 3 or (max_scrolls is not None and scrolls >= max_scrolls):
            break
        last_height = new_height
        scrolls += 1

# Fonction pour extraire les publications d'une page LinkedIn entreprise
def scrape_linkedin_company_posts(browser, company_name):
    company_page = browser.page_source
    linkedin_soup = bs(company_page, "html.parser")
    with open(f"{company_name}_soup.txt", "w+", encoding="utf-8") as t:
        t.write(linkedin_soup.prettify())
    containers = linkedin_soup.find_all("div", {"class": "feed-shared-update-v2"})
    containers = [container for container in containers if 'activity' in container.get('data-urn', '')]
    print(f"Nombre de publications trouvées : {len(containers)}")
    containers_text = "\n\n".join([c.prettify() for c in containers])
    with open(f"{company_name}_soup_containers.txt", "w+", encoding="utf-8") as t:
        t.write(containers_text)
    return len(containers)

# Fonction pour vérifier si un post est une offre d'emploi
def is_job_post(post_text):
    job_keywords = [
        "recrutement", "offre d'emploi", "hiring", "job", "emploi", "poste", "recherche", "candidature",
        "recrute", "opportunité", "carrière", "join us", "we are hiring", "apply now"
    ]
    post_text_lower = post_text.lower()
    return any(keyword in post_text_lower for keyword in job_keywords)

# Fonction pour extraire le texte d'un élément HTML
def get_text(container, selectors):
    for selector, attributes in selectors:
        element = container.find(selector, attributes)
        if element:
            text = element.get_text(strip=True)
            if text:
                return text
    return "No Content"

# Fonction pour extraire le nom de l'auteur
def get_author_name(container):
    author_selectors = [
        ("span", {"class": "update-components-actor__title"}),
        ("span", {"class": "update-components-actor__name"}),
        ("a", {"class": "update-components-actor__name-link"})
    ]
    return get_text(container, author_selectors)

# Fonction pour extraire la date du post
def get_post_date(container):
    date_selectors = [
        ("time", {}),
        ("span", {"class": "update-components-actor__sub-description"})
    ]
    return get_text(container, date_selectors)

