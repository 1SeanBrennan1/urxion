import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import os
from groq import Groq
from openai import OpenAI
from urllib.parse import quote, urlparse, urljoin
import time
import json
import re
import shutil
import argparse
import logging
from collections import deque
from threading import Lock
import textwrap
from datetime import datetime

# Constants
GROQ_TIMEOUT = 30
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MAX_TOKENS = 6000
MAX_PAGES = 10
ARTICLES_FOLDER = "/home/seani/mysite/articles"
COMPLETED_FOLDER = "/home/seani/mysite/articles/completed"
OUTPUT_FOLDER = "/home/seani/mysite/templates/blog"
FLASK_APP_PATH = "/home/seani/mysite/flask_app.py"
SITEMAP_PATH = "/home/seani/mysite/templates/sitemap.xml"
MAX_TOKENS_PER_REQUEST = 3000  # Adjust this based on your needs
TOKENS_PER_MINUTE_70B = 5500
REQUESTS_PER_MINUTE_70B = 25
MODEL_70B = "llama3-70b-8192"
ERROR_WAIT_TIME = 60  # Wait time for rate limit errors
MAX_CHUNK_SIZE = 4000  # Adjust this value based on the model's token limit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def split_prompt(prompt):
    words = prompt.split()
    mid = len(words) // 2
    return " ".join(words[:mid]), " ".join(words[mid:])

def estimate_tokens(text):
    # This is a rough estimate. Adjust the factor as needed.
    # Average token length is assumed to be 4 characters per token.
    return len(text) // 4

def ai_request_70b(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting AI request with model: {MODEL_70B}")
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_70B,
                max_tokens=MAX_TOKENS_PER_REQUEST
            )
            output = response.choices[0].message.content.strip()
            input_tokens = estimate_tokens(prompt)
            output_tokens = estimate_tokens(output)
            print(f"Input Tokens: {input_tokens}")
            print(f"Output Tokens: {output_tokens}")
            print(f"Input: {prompt}")
            print(f"Output: {output}")
            return output
        except Exception as e:
            logging.error(f"Error with AI request (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                wait_time = ERROR_WAIT_TIME
                logging.info(f"Rate limit error. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                wait_time = min(2 ** attempt, 32)  # Exponential backoff
                logging.error(f"API request failed. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    logging.error("Failed to get a successful AI response after multiple attempts.")
    return ""

def ai_request_70b_with_split(prompt, max_retries=3):
    estimated_tokens = estimate_tokens(prompt)
    if estimated_tokens > MAX_TOKENS_PER_REQUEST:
        logging.info(f"Estimated tokens ({estimated_tokens}) exceed limit. Splitting prompt.")
        prompt1, prompt2 = split_prompt(prompt)
        response1 = ai_request_70b_with_split(prompt1, max_retries)
        time.sleep(ERROR_WAIT_TIME)  # Wait between split requests
        response2 = ai_request_70b_with_split(prompt2, max_retries)
        return response1 + " " + response2
    else:
        return ai_request_70b(prompt, max_retries)

def read_article(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            total_chars = len(content)
            tokens_per_chunk = MAX_TOKENS_PER_REQUEST // 2 * 5  # Assuming 5 characters per token
            num_chunks = max(1, total_chars // tokens_per_chunk)
            chunk_size = total_chars // num_chunks
            for i in range(0, total_chars, chunk_size):
                yield content[i:i + chunk_size]
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        yield None

def extract_structure(content_generator):
    extracted_structure = ""
    for i, chunk in enumerate(content_generator):
        if chunk is None:
            logging.warning("Encountered None chunk, skipping...")
            continue
        prompt = f"""
        Analyze the following part {i+1} of a book and extract:
        1. All chapter titles and numbers
        2. Any key terms and their definitions
        3. The overall summary of the book (if present)

        Only extract information that is explicitly stated in the text. Do not infer or generate any content.
        Format the output as a JSON object with "chapters", "definitions", and "summary" keys.

        Text to analyze:
        {chunk}
        """
        extracted_structure += ai_request_70b_with_split(prompt) + "\n\n"
        time.sleep(2)  # Add a small delay between requests

    with open('debug_extracted_structure.json', 'w') as f:
        json.dump(extracted_structure, f, indent=2)
    return extracted_structure

def extract_json_objects(text):
    """Extract JSON objects from a string."""
    json_objects = []
    brace_level = 0
    current_json = ""
    for char in text:
        if char == '{':
            if brace_level == 0:
                current_json = char
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            current_json += char
            if brace_level == 0:
                json_objects.append(json.loads(current_json))
                current_json = ""
        elif brace_level > 0:
            current_json += char
    return json_objects

def organize_content(extracted_structure):
    json_objects = extract_json_objects(extracted_structure)
    organized_structure = {
        "title": "Book Title",
        "summary": "",
        "chapters": []
    }

    for obj in json_objects:
        if "summary" in obj:
            organized_structure["summary"] = obj["summary"]
        if "chapters" in obj:
            organized_structure["chapters"].extend(obj["chapters"])

    logging.info(f"Organized structure: {json.dumps(organized_structure, indent=2)}")
    return organized_structure

def generate_html_content(chapter_title, chapter_content, organized_structure):
    # Extract the book summary and table of contents
    book_summary = organized_structure.get('summary', 'No summary available.')
    chapters = organized_structure.get('chapters', [])

    # Generate the table of contents
    toc = '<ul>'
    for chapter in chapters:
        toc += f'<li><a href="#{chapter["title"].replace(" ", "_")}">{chapter["title"]}</a>: {chapter.get("summary", "No summary available.")}</li>'
    toc += '</ul>'

    # Generate the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8"/>
        <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
        <meta content="ie=edge" http-equiv="X-UA-Compatible"/>
        <title>{chapter_title}</title>
        <link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,600" rel="stylesheet"/>
        <link href="{{{{ url_for('static', filename='css/bootstrap.min.css') }}}}" rel="stylesheet"/>
        <link href="{{{{ url_for('static', filename='fontawesome/css/all.min.css') }}}}" rel="stylesheet"/>
        <link href="{{{{ url_for('static', filename='css/templatemo-business-oriented.css') }}}}" rel="stylesheet"/>
    </head>
    <body>
        <div class="parallax-window" data-image-src="{{{{ url_for('static', filename='img/biz-oriented-header.jpg') }}}}" data-parallax="scroll" id="parallax-1">
            <div class="tm-logo" style="background-color: transparent;">
                <img alt="Your Logo" class="tm-logo-img" src="{{{{ url_for('static', filename='img/Meeting-Gen.png') }}}}"/>
            </div>
        </div>
        <div class="tm-nav-container-outer">
            <div class="container-fluid">
                <div class="row">
                    <div class="col-12">
                        <nav class="navbar navbar-expand-lg" id="tm-main-nav">
                            <button aria-controls="navbar-nav" aria-expanded="false" aria-label="Toggle navigation" class="navbar-toggler toggler-example" data-target="#navbar-nav" data-toggle="collapse" type="button">
                                <span class="dark-blue-text"><i class="fas fa-bars"></i></span>
                            </button>
                            <div class="collapse navbar-collapse tm-nav" id="navbar-nav">
                                <ul class="navbar-nav ml-auto">
                                    <li class="nav-item">
                                        <a class="nav-link tm-nav-link" href="{{{{ url_for('index') }}}}">Home</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link tm-nav-link" href="{{{{ url_for('services') }}}}">Services</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link tm-nav-link" href="{{{{ url_for('cold_calling') }}}}">Cold Calling That Converts</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link tm-nav-link" href="{{{{ url_for('business_assessment') }}}}">Business Assessment</a>
                                    </li>
                                </ul>
                            </div>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
        <div class="container">
            <h1>{chapter_title}</h1>
            <h2>Book Summary</h2>
            <p>{book_summary}</p>
            <h2>Table of Contents</h2>
            {toc}
            <h2 id="{chapter_title.replace(" ", "_")}">{chapter_title}</h2>
            <p>{chapter_content}</p>
        </div>
        <footer class="container-fluid">
            <div class="row">
                <p class="col-lg-9 col-md-8 mb-5 mb-md-0">
                    Copyright © 2024 <span class="tm-text-primary">URXION</span>
                    - Contact Us At <a class="tm-link-primary" href="mailto:Sean.Brennan@urxion.com">Sean.Brennan@urxion.com</a>
                </p>
                <div class="col-lg-3 col-md-4 text-right">
                    <a class="tm-social-link" href="https://linkedin.com">
                        <i class="fab fa-linkedin fa-2x tm-social-icon"></i>
                    </a>
                </div>
            </div>
        </footer>
        <script src="{{{{ url_for('static', filename='js/jquery-3.4.1.min.js') }}}}"></script>
        <script src="{{{{ url_for('static', filename='js/bootstrap.min.js') }}}}"></script>
        <script src="{{{{ url_for('static', filename='js/parallax.min.js') }}}}"></script>
        <script src="{{{{ url_for('static', filename='js/tooplate-script.js') }}}}"></script>
        <script>
            $(document).ready(function () {{
                $('#parallax-1').parallax({{ imageSrc: "{{{{ url_for('static', filename='img/biz-oriented-header.jpg') }}}}" }});
            }});
        </script>
    </body>
    </html>
    """
    return html_content

def main(reprocess=False):
    logging.info(f"Articles folder: {ARTICLES_FOLDER}")
    os.makedirs(COMPLETED_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    if reprocess:
        files = os.listdir(COMPLETED_FOLDER)
        source_folder = COMPLETED_FOLDER
    else:
        files = os.listdir(ARTICLES_FOLDER)
        source_folder = ARTICLES_FOLDER

    logging.info(f"Files found: {files}")

    for filename in files:
        if filename.endswith('.txt'):
            file_path = os.path.join(source_folder, filename)
            logging.info(f"Starting to process file: {file_path}")

            try:
                content_generator = read_article(file_path)

                logging.info("Extracting structure")
                extracted_structure = extract_structure(content_generator)
                logging.info("Organizing content")
                organized_structure = organize_content(extracted_structure)

                processed_chapters = process_file(file_path, organized_structure)

                for index, chapter in enumerate(processed_chapters, start=1):
                    chapter_title = chapter['title']
                    chapter_content = chapter['content']

                    logging.info(f"Generating HTML for chapter {index}: {chapter_title}")
                    formatted_html = generate_html_content(chapter_title, chapter_content, organized_structure)

                    output_file = os.path.join(OUTPUT_FOLDER, f"{organized_structure['title'].lower().replace(' ', '_')}_{index}.html")

                    logging.info(f"Writing content to {output_file}")
                    with open(output_file, 'w') as file:
                        file.write(formatted_html)
                    logging.info(f"Wrote {len(formatted_html)} characters to {output_file}")

                if not reprocess:
                    os.rename(file_path, os.path.join(COMPLETED_FOLDER, filename))
                    logging.info(f"Moved {filename} to completed folder")
                    if os.path.exists(os.path.join(COMPLETED_FOLDER, filename)):
                        logging.info(f"Confirmed {filename} exists in completed folder")
                    else:
                        logging.error(f"Failed to move {filename} to completed folder")

                # Add the new route to the Flask app and update the sitemap
                add_route_and_update_sitemap(filename)

                # Update the Cold Calling That Converts.html
                update_cold_calling_html(filename)

            except Exception as e:
                logging.error(f"Error processing file {filename}: {str(e)}")
                continue

    logging.info("Processing complete")

def add_route_and_update_sitemap(filename):
    try:
        title = os.path.splitext(filename)[0].replace('_', ' ').title()  # Generate title from filename
        url_friendly_title = title.lower().replace(' ', '_')  # Generate URL-friendly title
        new_route = f"""
@app.route('/blog/{url_friendly_title}')
def blog_{url_friendly_title}():
    return render_template('blog/{url_friendly_title}.html')
"""

        with open(FLASK_APP_PATH, 'r') as file:
            app_content = file.read()

        if f"def blog_{url_friendly_title}():" not in app_content:
            # Find the /robots.txt route definition
            robots_txt_index = app_content.find("@app.route('/robots.txt')")
            if robots_txt_index != -1:
                # Insert the new route above the /robots.txt route
                insert_index = app_content.rfind('\n', 0, robots_txt_index) + 1
                updated_content = app_content[:insert_index] + new_route + app_content[insert_index:]

                with open(FLASK_APP_PATH, 'w') as file:
                    file.write(updated_content)
                logging.info(f"Added new route for {title}")
            else:
                logging.error("Could not find a suitable location to add the new route")
        else:
            logging.info(f"Route for {title} already exists")

        # Update sitemap
        sitemap_path = "/home/seani/mysite/templates/sitemap.xml"
        with open(sitemap_path, 'r') as file:
            sitemap_content = file.read()

        new_url = f"""
    <url>
        <loc>https://www.urxion.com/blog/{url_friendly_title}</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>"""

        if f"/blog/{url_friendly_title}" not in sitemap_content:
            insert_index = sitemap_content.rfind('</urlset>')
            updated_sitemap = sitemap_content[:insert_index] + new_url + sitemap_content[insert_index:]

            with open(sitemap_path, 'w') as file:
                file.write(updated_sitemap)
            logging.info(f"Added new URL to sitemap for {title}")
        else:
            logging.info(f"URL for {title} already exists in sitemap")

    except Exception as e:
        logging.error(f"Error updating Flask app or sitemap: {str(e)}")

def update_cold_calling_html(filename):
    try:
        title = os.path.splitext(filename)[0].replace('_', ' ').title()  # Generate title from filename
        url_friendly_title = title.lower().replace(' ', '_')  # Generate URL-friendly title

        # Update Cold Calling That Converts.html
        cold_calling_path = "/home/seani/mysite/templates/Cold Calling That Converts.html"
        with open(cold_calling_path, 'r') as file:
            soup = BeautifulSoup(file, 'html.parser')

        # Find the container for blog items
        container = soup.find('div', class_='container-fluid')
        if container:
            # Create a new blog item
            new_blog_item = soup.new_tag('div', attrs={'class': 'tm-blog-item'})
            new_blog_link = soup.new_tag('a', href=f'/blog/{url_friendly_title}', attrs={'class': 'tm-blog-link'})
            new_blog_img = soup.new_tag('img', src="{{ url_for('static', filename='img/[Image related to new article]') }}", attrs={'alt': 'Image', 'class': 'img-fluid tm-blog-img'})
            new_blog_content = soup.new_tag('div')
            new_blog_title = soup.new_tag('h4', attrs={'class': 'mb-3'})
            new_blog_title.string = title
            new_blog_text = soup.new_tag('p', attrs={'class': 'tm-strategy-text'})
            new_blog_text.string = "Brief description of the new blog post."

            new_blog_content.append(new_blog_title)
            new_blog_content.append(new_blog_text)
            new_blog_link.append(new_blog_img)
            new_blog_link.append(new_blog_content)
            new_blog_item.append(new_blog_link)

            # Add the new blog item to the container
            container.append(new_blog_item)

            # Write the updated HTML back to the file
            with open(cold_calling_path, 'w') as file:
                file.write(str(soup))
            logging.info(f"Added new blog item for {title} to Cold Calling That Converts.html")
        else:
            logging.error("Could not find container for blog items in Cold Calling That Converts.html")

    except Exception as e:
        logging.error(f"Error updating Cold Calling That Converts.html: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process blog posts")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess files in the completed folder")
    args = parser.parse_args()

    logging.info("Script started")
    main(reprocess=args.reprocess)
    logging.info("Script finished")

def chunk_text(text, max_chunk_size=MAX_CHUNK_SIZE):
    return textwrap.wrap(text, max_chunk_size, break_long_words=False, replace_whitespace=False)

def extract_chapter_content(chapter_title, full_content):
    logging.info(f"Extracting content for chapter: {chapter_title}")

    if not chapter_title:
        logging.info("No chapter title provided, generating one")
        prompt = f"""
        Analyze the following text and identify the chapter title. If no clear title is present, generate an appropriate title based on the content. Return only the title, nothing else.

        Text to analyze:
        {full_content[:2000]}  # Limit to first 2000 characters to avoid token limits
        """
        chapter_title = safe_ai_request(prompt)
        if not chapter_title:
            logging.error("Failed to generate chapter title")
            return None, None
        logging.info(f"Generated chapter title: {chapter_title}")

    prompt = f"""
    Extract the content for the chapter titled "{chapter_title}" from the following text:

    {full_content}

    Only include the content that is explicitly part of this chapter. Do not add any additional commentary or explanations.
    """
    chapter_content = safe_ai_request(prompt)

    if not chapter_content or not chapter_content.strip():
        logging.error(f"No content extracted for chapter '{chapter_title}'")
        return chapter_title, None

    logging.info(f"Successfully extracted content for chapter '{chapter_title}'")
    return chapter_title, chapter_content.strip()

def process_file(file_path, organized_structure):
    logging.info(f"Processing file: {file_path}")
    with open(file_path, 'r') as file:
        full_content = file.read()

    processed_chapters = []
    for index, chapter in enumerate(organized_structure['chapters'], start=1):
        chapter_title = chapter.get('title')
        logging.info(f"Processing chapter {index}: {chapter_title}")
        chapter_title, chapter_content = extract_chapter_content(chapter_title, full_content)

        if not chapter_title or not chapter_content:
            logging.warning(f"Unable to process chapter {index}. Skipping this chapter.")
            continue

        processed_chapters.append({
            'title': chapter_title,
            'content': chapter_content
        })
        logging.info(f"Completed processing chapter {index}: {chapter_title}")

    logging.info(f"Completed processing file: {file_path}")
    return processed_chapters
