import os
import re

for root, dirs, files in os.walk('.'):
    if '.git' in dirs:
        dirs.remove('.git')
    for file in files:
        if file == 'scrub_all.py':
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Catch any Groq or OpenAI key
            new_content = re.sub(r'gsk_[A-Za-z0-9_\-]{10,}', 'REMOVED_GROQ_KEY', content)
            new_content = re.sub(r'sk-[A-Za-z0-9_\-]{10,}', 'REMOVED_OPENAI_KEY', new_content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Scrubbed keys in {filepath}")
        except:
            pass
