import requests

BASE_URL = "http://127.0.0.1:5000"  # L'URL de votre API Flask locale

# Fonction pour se connecter à LinkedIn
def login(username, password):
    url = f"{BASE_URL}/login"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Logged in successfully.")
    else:
        print(f"Error: {response.json().get('error', 'Unknown error')}")

# Fonction pour extraire les publications d'une entreprise
def scrape_company_posts(company_name):
    url = f"{BASE_URL}/scrape_company_posts"
    data = {"company_name": company_name}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"Found {response.json()['message']} for company {company_name}")
    else:
        print(f"Error: {response.json().get('error', 'Unknown error')}")

# Fonction pour filtrer les offres d'emploi d'une entreprise
def filter_job_posts(company_name):
    url = f"{BASE_URL}/filter_job_posts"
    data = {"company_name": company_name}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        job_posts = response.json().get("job_posts", [])
        print(f"Found {len(job_posts)} job posts for company {company_name}")
        for job in job_posts:
            print(f"Author: {job['Auteur']}, Date: {job['Date']}, Post: {job['Post Text']}")
    else:
        print(f"Error: {response.json().get('error', 'Unknown error')}")

# Fonction pour scraper les publications sur la page d'accueil
def html_scrape_home_posts():
    url = f"{BASE_URL}/html_scrape_home_posts"
    response = requests.post(url)
    if response.status_code == 200:
        posts = response.json().get("posts", [])
        print(f"Found {len(posts)} posts.")
        for post in posts:
            print(f"Author: {post['Auteur']}, Date: {post['Date']}, Post: {post['Texte']}")
    else:
        print(f"Error: {response.json().get('error', 'Unknown error')}")

# Exemple d'utilisation
if __name__ == "__main__":
    username = input("Enter LinkedIn username: ")
    password = input("Enter LinkedIn password: ")

    # Se connecter à LinkedIn
    login(username, password)

    # Scraper des posts d'entreprise
    company_name = input("Enter company name to scrape posts: ")
    scrape_company_posts(company_name)

    # Filtrer les offres d'emploi
    filter_job_posts(company_name)

    # Scraper des posts de la page d'accueil LinkedIn
    html_scrape_home_posts()
