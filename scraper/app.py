from flask import Flask, request, jsonify
from linkedin_scraper import scrape_linkedin_feed, scroll_linkedin_feed, scrape_linkedin_company_posts, is_job_post, get_text, get_author_name, get_post_date
from bs4 import BeautifulSoup as bs
import os
import random
import time
app = Flask(__name__)

# Variable globale pour stocker l'instance du navigateur
browser = None

# Route pour se connecter à LinkedIn



@app.route('/login', methods=['POST'])
def login():
    global browser  # Utiliser la variable globale
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Initialiser le navigateur
    browser = scrape_linkedin_feed(username, password)
    return jsonify({"message": "Logged in successfully"}), 200

# Route pour extraire les publications d'une entreprise
@app.route('/scrape_company_posts', methods=['POST'])
def scrape_company_posts():
    global browser  # Utiliser la variable globale
    if browser is None:
        return jsonify({"error": "Please log in first"}), 400
    
    data = request.json
    company_name = data.get('company_name')
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    # Faire défiler le fil d'actualités
    scroll_linkedin_feed(browser, max_scrolls=5)
    
    # Extraire les publications
    num_posts = scrape_linkedin_company_posts(browser, company_name)
    return jsonify({"message": f"Found {num_posts} posts", "company_name": company_name}), 200

# Route pour filtrer les offres d'emploi
@app.route('/filter_job_posts', methods=['POST'])
def filter_job_posts():
    global browser  # Utiliser la variable globale
    if browser is None:
        return jsonify({"error": "Please log in first"}), 400
    
    data = request.json
    company_name = data.get('company_name')
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    # Lire les publications sauvegardées
    try:
        with open(f"{company_name}_soup_containers.txt", "r", encoding="utf-8") as f:
            containers_html = f.read()
    except FileNotFoundError:
        return jsonify({"error": "No posts found for this company. Please scrape first."}), 404
    
    # Analyser les publications
    containers_soup = bs(containers_html, "html.parser")
    containers = containers_soup.find_all("div", {"class": "feed-shared-update-v2"})
    job_posts = []
    
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
        job_posts.append({
            "Auteur": author_name,
            "Date": post_date,
            "Post Text": post_text
        })
    
    return jsonify({"job_posts": job_posts}), 200





@app.route('/html_scrape_home_posts', methods=['POST'])
def html_scrape_home_posts():
    global browser
    if browser is None:
        return jsonify({"error": "Please log in first"}), 400
    
    # Vérifier si l'utilisateur est bien sur LinkedIn
    if "linkedin.com" not in browser.current_url:
        return jsonify({"error": "Not logged into LinkedIn"}), 400

    # Faire défiler la page pour charger plus de posts
    SCROLL_PAUSE_TIME = random.uniform(1.5, 4)  # Temps d'attente entre chaque scroll
    SCROLL_COMMAND = "window.scrollTo(0, document.body.scrollHeight);"
    GET_SCROLL_HEIGHT_COMMAND = "return document.body.scrollHeight"

    time.sleep(random.uniform(5, 8))  # Pause avant de commencer le scrolling
    last_height = browser.execute_script(GET_SCROLL_HEIGHT_COMMAND)
    no_change_count = 0
    
    while no_change_count < 3:  # Arrêter après 3 tentatives sans changement
        browser.execute_script(SCROLL_COMMAND)
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = browser.execute_script(GET_SCROLL_HEIGHT_COMMAND)
        
        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0  # Réinitialiser si la page continue à scroller
        
        last_height = new_height

    # Attendre un peu pour s'assurer que tout est bien chargé
    time.sleep(random.uniform(2, 4))

    # Extraire le HTML des publications après le scrolling
    page_source = browser.page_source
    linkedin_soup = bs(page_source, "html.parser")

    # Vérifier si des posts ont été trouvés
    posts = linkedin_soup.find_all("div", class_="feed-shared-update-v2")
    if not posts:
        return jsonify({"error": "No posts found"}), 404

    # Extraire les informations et le HTML de chaque post
    post_data = []
    for i, post in enumerate(posts):
        post_html = post.encode_contents().decode("utf-8")
        post_text = get_text(post, [
            ("div", {"class": "feed-shared-update-v2__description-wrapper"}),
            ("div", {"class": "update-components-text"}),
            ("span", {"class": "break-words"})
        ])
        author_name = get_author_name(post)
        post_date = get_post_date(post)

        post_data.append({
            "post_number": i + 1,
            "Auteur": author_name,
            "Date": post_date,
            "Texte": post_text,
            "HTML": post_html
        })

    return jsonify({"total_posts": len(post_data), "posts": post_data}), 200


if __name__ == "__main__":
    app.run(debug=True)