import requests
from bs4 import BeautifulSoup

def fetch_question_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the question title
        title_tag = soup.find('h1', class_='question-hyperlink')
        title = title_tag.get_text(strip=True) if title_tag else "No title found"
        
        # Find the question content
        content_tag = soup.find('div', class_='js-post-body')
        if content_tag:
            content_excerpt = content_tag.find('div', class_='s-post-summary--content-excerpt')
            if content_excerpt:
                content = content_excerpt.get_text(strip=True)
            else:
                content = ""
        else:
            content = ""
        
        # Find comments
        comments = []
        comments_list = soup.find('ul', class_='comments-list js-comments-list')
        if comments_list:
            comment_items = comments_list.find_all('li', class_='comment js-comment')
            for comment_item in comment_items:
                comment_text = comment_item.find('span', class_='comment-copy')
                if comment_text:
                    comment = comment_text.get_text(strip=True)
                    comments.append(comment)
        
        return title, content, comments
    else:
        return "Error fetching the page", f"Status code: {response.status_code}", []

def search_stackexchange(query):
    # Format the URL with the query
    url = f'https://gis.stackexchange.com/search?q={query}'
    print(url)

    # Send the HTTP request to fetch the page content
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Page fetched successfully.")

        # Find all the question summaries
        question_summaries = soup.find_all('div', class_='s-post-summary')

        # Extract question titles and links
        gis_questions = []
        for summary in question_summaries:
            # Find the link within the summary
            link_tag = summary.find('a', class_='s-link')
            if link_tag:
                href = link_tag.get('href')
                title = link_tag.get_text(strip=True)
                if href and href.startswith('/questions/'):
                    gis_questions.append((title, href))
                    print(f"Found question: {title} - {href}")

        # If we found any questions, print the first 5
        if gis_questions:
            combined_contexts = []
            print(f"Search results for '{query}':")
            for title, href in gis_questions[:5]:  # Limit to the first 5 results
                link = f"https://gis.stackexchange.com{href}"
                print(f"{title} - {link}")
                
                # Fetch and display the content of the question
                question_title, question_content, comments = fetch_question_content(link)
                print(f"\nTitle: {question_title}\n")
                print(f"Content: {question_content}\n")
                
                if comments:
                    print("Comments:")
                    for comment in comments:
                        print(f"- {comment}\n")
                
                # Combine content and comments
                combined_content = question_content
                if comments:
                    combined_content += "\n\nComments:\n" + "\n".join(f"- {comment}" for comment in comments)
                combined_contexts.append(combined_content)
            
            # Pass combined contexts to AI assistant
            parsed_content = pass_to_ai_assistant(combined_contexts)
            return parsed_content
        else:
            print("No relevant results found.")
    else:
        print("Error fetching the page. Status code:", response.status_code)

def pass_to_ai_assistant(contexts):
    # This function should contain the logic to pass the contexts to your AI assistant
    print("Passing contexts to AI assistant:")
    combined_external_content = "\n\n".join(contexts)
    return combined_external_content