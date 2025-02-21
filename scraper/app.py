from flask import Flask, request, jsonify
from linkedin_scraper import (scrape_linkedin_feed, scroll_linkedin_feed, 
                              scrape_linkedin_company_posts, is_job_post, 
                              get_text, get_author_name, get_post_date)
from bs4 import BeautifulSoup as bs
import os
import random
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Variable globale pour stocker l'instance du navigateur
browser = None

# Fonction pour nettoyer la date
def clean_date(date_str):
    if not date_str:
        return "Unknown"
    months = {
        "janv": "January", "févr": "February", "mars": "March", "avr": "April", 
        "mai": "May", "juin": "June", "juil": "July", "août": "August", 
        "sept": "September", "oct": "October", "nov": "November", "déc": "December"
    }
    for fr, en in months.items():
        if fr in date_str:
            date_str = date_str.replace(fr, en)
    return date_str.strip().replace("il y a", "").strip()

# Fonction pour convertir une date relative ou absolue
def get_actual_date(date_str):
    now = datetime.now()
    try:
        if "minute" in date_str:
            return now - relativedelta(minutes=int(date_str.split()[0]))
        if "heure" in date_str:
            return now - relativedelta(hours=int(date_str.split()[0]))
        if "jour" in date_str:
            return now - relativedelta(days=int(date_str.split()[0]))
        if "mois" in date_str:
            return now - relativedelta(months=int(date_str.split()[0]))
        if "année" in date_str:
            return now - relativedelta(years=int(date_str.split()[0]))
        return datetime.strptime(date_str, "%d %B %Y")
    except (ValueError, AttributeError):
        return None

# Route pour se connecter à LinkedIn
@app.route('/login', methods=['POST'])
def login():
    global browser
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    browser = scrape_linkedin_feed(username, password)
    return jsonify({"message": "Logged in successfully"}), 200

# Route pour extraire les posts d'une entreprise
@app.route('/scrape_company_posts', methods=['POST'])
def scrape_company_posts():
    global browser
    if browser is None:
        return jsonify({"error": "Please log in first"}), 400
    data = request.json
    company_name = data.get('company_name')
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    scroll_linkedin_feed(browser, max_scrolls=5)
    num_posts = scrape_linkedin_company_posts(browser, company_name)
    return jsonify({"message": f"Found {num_posts} posts", "company_name": company_name}), 200

# Route pour extraire les posts de la page d'accueil
@app.route('/html_scrape_home_posts', methods=['POST'])
def html_scrape_home_posts():
    global browser
    if browser is None:
        return jsonify({"error": "Please log in first"}), 400

    if "linkedin.com" not in browser.current_url:
        return jsonify({"error": "Not logged into LinkedIn"}), 400

    print("[INFO] Début du scrolling...")

    last_height = browser.execute_script("return document.body.scrollHeight")

    for i in range(15):  # Augmenter le nombre de scrolls
        print(f"[INFO] Scrolling {i+1}/15...")

        # Scroll vers le bas
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(4, 8))  # Pause plus longue

        new_height = browser.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            print("[INFO] Aucun nouveau post détecté, attente avant nouvel essai...")
            time.sleep(5)  # Pause plus longue avant d'arrêter définitivement
            new_height = browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Si toujours aucun changement, arrêt du scrolling

        last_height = new_height

    print("[INFO] Scrolling terminé.")

    try:
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "feed-shared-update-v2"))
        )
    except:
        return jsonify({"error": "No posts found after scrolling"}), 404

    linkedin_soup = bs(browser.page_source, "html.parser")
    posts = linkedin_soup.find_all("div", class_="feed-shared-update-v2")

    if not posts:
        return jsonify({"error": "No posts found"}), 404

    print(f"[INFO] Nombre de posts trouvés : {len(posts)}")

    post_data = []
    for i, post in enumerate(posts):
        post_text = get_text(post, [
            ("div", {"class": "feed-shared-update-v2__description"}),
            ("div", {"class": "update-components-text"}),
            ("span", {"class": "break-words"})
        ])
        author_name = get_author_name(post)
        post_date = get_post_date(post)

        cleaned_date = clean_date(post_date)
        actual_date = get_actual_date(cleaned_date)
        formatted_date = actual_date.strftime('%Y-%m-%d %H:%M:%S') if actual_date else "Unknown"

        print(f"[INFO] Post {i+1} - Auteur: {author_name}, Date: {formatted_date}")

        post_data.append({
            "Auteur": author_name,
            "Date": formatted_date,
            "Texte": post_text,
            "HTML": post.encode_contents().decode("utf-8")
        })

    return jsonify({"posts": post_data}), 200



if __name__ == "__main__":
    app.run(debug=True)
