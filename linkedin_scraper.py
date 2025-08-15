import json
import time
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from dotenv import load_dotenv, dotenv_values 
import os
from utils import print_warn, print_error 
load_dotenv() 

class LinkedInScraper:
    def __init__(self, headless=False):
        self.driver = None
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(os.getenv('CHROMEDRIVER_PATH', 'chromedriver'))  # Ensure CHROMEDRIVER_PATH is set in .env
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login(self, username, password):
        """Login to LinkedIn"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for successful login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "global-nav"))
            )
            print("Successfully logged in to LinkedIn")
            return True
            
        except TimeoutException:
            print_error("Login failed - timeout")
            return False
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False
    
    def search_company(self, company_name):
        """Search for a company on LinkedIn"""
        try:
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name.replace(' ', '%20')}"
            self.driver.get(search_url)
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results-container"))
            )
            
            # Find the first company result
            company_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/company/')]")
            if company_links:
                company_url = company_links[0].get_attribute('href')
                return company_url
            
        except TimeoutException:
            print_error(f"Could not find company: {company_name}")
        except Exception as e:
            print_error(f"Error searching for {company_name}: {str(e)}")
        
        return None
    
    def scrape_company_posts(self, company_url, max_posts=10):
        """Scrape recent posts from a company's LinkedIn page"""
        posts_data = []
        
        try:
            # Navigate to company posts
            posts_url = f"{company_url}/posts/"
            self.driver.get(posts_url)
            
            # Wait for posts to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "scaffold-finite-scroll__content"))
            )
            
            # Scroll to load more posts
            for _ in range(3):  # Scroll 3 times to load more content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Find post elements
            posts = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'feed-shared-update-v2')]")
            
            for i, post in enumerate(posts[:max_posts]):
                try:
                    post_data = self.extract_post_data(post)
                    if post_data:
                        posts_data.append(post_data)
                except Exception as e:
                    print_error(f"Error extracting post {i}: {str(e)}")
                    
        except TimeoutException:
            print_error(f"Could not load posts for {company_url}")
        except Exception as e:
            print_error(f"Error scraping posts: {str(e)}")
            
        return posts_data
    
    def extract_post_data(self, post_element):
        """Extract data from a single post element"""
        try:
            # Extract post text
            text_element = post_element.find_element(By.XPATH, ".//span[contains(@class, 'break-words')]")
            post_text = text_element.text if text_element else ""
            
            # Extract timestamp
            time_element = post_element.find_element(By.XPATH, ".//time")
            timestamp = time_element.get_attribute('datetime') if time_element else ""
            
            # Extract engagement metrics (likes, comments, etc.)
            try:
                engagement_element = post_element.find_element(By.XPATH, ".//button[contains(@aria-label, 'reactions')]")
                engagement_text = engagement_element.text if engagement_element else "0"
            except NoSuchElementException:
                engagement_text = "0"
            
            return {
                'post_text': post_text,
                'timestamp': timestamp,
                'engagement': engagement_text,
                'scraped_at': datetime.now().isoformat()
            }
            
        except NoSuchElementException:
            return None
    
    def scrape_companies_from_json(self, data, max_posts_per_company=10):
        """Main function to scrape all companies from JSON file"""
        # Read companies from JSON
        
        all_company_data = []
        
        try:
            for company in data['companies']:
                company_name = company['name']
                print(f"Processing company: {company_name}")
                
                # Search for company
                company_url = self.search_company(company_name)
                
                if company_url:
                    print(f"Found company URL: {company_url}")
                    
                    # Scrape posts
                    posts = self.scrape_company_posts(company_url, max_posts_per_company)
                    
                    company_data = {
                        'company_name': company_name,
                        'company_url': company_url,
                        'posts': posts,
                        'total_posts_scraped': len(posts)
                    }
                    
                    all_company_data.append(company_data)
                    print(f"Scraped {len(posts)} posts for {company_name}")
                    
                    # Add delay between companies to avoid rate limiting
                    time.sleep(5)
                else:
                    print_warn(f"Could not find LinkedIn page for {company_name}")
        except Exception as e:
            print_error(f"Error processing company {company_name}: {str(e)}")
        return all_company_data
    
    def save_to_csv(self, data, output_file):
        """Save scraped data to CSV file"""
        rows = []
        for company in data:
            scraped_at = datetime.now().isoformat()
            if company['posts']:
                for post in company['posts']:
                    rows.append({
                        'company_name': company['company_name'],
                        'company_url': company['company_url'],
                        'post_text': post['post_text'],
                        'timestamp': post['timestamp'],
                        'engagement': post['engagement'],
                        'scraped_at': scraped_at
                    })
            else:
                # Add a row even if no posts were found
                rows.append({
                    'company_name': company['company_name'],
                    'company_url': company['company_url'],
                    'post_text': '',
                    'timestamp': '',
                    'engagement': '',
                    'scraped_at': scraped_at
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
    
    def save_to_json(self, data, output_file):
        """Save scraped data to JSON file"""
        with open(output_file, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"Data saved to {output_file}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    # Configuration
    JSON_FILE = "Scrape.json"
    OUTPUT_CSV = "linkedin_posts.csv"
    OUTPUT_JSON = "linkedin_posts.json"
    LINKEDIN_USERNAME = os.getenv('LINKEDIN_USERNAME')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    with open(JSON_FILE, 'r') as file:
        data = json.load(file)
    
    data['companies'] = [data['companies'][0]]

    scraper = LinkedInScraper(headless=False)  # Set to True to run headless

    try:
        # Login to LinkedIn
        if scraper.login(LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
            print("Starting company scraping...")
            
            # Scrape companies
            company_data = scraper.scrape_companies_from_json(data, max_posts_per_company=5)
            
            # Save results
            scraper.save_to_csv(company_data, OUTPUT_CSV)
            scraper.save_to_json(company_data, OUTPUT_JSON)
            
            print(f"Scraping completed. Processed {len(company_data)} companies.")
        else:
            print_error("Failed to login to LinkedIn")
    except Exception as e:
        print_error(f"Error during scraping: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
