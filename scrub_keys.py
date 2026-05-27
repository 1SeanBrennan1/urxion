import os
import re
import shutil

# Delete the backup folder (it contains the leaked text files)
if os.path.exists('code_copy'):
    shutil.rmtree('code_copy')
    print("Deleted 'code_copy' folder.")

# Clean the actual Python files
files_to_clean = ['blog_generator.py', 'miniblogpostredo.py']
for file in files_to_clean:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use Regex to find and replace Groq (gsk_) and OpenAI (sk-) keys
        content = re.sub(r'gsk_[A-Za-z0-9_\-]+', 'REMOVED_GROQ_KEY', content)
        content = re.sub(r'sk-[A-Za-z0-9_\-]+', 'REMOVED_OPENAI_KEY', content)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Scrubbed keys in {file}")
