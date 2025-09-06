from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time, re, pandas as pd

app = Flask(__name__)

# Fungua browser (headless mode kwa server)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

def login_instagram(username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password + Keys.RETURN)
    time.sleep(8)

def search_hashtag(tag):
    driver.get(f"https://www.instagram.com/explore/tags/{tag}/")
    time.sleep(5)

def get_post_links(limit=100):
    links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(links) < limit:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/p/" in href:
                links.add(href)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return list(links)[:limit]

def extract_info(post_url):
    driver.get(post_url)
    time.sleep(6)

    try:
        username = driver.find_element(By.XPATH, '//a[contains(@href, "/") and @role="link"]').text
    except:
        username = "Unknown"

    try:
        caption = driver.find_element(By.XPATH, '//div[@data-testid="post-comment-root"]').text
    except:
        caption = ""

    bio = ""
    if username != "Unknown":
        try:
            driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(6)
            try:
                bio_section = driver.find_element(By.CSS_SELECTOR, "div.-vDIg span")
                bio = bio_section.text
            except:
                try:
                    meta_desc = driver.find_element(By.XPATH, '//meta[@name="description"]').get_attribute('content')
                    bio = meta_desc
                except:
                    bio = ""
        except:
            bio = ""

    numbers = re.findall(r'\+?\d[\d\s\-]{7,}', bio + " " + caption)

    return {
        "Username": username,
        "Phone Numbers": ", ".join(numbers),
        "Bio": bio.strip()
    }

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    hashtag = data.get("hashtag", "")
    login_instagram("headquater_ai_", "Stevene2025@")

    search_hashtag(hashtag)
    links = get_post_links(50)  # limit kwa haraka
    results = []
    seen = set()

    for url in links:
        info = extract_info(url)
        if info["Username"] not in seen and info["Username"] != "Unknown":
            seen.add(info["Username"])
            results.append(info)

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
