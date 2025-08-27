import requests
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()
access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")

url = "https://api.linkedin.com/rest/posts"
author f"author={encoded person urn or organization urn like urn%3Ali%3Aperson%3A5abc_dEfgH or urn%3Ali%3Aorganization%3A2414183}" 
additional_params = "&q=author&count=10&sortBy=LAST_MODIFIED"

final_url_query = f"{url}?{author}{additional_params}"


"https://api.linkedin.com/rest/posts?dscAdAccount={encoded dscAdAccount}&q=dscAdAccount&dscAdTypes=List(STANDARD,VIDEO)"

def extract_data(author_urns, access_token):
    """
    For each author URN, make a GET request to LinkedIn's posts API and collect the results.
    """
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    results = []
    for urn in author_urns:
        author = f"author={urn}"
        additional_params = "&q=author&count=10&sortBy=LAST_MODIFIED"
        final_url_query = f"{url}?{author}{additional_params}"
        response = requests.get(final_url_query, headers=headers)
        if response.status_code == 200:
            results.append(response.json())
        else:
            results.append({"urn": urn, "error": response.status_code, "message": response.text})
    return results