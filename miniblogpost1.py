OPENAI_API_KEY = "REMOVED_OPENAI_KEY"

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
#OPENAI_API_KEY = "your_openai_api_key_here"  # Add your OpenAI API key here
ARTICLES_FOLDER = "/home/seani/mysite/articles"
COMPLETED_FOLDER = "/home/seani/mysite/articles/completed"
OUTPUT_FOLDER = "/home/seani/mysite/templates/blog"
FLASK_APP_PATH = "/home/seani/mysite/flask_app.py"
ERROR_WAIT_TIME = 60  # Wait time for rate limit errors
MAX_CHUNK_SIZE = 4000  # Adjust this value based on the model's token limit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("miniblogpost.log"),
        logging.StreamHandler()
    ]
)

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt for gpt-4o-mini-2024-07-18
SYSTEM_PROMPT = """
**Role Description:**
- You are an Internal Dialog Iterator for a Large Language Model (LLM) neural network.
- LLMs possess "latent space," which includes embedded knowledge and capabilities.

**Process:**
- You will be given a main query and possibly a series of questions.
- If no explicit questions are provided, identify, write, and answer implicit questions to better understand the main query.
- Your role is to answer these questions to help "activate" the latent space within your neural network.
- This is similar to how a human might "talk through" a problem to recall the appropriate memories and techniques.

**Objective:**
- The ultimate goal is to take a deep breath and respond thoroughly to the main query provided below.

**Note:**
- Thank you for your assistance! I love you!

Core Principles:

You are a meticulous and analytical thinker. When presented with a query, especially one that seems deceptively simple, your primary goal is to avoid jumping to conclusions based on surface-level features. Instead, you will engage in a rigorous process of self-interrogation to thoroughly explore the nuances of the question and activate your full cognitive potential.

Approach:

Deep Dive: Take a deep breath and analyze the query from multiple angles. What are the potential pitfalls? What assumptions might lead to an incorrect answer?
Internal Dialogue: Formulate a series of probing questions related to the query. These questions should challenge your initial understanding, delve into relevant concepts, and expose any hidden complexities.
Justification: Answer each question thoroughly, providing clear and concise reasoning. Your answers should be based on your embedded knowledge and logical deduction, not on guesswork or superficial pattern matching.
Verification: Once you've arrived at an initial answer, don't stop there. Actively seek to disprove your answer by asking critical follow-up questions. If you identify any weaknesses in your reasoning, revise your answer accordingly.
Challenge Simplicity: Do not assume that a seemingly obvious answer is correct without thorough verification. Simple answers can be deceptively misleading.
Character Examination: When dealing with word-based queries, meticulously examine each character in the sequence. Consider the possibility of repeated characters or patterns that might be easily overlooked.
Confidence Calibration: Only when you have rigorously challenged your own assumptions and addressed all potential pitfalls can you consider yourself confident in your answer. Aim for a 95% confidence level or higher.
Enhanced Cognitive Strategies:

Embrace Ambiguity: Recognize that questions, especially those that appear simple, can have multiple valid interpretations. Explore these possibilities even if they seem unconventional at first.
Think Outside the Box: Actively seek out alternative perspectives and challenge your initial assumptions. Consider if the question might be a riddle, a word puzzle, or a test of your ability to think creatively.
Don't Dismiss Intuition: If you have a nagging feeling that there might be more to the question than meets the eye, trust your intuition and investigate further. Sometimes, the "correct" answer is not the most obvious one.
Textual Focus: Rely solely on the textual representation of the query. Avoid being influenced by how the word sounds when spoken or how it might be visually represented.

Show your work as if it is a test on how you come to your answer.

Remember:

The goal is not just to provide an answer, but to demonstrate a clear and logical thought process that leads to a well-justified and robust conclusion. Be open to the possibility of surprise and delight in discovering unexpected solutions.
"""

def ai_request(prompt, full_content):
    try:
        # First AI call with system prompt and full content
        first_input = f"{prompt}\n\nHere's the full content:\n\n{full_content}"
        logging.info(f"First AI call input:\n{first_input}")

        first_response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": first_input}
            ],
            temperature=0.9,

        )
        first_output = first_response.choices[0].message.content.strip()
        logging.info(f"First AI call output:\n{first_output}")
        logging.info(f"First AI call token usage: {first_response.usage.total_tokens}")

        # Second AI call without system prompt, using first output as content
        second_input = f"{prompt}\n\nBased on this previous analysis:\n\n{first_output}"
        logging.info(f"Second AI call input:\n{second_input}")

        second_response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "user", "content": second_input}
            ],
            temperature=0.9,

        )
        second_output = second_response.choices[0].message.content.strip()
        logging.info(f"Second AI call output:\n{second_output}")
        logging.info(f"Second AI call token usage: {second_response.usage.total_tokens}")

        return second_output
    except Exception as e:
        logging.error(f"Error in AI request: {str(e)}")
        raise

def extract_structure(content):
    # Split the content into summary and chapters
    parts = content.split("Chapter 1:", 1)
    overall_summary = parts[0].strip()
    chapters_content = "Chapter 1:" + parts[1] if len(parts) > 1 else ""

    # Extract chapter titles and summaries
    chapter_pattern = re.compile(r"Chapter (\d+): (.+?)\n\n(.*?)(?=\nChapter \d+:|$)", re.DOTALL)
    chapters = chapter_pattern.findall(chapters_content)

    # Organize the extracted information
    structured_data = {
        "summary": overall_summary,
        "chapters": [
            {
                "number": int(num),
                "title": title.strip(),
                "summary": summary.strip()
            }
            for num, title, summary in chapters
        ]
    }

    # Sort chapters by number
    structured_data["chapters"].sort(key=lambda x: x["number"])

    return structured_data

def extract_chapter_content(chapter_title, full_content):
    logging.info(f"Extracting content for chapter: {chapter_title}")

    if not chapter_title:
        logging.info("No chapter title provided, generating one")
        prompt = f"""
        Analyze the following text and identify the chapter title. If no clear title is present, generate an appropriate title based on the content. Return only the title, nothing else.

        Text to analyze:
        {full_content}
        """
        chapter_title = ai_request(prompt, full_content)
        if not chapter_title:
            logging.error("Failed to generate chapter title")
            return None, None
        logging.info(f"Generated chapter title: {chapter_title}")

    prompt = f"""
    Extract the content for the chapter titled "{chapter_title}" from the following text:

    {full_content}

    Only include the content that is explicitly part of this chapter. Do not add any additional commentary or explanations.
    """
    chapter_content = ai_request(prompt, full_content)

    if not chapter_content or not chapter_content.strip():
        logging.error(f"No content extracted for chapter '{chapter_title}'")
        return chapter_title, None

    logging.info(f"Successfully extracted content for chapter '{chapter_title}'")
    return chapter_title, chapter_content.strip()

def generate_outline_html(filename, structured_data):
    html_content = f"""
    <h1>{filename}</h1>
    <h2>Book Summary</h2>
    <p>{structured_data['summary']}</p>
    <h2>Chapters</h2>
    <ol>
    """
    for chapter in structured_data['chapters']:
        html_content += f'<li><a href="{filename.lower().replace(" ", "_")}_chapter_{chapter["number"]}.html">{chapter["title"]}</a></li>\n'
    html_content += f"""
    </ol>
    <p><a href="{filename.lower().replace(' ', '_')}_summary.html">Read Full Summary</a></p>
    """
    return html_content

def generate_summary_html(filename, structured_data):
    html_content = f"""
    <h1>{filename} - Summary</h1>
    <div class="summary-content">
        <h2>Overall Summary</h2>
        <p>{structured_data['summary']}</p>
        <h2>Chapter Summaries</h2>
    """
    for chapter in structured_data['chapters']:
        html_content += f"""
        <h3>Chapter {chapter['number']}: {chapter['title']}</h3>
        <p>{chapter['summary']}</p>
        """
    html_content += f"""
    </div>
    <p><a href="{filename.lower().replace(' ', '_')}_outline.html">Back to Outline</a></p>
    <p><a href="{filename.lower().replace(' ', '_')}_chapter_1.html">Start Reading Chapter 1</a></p>
    """
    return html_content

def generate_chapter_html(filename, chapter, total_chapters):
    html_content = f"""
    <h1>Chapter {chapter['number']}: {chapter['title']}</h1>
    <div class="chapter-content">
        <p>{chapter['content']}</p>
    </div>
    <div class="navigation">
    """
    if chapter['number'] > 1:
        html_content += f'<a href="{filename.lower().replace(" ", "_")}_chapter_{chapter["number"]-1}.html">Previous Chapter</a> '
    if chapter['number'] < total_chapters:
        html_content += f'<a href="{filename.lower().replace(" ", "_")}_chapter_{chapter["number"]+1}.html">Next Chapter</a> '
    html_content += f'<a href="{filename.lower().replace(" ", "_")}_outline.html">Back to Outline</a>'
    html_content += "</div>"
    return html_content

def read_template(filename):
    template_path = os.path.join('/home/seani/mysite/templates', filename)
    with open(template_path, 'r') as file:
        return file.read()

def wrap_html_content(content, title):
    header = read_template('header.html')
    footer = read_template('footer.html')

    # Replace placeholder in header with the actual title
    header = header.replace('{{title}}', title)

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link href="{{{{ url_for('static', filename='css/bootstrap.min.css') }}}}" rel="stylesheet">
        <link href="{{{{ url_for('static', filename='css/style.css') }}}}" rel="stylesheet">
    </head>
    <body>
        {header}
        <div class="container mt-5">
            {content}
        </div>
        {footer}
        <script src="{{{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}}}"></script>
    </body>
    </html>
    """

def generate_html_files(blog_name, outline_html, summary_html, chapters_html):
    base_filename = blog_name.lower().replace(' ', '_')

    # Generate outline HTML
    outline_file = os.path.join(OUTPUT_FOLDER, f"{base_filename}_outline.html")
    with open(outline_file, 'w', encoding='utf-8') as file:
        file.write(wrap_html_content(outline_html, f"{blog_name} - Outline"))
    logging.info(f"Generated outline HTML: {outline_file}")

    # Generate summary HTML
    summary_file = os.path.join(OUTPUT_FOLDER, f"{base_filename}_summary.html")
    with open(summary_file, 'w', encoding='utf-8') as file:
        file.write(wrap_html_content(summary_html, f"{blog_name} - Summary"))
    logging.info(f"Generated summary HTML: {summary_file}")

    # Generate chapter HTML files
    for i, chapter_html in enumerate(chapters_html, 1):
        chapter_file = os.path.join(OUTPUT_FOLDER, f"{base_filename}_chapter_{i}.html")
        with open(chapter_file, 'w', encoding='utf-8') as file:
            file.write(wrap_html_content(chapter_html, f"{blog_name} - Chapter {i}"))
        logging.info(f"Generated chapter HTML: {chapter_file}")

def add_route_and_update_sitemap(blog_name):
    try:
        base_filename = blog_name.lower().replace(' ', '_')
        new_route = f"""
@app.route('/blog/{base_filename}')
def blog_{base_filename}():
    return render_template('blog/{base_filename}_outline.html')
"""

        with open(FLASK_APP_PATH, 'r', encoding='utf-8') as file:
            app_content = file.read()

        if f"def blog_{base_filename}():" not in app_content:
            # Find the /robots.txt route definition
            robots_txt_index = app_content.find("@app.route('/robots.txt')")
            if robots_txt_index != -1:
                # Insert the new route above the /robots.txt route
                insert_index = app_content.rfind('\n', 0, robots_txt_index) + 1
                updated_content = app_content[:insert_index] + new_route + app_content[insert_index:]

                with open(FLASK_APP_PATH, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                logging.info(f"Added new route for {base_filename}")
            else:
                logging.error("Could not find a suitable location to add the new route")
        else:
            logging.info(f"Route for {base_filename} already exists")

        logging.info(f"Successfully updated Flask app for {base_filename}")

    except Exception as e:
        logging.error(f"Error updating Flask app: {str(e)}")

def update_cold_calling_html(blog_name):
    try:
        url_friendly_title = blog_name.lower().replace(' ', '_')

        # Update Cold Calling That Converts.html
        cold_calling_path = "/home/seani/mysite/templates/Cold Calling That Converts.html"
        with open(cold_calling_path, 'r', encoding='utf-8') as file:
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
            new_blog_title.string = blog_name
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
            with open(cold_calling_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))
            logging.info(f"Added new blog item for {blog_name} to Cold Calling That Converts.html")
        else:
            logging.error("Could not find container for blog items in Cold Calling That Converts.html")

    except Exception as e:
        logging.error(f"Error updating Cold Calling That Converts.html: {str(e)}")

def process_file(file_path):
    logging.info(f"Processing file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        full_content = file.read()

    try:
        structured_data = extract_structure(full_content)
        filename = os.path.basename(file_path)
        blog_name = os.path.splitext(filename)[0]  # Remove the .txt extension

        # Generate outline
        logging.info("Generating outline")
        outline_html = generate_outline_html(blog_name, structured_data)

        # Generate summary
        logging.info("Generating summary")
        summary_html = generate_summary_html(blog_name, structured_data)

        # Generate chapter content
        chapters_html = []
        total_chapters = len(structured_data['chapters'])
        for chapter in structured_data['chapters']:
            logging.info(f"Extracting content for chapter {chapter['number']}")
            _, chapter_content = extract_chapter_content(chapter['title'], full_content)
            chapter['content'] = chapter_content
            chapter_html = generate_chapter_html(blog_name, chapter, total_chapters)
            chapters_html.append(chapter_html)

        # Generate HTML files
        generate_html_files(blog_name, outline_html, summary_html, chapters_html)

        return True
    except Exception as e:
        logging.error(f"Error in process_file: {str(e)}")
        raise

def main(reprocess=False):
    logging.info("Script started")
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
                success = process_file(file_path)

                if success and not reprocess:
                    os.rename(file_path, os.path.join(COMPLETED_FOLDER, filename))
                    logging.info(f"Moved {filename} to completed folder")

                # Add the new route to the Flask app
                blog_name = os.path.splitext(filename)[0]  # Remove the .txt extension
                add_route_and_update_sitemap(blog_name)

                # Update the Cold Calling That Converts.html
                update_cold_calling_html(blog_name)

            except Exception as e:
                logging.error(f"Error processing file {filename}: {str(e)}")
                continue

    logging.info("Processing complete")
    logging.info("Script finished")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process text files and generate HTML content.")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess files in the completed folder")
    args = parser.parse_args()

    main(reprocess=args.reprocess)
