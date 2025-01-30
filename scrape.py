import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_bill_info_selenium(url):
    """
    Use Selenium with webdriver-manager to open 'url' in a browser,
    find elements by their classes/IDs, and return the Digest and Bill Authors as text.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # runs in headless mode
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=chrome_options
    )
    digest_text = "Digest not found"
    authors_text = "Authors not found"

    try:
        driver.get(url)

        # Wait for the root element of the React app to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "root"))
        )

        # Additional wait to ensure all dynamic content is loaded
        time.sleep(10)

        # Retry mechanism to handle cases where elements are not immediately available
        retries = 3
        while retries > 0:
            try:
                # Use WebDriverWait to wait for the Digest element to appear
                digest_element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.BillDetails_digest__3rGrH p.CollapsibleDigest_digestText__1KQdW"))
                )
                digest_text = digest_element.text
                break
            except Exception as e:
                print(f"Retry {3 - retries + 1}: Failed to find Digest element: {e}")
                retries -= 1
                time.sleep(5)  # Wait before retrying

        # Capture a screenshot after loading the page
        screenshot_path = f'screenshot_{url.split("/")[-2]}.png'
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        # Get the page source to debug issues
        page_source_path = f'page_source_{url.split("/")[-2]}.html'
        with open(page_source_path, 'w') as file:
            file.write(driver.page_source)
        print(f"Page source saved to {page_source_path}")

        # Update this part to find the Bill Authors element if necessary
        # authors_element = WebDriverWait(driver, 10).until(
        #     EC.visibility_of_element_located((By.CSS_SELECTOR, "YOUR_AUTHORS_SELECTOR"))
        # )
        # authors_text = authors_element.text

    except Exception as e:
        print(f"Failed to retrieve or parse {url}: {e}")
    finally:
        driver.quit()

    return digest_text, authors_text

def main():
    # Load your spreadsheet; assuming the file is in the same directory
    df = pd.read_excel("edbills.xlsx")

    # Ensuring columns for text storage are string/object
    for col in ["Digest", "Bill Authors"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype('string')

    # Iterate over each row, sanitize URL, then scrape
    for index, row in df.iterrows():
        raw_url = row.get("URL Address", "")
        
        # Remove leading/trailing whitespace and any extra embedded spaces
        sanitized_url = raw_url.strip().replace(" ", "")
        if not sanitized_url:
            continue
        
        digest, authors = scrape_bill_info_selenium(sanitized_url)
        df.at[index, "Digest"] = digest
        df.at[index, "Bill Authors"] = authors

    # Save the updated data
    df.to_excel("edbills_output.xlsx", index=False)
    print("Selenium-based scraping completed. Check edbills_output.xlsx.")

if __name__ == "__main__":
    main()