import re
import random

def parse_spintax(text: str) -> str:
    """
    Parses spintax in the format {Option 1|Option 2|Option 3}.
    Nested spintax is not supported for simplicity.
    """
    if not text:
        return ""
        
    pattern = re.compile(r'\{([^{}]+)\}')
    
    while True:
        match = pattern.search(text)
        if not match:
            break
            
        options = match.group(1).split('|')
        selected = random.choice(options).strip()
        text = text[:match.start()] + selected + text[match.end():]
        
    return text

if __name__ == "__main__":
    test_text = "{Hello|Hi|Hey} there! This is a {test|trial|check}."
    for _ in range(5):
        print(parse_spintax(test_text))
