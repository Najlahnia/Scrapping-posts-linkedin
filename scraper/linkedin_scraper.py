from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
import time
import random
import re
from datetime import datetime
from selenium.webdriver.common.keys import Keys

# Fonction pour initialiser le navigateur et se connecter à LinkedIn
def scrape_linkedin_feed(username, password, page_url='https://www.linkedin.com/feed/'):
    """
    Initialise le navigateur Chrome, se connecte à LinkedIn et ouvre la page spécifiée.

    :param username: Email ou identifiant LinkedIn.
    :param password: Mot de passe LinkedIn.
    :param page_url: URL de la page LinkedIn à ouvrir (par défaut : le fil d'actualités).
    :return: Instance du navigateur Selenium.
    """
    # Configuration des options Chrome
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)  # Garde le navigateur ouvert après l'exécution

    # Initialisation du WebDriver
    browser = webdriver.Chrome(options=chrome_options)

    # Attendre un temps aléatoire pour éviter la détection
    time.sleep(random.uniform(6, 11))

    # Ouvrir la page de connexion LinkedIn
    browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')
    time.sleep(random.uniform(4, 10))

    # Remplir les champs de connexion
    email_field = browser.find_element(By.ID, 'username')
    email_field.send_keys(username)
    password_field = browser.find_element(By.ID, 'password')
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    # Attendre un temps aléatoire après la connexion
    time.sleep(random.uniform(8, 12))

    # Ouvrir la page spécifiée
    browser.get(page_url)
    print("Le navigateur est ouvert. Vous pouvez interagir avec lui.")

    return browser

# Fonction pour faire défiler le fil d'actualités
def scroll_linkedin_feed(browser, max_scrolls=None):
    """
    Fait défiler le fil d'actualités LinkedIn pour charger plus de publications.

    :param browser: Instance du navigateur Selenium.
    :param max_scrolls: Nombre maximum de défilements (par défaut : None pour un défilement illimité).
    """
    SCROLL_PAUSE_TIME = random.uniform(1, 8)
    SCROLL_COMMAND = "window.scrollTo(0, document.body.scrollHeight);"
    GET_SCROLL_HEIGHT_COMMAND = "return document.body.scrollHeight"

    # Attendre le chargement initial de la page
    time.sleep(random.uniform(8, 12))

    # Initialiser la hauteur de défilement
    last_height = browser.execute_script(GET_SCROLL_HEIGHT_COMMAND)
    scrolls = 0
    no_change_count = 0

    while True:
        # Faire défiler la page
        browser.execute_script(SCROLL_COMMAND)
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculer la nouvelle hauteur de défilement
        new_height = browser.execute_script(GET_SCROLL_HEIGHT_COMMAND)

        # Vérifier si la hauteur a changé
        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0

        # Arrêter si la hauteur ne change plus ou si le nombre maximum de défilements est atteint
        if no_change_count >= 3 or (max_scrolls is not None and scrolls >= max_scrolls):
            break

        last_height = new_height
        scrolls += 1

# Fonction pour extraire les publications d'une page LinkedIn entreprise
def scrape_linkedin_company_posts(browser, company_name):
    """
    Récupère et sauvegarde les publications d'une page LinkedIn entreprise.

    :param browser: Instance du navigateur Selenium.
    :param company_name: Nom de l'entreprise pour nommer les fichiers de sortie.
    :return: Nombre de publications trouvées.
    """
    # Récupérer le code source de la page
    company_page = browser.page_source

    # Parser le HTML avec BeautifulSoup
    linkedin_soup = bs(company_page, "html.parser")

    # Sauvegarder le contenu HTML dans un fichier
    with open(f"{company_name}_soup.txt", "w+", encoding="utf-8") as t:
        t.write(linkedin_soup.prettify())

    # Rechercher les publications
    containers = linkedin_soup.find_all("div", {"class": "feed-shared-update-v2"})

    # Filtrer les publications avec l'attribut "data-urn" contenant "activity"
    containers = [container for container in containers if 'activity' in container.get('data-urn', '')]

    # Afficher le nombre de publications trouvées
    print(f"Nombre de publications trouvées : {len(containers)}")

    # Sauvegarder les publications filtrées dans un fichier
    containers_text = "\n\n".join([c.prettify() for c in containers])
    with open(f"{company_name}_soup_containers.txt", "w+", encoding="utf-8") as t:
        t.write(containers_text)

    return len(containers)

# Fonction pour vérifier si un post est une offre d'emploi
def is_job_post(post_text):
    """
    Vérifie si le texte du post contient des mots-clés liés aux offres d'emploi.

    :param post_text: Texte du post.
    :return: True si c'est une offre d'emploi, False sinon.
    """
    job_keywords = [
        "recrutement", "offre d'emploi", "hiring", "job", "emploi", "poste", "recherche", "candidature",
        "recrute", "opportunité", "carrière", "join us", "we are hiring", "apply now"
    ]
    post_text_lower = post_text.lower()
    return any(keyword in post_text_lower for keyword in job_keywords)

# Fonction pour extraire le texte d'un élément HTML
def get_text(container, selectors):
    """
    Tente d'extraire du texte à partir d'une liste de sélecteurs.

    :param container: Élément HTML BeautifulSoup.
    :param selectors: Liste de tuples (balise, attributs) pour rechercher le texte.
    :return: Texte extrait ou "No Content" si rien n'est trouvé.
    """
    for selector, attributes in selectors:
        element = container.find(selector, attributes)
        if element:
            text = element.get_text(strip=True)
            if text:
                return text
    return "No Content"

# Fonction pour extraire le nom de l'auteur
def get_author_name(container):
    """
    Extrait le nom de la société ou de la personne qui a publié le post.

    :param container: Élément HTML BeautifulSoup.
    :return: Nom de l'auteur.
    """
    author_selectors = [
        ("span", {"class": "update-components-actor__title"}),
        ("span", {"class": "update-components-actor__name"}),
        ("a", {"class": "update-components-actor__name-link"})
    ]
    return get_text(container, author_selectors)

# Fonction pour extraire la date du post
def get_post_date(container):
    """
    Extrait la date de publication du post.

    :param container: Élément HTML BeautifulSoup.
    :return: Date du post.
    """
    date_selectors = [
        ("time", {}),
        ("span", {"class": "update-components-actor__sub-description"})
    ]
    return get_text(container, date_selectors)

# Point d'entrée du script
if __name__ == "__main__":
    # Informations de connexion LinkedIn
    USERNAME = ""
    PASSWORD = ""

    # Initialiser le navigateur et se connecter
    browser = scrape_linkedin_feed(USERNAME, PASSWORD)

    # Faire défiler le fil d'actualités
    scroll_linkedin_feed(browser, max_scrolls=5)

    # Extraire les publications de la page
    company_name = "nom_entreprise"
    num_posts = scrape_linkedin_company_posts(browser, company_name)

    # Traiter chaque publication
    with open(f"{company_name}_soup_containers.txt", "r", encoding="utf-8") as f:
        containers_html = f.read()
    containers_soup = bs(containers_html, "html.parser")
    containers = containers_soup.find_all("div", {"class": "feed-shared-update-v2"})

    for container in containers:
        post_text = get_text(container, [
            ("div", {"class": "feed-shared-update-v2__description-wrapper"}),
            ("div", {"class": "update-components-text"}),
            ("span", {"class": "break-words"})
        ])

        if not is_job_post(post_text):
            continue

        author_name = get_author_name(container)
        post_date = get_post_date(container)

        post_data = {
            "Auteur": author_name,
            "Date": post_date,
            "Post Text": post_text
        }

        print(f"\nOffre d'emploi trouvée : {post_data}")