import requests
import time
import openai
from bs4 import BeautifulSoup
import datetime

# Define your API keys and D7SMS API endpoint
SMSAPI_KEY = 'your_d7sms_api_key'
SMS_URL = 'https://api.d7networks.com/secure/send'
OPENAI_API_KEY = 'your_openai_api_key'
PHONE_NUMBER = 'your_phone_number'  # Your phone number to receive and send messages
current_year = datetime.datetime.now().year

# Define the websites and their corresponding identifiers
WEBSITES = {
    'TechCrunch': {
        'url': 'https://techcrunch.com/',
        'title_selector': 'a.post-block__title__link',
    },
    'TheVerge': {
        'url': 'https://www.theverge.com/tech',
        'title_selector': f'a[href*="/{current_year}/"]',
    },
    'Wired': {
        'url': 'https://www.wired.com/',
        'title_selector': 'a[href="/story]',
    },
}

# Function to send an SMS using D7SMS
def send_sms(recipient, message):
    headers = {
        'Authorization': f'Bearer {SMSAPI_KEY}',
        'Content-Type': 'application/json',
    }

    data = {
        'to': recipient,
        'content': message,
    }

    response = requests.post(SMS_URL, headers=headers, json=data)

    if response.status_code == 200:
        print('SMS sent successfully')
    else:
        print('SMS sending failed')

# Function to scrape tech news from a given URL
def scrape_tech_news(website_name, website_data, count=2):
    url = website_data['url']
    title_selector = website_data['title_selector']

    try:
        # Send an HTTP GET request to the website
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the elements that contain the article titles and links
            article_elements = soup.select(title_selector)

            # Create a list to store the articles
            articles = []

            # Loop through the elements and extract the titles and links for the specified count
            for idx, article in enumerate(article_elements):
                if idx >= count:
                    break
                title = article.text
                link = article['href'] if 'href' in article.attrs else ''  # Extract link if available
                articles.append({'title': title, 'link': link})

            return articles
        else:
            print(f"Failed to retrieve the web page for {website_name}.")
            return None

    except Exception as e:
        print(f"An error occurred while scraping {website_name}: {str(e)}")
        return None

# Function to generate a LinkedIn post based on an article
def generate_linkedin_post(article):
    openai.api_key = OPENAI_API_KEY
    prompt = f"Generate a LinkedIn post based on the following article: {article['title']} - {article['link']}"
    response = openai.Completion.create(
        engine="davinci",  # Choose the GPT model
        prompt=prompt,
        max_tokens=150  # Adjust the length of the generated post
    )
    return response.choices[0].text

# Main loop
while True:
    article_selections = {}  # Store selected articles
    for website_name, website_data in WEBSITES.items():
        articles = scrape_tech_news(website_name, website_data, count=2)
        if articles:
            article_selections[website_name] = articles  # Store the articles

    # Send a text message with the list of articles for selection
    message = "Here are some recent articles to write about:\n"
    for idx, (source, articles) in enumerate(article_selections.items(), start=1):
        message += f"{chr(65 + idx)}. {source}:\n"
        for a_idx, article in enumerate(articles, start=1):
            message += f"{a_idx}. {article['title']}\n"

    send_sms(PHONE_NUMBER, message)

    # Wait for your response and process it
    response_text = input("Please select an article (e.g., A1, B2, or EXIT to stop): ")
    response_text = response_text.upper()

    if response_text == "EXIT":
        break

    if len(response_text) == 2 and response_text[0] in article_selections:
        source_index = ord(response_text[0]) - 65
        article_index = int(response_text[1]) - 1
        selected_article = article_selections[list(WEBSITES.keys())[source_index]][article_index]

        generated_post = generate_linkedin_post(selected_article)
        send_sms(PHONE_NUMBER, "Generated LinkedIn Post:\n" + generated_post)
        send_sms(PHONE_NUMBER, "Please review and make any necessary edits before posting.")
        time.sleep(86400 * 7)  # Wait for 1 week before the next batch of articles
