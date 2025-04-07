#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import pandas as pd

base_url = "https://www.shl.com/solutions/products/product-catalog/"
LANDING_URL = "https://www.shl.com"
DATA_DIR = "data/"

# Function to extract table data
def extract_table_data(table):
    data = []
    for row in table.find_all('tr')[1:]:  # Skip header row
        cols = row.find_all('td')
        if cols:
            # 1. Getting the URL
            link = cols[0].find('a', href=True)
            url = link['href'] if link else None
            if url and not url.startswith(LANDING_URL):
                url = LANDING_URL + url
            # 2. Name of the assessment solution
            name = link.get_text(strip=True) if link else cols[0].get_text(strip=True)
            # 3. Remote testing - True or False
            remote_testing = bool(cols[1].find('span', class_="catalogue__circle -yes"))
            # 4. Adaptive/IRT - True or False
            adaptive_irt = bool(cols[2].find('span', class_="catalogue__circle -yes"))
            # 5. Test type - A, B, C, D, E, K, P, S
            test_type = " ".join([elem.get_text(strip=True) for elem in cols[3].find_all('span', class_="product-catalogue__key")])

            data.append({'Name': name, 
                         'URL': url, 
                         'Remote_Testing': "yes" if remote_testing else "no",
                         'Adaptive_IRT': "yes" if adaptive_irt else "no",
                         'Test_Type': test_type
                         })
    return data


def scrape_records(table_num: int = -1) -> None:
    """
    Scrapes table data from a paginated website and saves it to a CSV file.
    This function fetches HTML content from a base URL, extracts table data from the last table
    on each page, and follows pagination links to scrape data from subsequent pages. The scraped
    data is saved to a CSV file, with the file name determined by the `table_num` parameter.
    Args:
        table_num (int, optional): Determines the output CSV file name.
            - If `table_num` is -1 (default), individual test solutions data is scraped'.
            - If `table_num` is 0, prepackaged job solutions data is scraped.
    Returns:
        None
    Raises:
        Requests-related exceptions if there are issues with HTTP requests.
        AttributeError if expected HTML elements are not found during scraping.
    Notes:
        - The function assumes the presence of a global `base_url` and `LANDING_URL` variable.
        - The helper function `extract_table_data` is used to process table data.
        - The function removes duplicate records before saving the data to a CSV file.
        - Multiple attempts may be needed to scrape properly due to the website's structure.
    """

    records = []
    session = requests.Session()
    response = session.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')

    table = tables[-1] ## Change 1
    records.extend(extract_table_data(table))
    next_page_element = soup.find_all('li', class_='pagination__item -arrow -next')[-1] ## Change 2
    next_page_url = next_page_element.find('a').get('href') if next_page_element else None
    print(next_page_url)

    while next_page_url:
        response = session.get(LANDING_URL + next_page_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find_all('table')[-1] ## Change 3
        records.extend(extract_table_data(table))
        next_page_element = soup.find_all('li', class_='pagination__item -arrow -next')
        next_page_url = next_page_element[-1].find('a').get('href') if next_page_element else None

        print(next_page_url)

    df = pd.DataFrame(records).drop_duplicates()
    if table_num == -1:
        df.to_csv(DATA_DIR + 'individual_test_solutions.csv', index=False)
    elif table_num == 0:
        df.to_csv(DATA_DIR + 'prepackaged_job_solutions.csv', index=False)
    
    session.close()


def get_product_text(url):
    """
    Fetches and extracts product-related text from a given URL.
    Args:
        url (str): The URL of the webpage to scrape.
    Returns:
        str: A concatenated string of extracted text, with each element separated by a newline.
    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request.
        AttributeError: If the expected HTML elements are not found in the page.
    """
    session = requests.Session()
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    texts = [soup.find('h1').get_text(strip=True)]
    texts.extend([
        elem.get_text(separator='\n', strip=True) 
        for elem in soup.find_all('div', class_="product-catalogue-training-calendar__row typ")
        ])
    session.close()
    return "\n".join(texts)


def augment_records(dataset: int = 1, file_path: str = DATA_DIR + "individual_test_solutions.csv") -> None:
    """
    Augments the records in the specified dataset by scraping product-related text 
    and appending it to the existing data. The updated data is then saved to a new CSV file.

    Args:
        dataset (int, optional): Specifies the dataset to use. Defaults to 1.
            - 0: Uses the "prepackaged_job_solutions.csv" file.
            - 1: Uses the "individual_test_solutions.csv" file.
        file_path (str, optional): The file path to the dataset CSV file. Defaults to 
            DATA_DIR + "individual_test_solutions.csv".

    Returns:
        None: The function saves the augmented dataset to a new CSV file with 
        "_with_description" appended to the original file name.

    Notes:
        - The function scrapes product-related text from URLs in the "URL" column 
          using the `get_product_text` function.
        - The scraped text is combined with the "Remote_Testing" column to form 
          the "Description" column.
        - The "Assessment_Time" column is extracted from the "Description" column 
          using a regex pattern to find the number of minutes.
    """

    if dataset == 0:
        file_path = DATA_DIR + "prepackaged_job_solutions.csv"
    df = pd.read_csv(file_path)
    # 1. Scrape product-related text from URLs
    df['Description'] = df.loc[:, "URL"].map(get_product_text)
    # 2. Combine the scraped text with the "Remote_Testing" column
    df["Description"] = df.loc[:, "Description"] + " " + df.loc[:, "Remote_Testing"]
    # 3. Extract the number of minutes from the "Description" column
    df["Assessment_Time"] = df.loc[:, "Description"].str.extract(r'minutes = (\d*)\s')
    df.to_csv(file_path[:-4] + "_with_description" + file_path[-4:], index=False)


if __name__ == "__main__":
    # scrape_records(table_num=-1)
    ...