# Constants
OPENAI_API_KEY = 









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
#OPENAI_API_KEY = "your_api_key_here"  # Add your OpenAI API key here
ARTICLES_FOLDER = "/home/seani/mysite/articles"
COMPLETED_FOLDER = "/home/seani/mysite/articles/completed"
OUTPUT_FOLDER = "/home/seani/mysite/templates/blog"
FLASK_APP_PATH = "/home/seani/mysite/flask_app.py"
SITEMAP_PATH = "/home/seani/mysite/sitemap.xml"
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

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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

        first_response = openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": first_input}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        first_output = first_response.choices[0].message.content
        logging.info(f"First AI call output:\n{first_output}")
        logging.info(f"First AI call token usage: {first_response.usage.total_tokens}")

        # Second AI call without system prompt, using first output as content
        second_input = f"{prompt}\n\nBased on this previous analysis:\n\n{first_output}"
        logging.info(f"Second AI call input:\n{second_input}")

        second_response = openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "user", "content": second_input}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        second_output = second_response.choices[0].message.content
        logging.info(f"Second AI call output:\n{second_output}")
        logging.info(f"Second AI call token usage: {second_response.usage.total_tokens}")

        return second_output
    except Exception as e:
        logging.error(f"Error in AI request: {str(e)}")
        raise

def extract_structure(content):
    # Extract overall summary (everything before Chapter 1)
    overall_summary = content.split("Chapter 1:", 1)[0].strip()

    # Extract chapters
    chapter_pattern = re.compile(r"Chapter (\d+): (.+?)(?=\nChapter \d+:|$)", re.DOTALL)
    chapters = chapter_pattern.findall(content)

    return overall_summary, chapters

def create_html_files(filename, chapters, content):
    base_filename = filename.lower().replace(' ', '_')

    # Read header and footer
    with open("/home/seani/mysite/templates/header.html", 'r', encoding='utf-8') as f:
        header = f.read()
    with open("/home/seani/mysite/templates/footer.html", 'r', encoding='utf-8') as f:
        footer = f.read()

    # Extract book summary (everything before Chapter 1)
    book_summary = content.split("Chapter 1")[0].strip()

    # Create outline HTML
    outline_html = f"{header}\n<h1>{filename}</h1>\n<p>{book_summary}</p>\n<h2>Chapters</h2>\n<ul>"

    processed_chapters = set()
    for num, title in chapters:
        if num in processed_chapters:
            continue
        processed_chapters.add(num)

        chapter_filename = f"{base_filename}_chapter_{num}.html"
        chapter_summary = extract_chapter_summary(content, num, title)
        outline_html += f'<li><h3><a href="{chapter_filename}">Chapter {num}: {title}</a></h3><p>{chapter_summary}</p></li>'

    outline_html += f"</ul>\n{footer}"
    with open(os.path.join(OUTPUT_FOLDER, f"{base_filename}_outline.html"), 'w', encoding='utf-8') as f:
        f.write(outline_html)

    # Update chapter HTML files with navigation links
    for i, (num, title) in enumerate(chapters):
        if i >= len(processed_chapters):
            break

        chapter_filename = f"{base_filename}_chapter_{num}.html"
        chapter_path = os.path.join(OUTPUT_FOLDER, chapter_filename)

        if not os.path.exists(chapter_path):
            logging.warning(f"Chapter file not found: {chapter_filename}")
            continue

        with open(chapter_path, 'r', encoding='utf-8') as f:
            chapter_content = f.read()

        soup = BeautifulSoup(chapter_content, 'html.parser')

        # Add navigation links
        nav_links = "<div class='chapter-nav'>"
        if i > 0:
            prev_chapter = f"{base_filename}_chapter_{chapters[i-1][0]}.html"
            nav_links += f"<a href='{prev_chapter}'>Previous Chapter</a> | "
        nav_links += f"<a href='{base_filename}_outline.html'>Outline</a>"
        if i < len(processed_chapters) - 1:
            next_chapter = f"{base_filename}_chapter_{chapters[i+1][0]}.html"
            nav_links += f" | <a href='{next_chapter}'>Next Chapter</a>"
        nav_links += "</div>"

        # Insert navigation links at the end of the content
        content_div = soup.find('div', class_='chapter-content')
        if content_div:
            content_div.append(BeautifulSoup(nav_links, 'html.parser'))
        else:
            logging.warning(f"Content div not found in {chapter_filename}")

        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    logging.info(f"Completed creating/updating HTML files for {filename}")

def extract_chapter_content(content, chapter_num, chapter_title):
    # Define the pattern to match chapter content
    chapter_pattern = re.compile(rf"Chapter\s*{chapter_num}\s*.*?(?=Chapter\s*\d+|$)", re.DOTALL | re.IGNORECASE)

    # Find all matches for the chapter content
    chapter_matches = chapter_pattern.findall(content)

    # Join all matches, preserving all content
    chapter_content = "\n".join(match.strip() for match in chapter_matches)

    logging.info(f"Extracted content for Chapter {chapter_num}: {len(chapter_content)} characters")
    return chapter_content

def refine_chapter_content(chapter_content, chapter_num, chapter_title):
    prompt = f"""
    Please organize and refine the following content for Chapter {chapter_num}: {chapter_title}.
    The content contains multiple sections about different aspects of the chapter.
    Organize related information and ensure a logical flow, but do not remove any significant content.
    Format the content with appropriate HTML tags for headings, paragraphs, and lists, but DO NOT include any <!DOCTYPE>, <html>, <head>, or <body> tags.
    Start directly with the content, assuming it will be placed within an existing <div> element.

    Content:
    {chapter_content}
    """

    return ai_request(prompt, chapter_content)

def update_flask_app(filename, chapters):
    with open(FLASK_APP_PATH, 'r') as f:
        flask_app_content = f.read()

    base_filename = filename.lower().replace(' ', '_')
    new_routes = []

    for num, title in chapters:
        route = f"""
@app.route('/blog/{base_filename}_chapter_{num}')
def {base_filename}_chapter_{num}():
    return render_template('blog/{base_filename}_chapter_{num}.html')
"""
        new_routes.append(route)

    new_routes_str = "\n".join(new_routes)

    if "# New Routes" in flask_app_content:
        flask_app_content = flask_app_content.replace("# New Routes", f"# New Routes\n{new_routes_str}")
    else:
        flask_app_content += f"\n# New Routes\n{new_routes_str}"

    with open(FLASK_APP_PATH, 'w') as f:
        f.write(flask_app_content)

def update_sitemap(filename, chapters):
    if not os.path.exists(SITEMAP_PATH):
        # Create a new sitemap.xml file if it doesn't exist
        root = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        tree = ET.ElementTree(root)
        tree.write(SITEMAP_PATH)

    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()

    base_filename = filename.lower().replace(' ', '_')
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    for num, title in chapters:
        url = ET.Element('url')
        loc = ET.SubElement(url, 'loc')
        loc.text = f"http://yourdomain.com/blog/{base_filename}_chapter_{num}"
        lastmod = ET.SubElement(url, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')
        root.append(url)

    tree.write(SITEMAP_PATH)

chapter_summary_cache = {}

def extract_chapter_summary(content, chapter_num, chapter_title):
    if chapter_num in chapter_summary_cache:
        return chapter_summary_cache[chapter_num]

    chapter_content = extract_chapter_content(content, chapter_num, chapter_title)
    prompt = f"Summarize the following chapter in 2-3 sentences:\n\nChapter {chapter_num}: {chapter_title}\n\n{chapter_content[:1000]}"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        summary = response.choices[0].message.content.strip()
        chapter_summary_cache[chapter_num] = summary
        return summary
    except Exception as e:
        logging.error(f"Error generating summary for Chapter {chapter_num}: {str(e)}")
        return f"Summary not available for Chapter {chapter_num}: {chapter_title}"

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    filename = os.path.splitext(os.path.basename(file_path))[0]
    overall_summary, chapters = extract_structure(content)

    logging.info(f"Processing file: {filename}")

    create_html_files(filename, chapters, content)
    update_flask_app(filename, chapters)
    update_sitemap(filename, chapters)

    # Move processed file to COMPLETED_FOLDER
    shutil.move(file_path, os.path.join(COMPLETED_FOLDER, os.path.basename(file_path)))

def main():
    for filename in os.listdir(ARTICLES_FOLDER):
        if filename.endswith('.txt'):
            file_path = os.path.join(ARTICLES_FOLDER, filename)
            logging.info(f"Processing file: {filename}")
            process_file(file_path)
            logging.info(f"Completed processing file: {filename}")

if __name__ == "__main__":
    main()
