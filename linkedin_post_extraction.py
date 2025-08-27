
url = "https://api.linkedin.com/rest/posts"
author f"author={encoded person urn or organization urn like urn%3Ali%3Aperson%3A5abc_dEfgH or urn%3Ali%3Aorganization%3A2414183}" 
additional_params = "&q=author&count=10&sortBy=LAST_MODIFIED"

final_url_query = f"{url}?{author}{additional_params}"

