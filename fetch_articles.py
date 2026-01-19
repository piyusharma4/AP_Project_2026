from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import trafilatura
import json

def get_article_links(topic_url):
    # Setup Chrome options (headless = no visible UI window)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    print(f"Fetching: {topic_url}")
    driver.get(topic_url)
    
    # Wait for JavaScript to load the content
    time.sleep(5)
    
    # Scroll down to trigger lazy loading (repeat if there are many articles)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Extract article elements
    # Note: These selectors depend on the site's current CSS class names. 
    # We look for anchor tags <a> that contain '/en/articles/' in the href.
    articles = driver.find_elements(By.CSS_SELECTOR, "a[href^='/en/articles/']")
    
    results = []
    seen_urls = set()
    
    for article in articles:
        url = article.get_attribute('href')
        title = article.text.strip()
        
        # Filter out duplicates and non-article links
        if url and url not in seen_urls and "/topic/" not in url:
            # Sometimes titles are empty if the link wraps an image, so we fallback
            if not title:
                title = "No Title Found"
            
            results.append({'title': title, 'url': url})
            seen_urls.add(url)
            
    driver.quit()
    return results

#===========================================

def chunk_text(text, chunk_size=1000, overlap=100):
    if not text:
        return []

    words = text.split()
    chunks=[]
    current_chunk=[]
    current_length=0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1

        if current_length >= chunk_size:
            # Join words to form the chunk string
            chunk_str = " ".join(current_chunk)
            chunks.append(chunk_str)

            #Keep the last few words to overlap
            overlap_count = int(overlap / 10)
            current_chunk = current_chunk[-overlap_count:]
            current_length = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# Run the function
for i in range(1,259):
    topic_url = f"https://acharyaprashant.org/en/articles/topic/{i}"
    links = get_article_links(topic_url)

    print(f"Found {len(links)} articles:")
    for link in links:
        print(f"- {link['url']}")
    # print(text)


#Run a single topic 
# example_topic = f"https://acharyaprashant.org/en/articles/topic/69"
# links = get_article_links(example_topic)
# print(f"Found {len(links)} articles:")
# for link in links:
#     print(f"- {link['url']}")



#=====================================

#Main Processing Loop
processed_data =[]

print("Staring extraction...")
for link in links:
    print(f"Processing: {link['url']}")
    downloaded = trafilatura.fetch_url(link['url'])

    #Extract Text and Metadata
    metadata = trafilatura.extract(downloaded, output_format="json", include_comments=False)
    
    if metadata:
        meta_dict = json.loads(metadata)
        full_text = meta_dict.get("text", '')

        #Create chunks
        text_chunks = chunk_text(full_text)

        #Structure the data for Vector Storage
        for i, chunk in enumerate(text_chunks):
            record = {
                "id": f"{link['url']}_{i}",         # Unique ID for Chroma
                "text": chunk,              # The content to embed
                "metadata": {               # Data to filter by later
                    "source": link['url'],
                    "chunk_index": i
                }
            }
            processed_data.append(record)        

#Save to JSONL
output_file = "knowledge_base.jsonl"
with open(output_file, 'w', encoding='utf-8') as f:
    for entry in processed_data:
        json.dump(entry, f)
        f.write('\n')

print(f"Successfully saved {len(processed_data)} chunks to {output_file}")


