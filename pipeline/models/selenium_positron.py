import math
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from pyvirtualdisplay import Display

class Positron:
    __username = None
    __password = None
    __driver = None
    __url = "https://www.positronrt.com.br/rastreador5"
    __wait = None
    headless = True
    __display = None
    
    @classmethod
    def start(cls, username, password):
        cls.__username = username
        cls.__password = password
        cls.__open_browser()
        cls.__authenticate()
        
    @classmethod
    def set_url(cls, url):
        cls.__url = url
        
    @classmethod
    def set_headless(cls, headless):
        cls.headless = headless
        
    @classmethod
    def __open_browser(cls):
        print("Starting virtual display")
        cls.__display = Display(visible=0, size=(800, 600))
        cls.__display.start()
        
        print("Setting Firefox options")
        options = Options()
        
        if cls.headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=800,600')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--enable-automation')
            
            # Simular navegador real
            options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference('useAutomationExtension', False)
            
            # Aceitar cookies e habilitar JavaScript
            options.set_preference("network.cookie.cookieBehavior", 0)
            options.set_preference("javascript.enabled", True)
            
            # Configurar idioma e timezone
            options.set_preference("intl.accept_languages", "pt-BR, pt")
            options.set_preference("browser.timezone.mode", "system")
            
            # Simular recursos de hardware
            options.set_preference("media.navigator.enabled", True)
            options.set_preference("media.navigator.permission.disabled", True)
            options.set_preference("dom.webnotifications.enabled", True)
            
            # Evitar fingerprinting
            options.set_preference("privacy.resistFingerprinting", False)
            options.set_preference("webgl.disabled", False)
            
        print("Starting Firefox browser")
        cls.__driver = webdriver.Firefox(options=options)
        
        # Adicionar headers personalizados
        cls.__driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Waiting for the browser to open...")
        cls.__wait = WebDriverWait(cls.__driver, 30)
        cls.__wait.until(EC.presence_of_element_located((By.TAG_NAME, "html")))
        print("Browser started successfully")
        
    
    @classmethod
    def __authenticate(cls):
        print("Starting authentication")
        cls.__driver.get(cls.__url)
        # Login
        username_input = cls.__wait.until(
            EC.presence_of_element_located((By.ID, "j_username"))
        )
        print("Username field found")
        username_input.clear()
        username_input.send_keys(cls.__username)
        
        # Espera explícita pelo campo de senha
        password_input = cls.__wait.until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print("Password field found")
        # password_input = cls.__driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(cls.__password)

        # Clicar no botão de login
        # Espera explícita pelo botão de login
        login_button = cls.__wait.until(
            EC.element_to_be_clickable((By.ID, "enterButton"))
        )
        print("Login button found")
        # login_button = cls.__driver.find_element(By.ID, "enterButton")
        login_button.click()
        
        cls.__wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".topbar-items.fadeInDown.animated")))
        print("Login successful")
    
    @classmethod
    def get_total_pages(cls) -> dict:
        try:
            print("Navigating to the positions page")
            endpoint = '/position.xhtml'
            cls.__driver.get(cls.__url + endpoint)
            
            print("Waiting for the dropdown to load")
            # Wait for the dropdown to load
            cls.__wait.until(EC.presence_of_element_located((By.ID, "selectionForm:selectionType_label")))
            
            print("Waiting for a short time to ensure the page loaded completely")
            # Wait for a short time to ensure the page loaded completely
            cls.__driver.implicitly_wait(2000)
            
            try:
                print("Clicking to select 'All Trackers'")
                # Click to select "All Trackers"
                cls.__driver.find_element(By.ID, "selectionForm:selectionType_label").click()
                cls.__driver.implicitly_wait(1000)
                cls.__driver.find_element(By.ID, "selectionForm:selectionType_0").click()
                
                print("Waiting for the table to update")
                # Wait for the table to update
                cls.__wait.until(EC.presence_of_element_located((By.ID, "tablePositionsForm:tablePositions_data")))
                
                # Wait for the table to load
                cls.__wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, r"#tablePositionsForm\:tablePositions_data tr[role='row']")))
                print("Table loaded")

                # Try to get the total number of plates
                total_element = cls.__driver.find_element(By.ID, "tablePositionsForm:tablePositions:tableTotal")
                
                if total_element:
                    total_plates = total_element.text
                    print(f"Total of plates found: {total_plates}")
                else:
                    print("Total element not found")
                    raise Exception("Total element not found")
                
                print("Searching for the number of plates per page")
                # Get the number of plates per page
                select_element = cls.__driver.find_element(By.NAME, "tablePositionsForm:tablePositions_rppDD")
                if select_element:
                    html_select = select_element.get_attribute("innerHTML")

                    selected_value = re.search(r'value="(\d+)" selected="selected"', html_select)
                    if selected_value:
                        plates_per_page = selected_value.group(1)
                        print(f"Plates per page: {plates_per_page}")
                
            except Exception as e:
                print(f"Error getting the number of trackers: {str(e)}")
                raise e
                
            return {"total_pages": math.ceil(int(total_plates) / int(plates_per_page))}
            
        except Exception as e:
            print(f"Error getting the number of trackers: {str(e)}")
            raise e
    
    @classmethod
    def __read_rows(cls, page_number: int) -> pd.DataFrame:
        try:
            print(f"Waiting for page {page_number + 1} to be active in the lower paginator")
            
            # Wait until the correct page is active in the lower paginator
            seletor = rf"#tablePositionsForm\:tablePositions_paginator_bottom .ui-paginator-pages a[aria-label='Page {page_number + 1}'].ui-state-active"
            cls.__wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor)))
            print(f"Page {page_number + 1} is active")
            
            # Wait until the table is loaded
            cls.__wait.until(EC.presence_of_element_located((By.ID, "tablePositionsForm:tablePositions:exportCsv")))
            cls.__wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, r"#tablePositionsForm\:tablePositions_data tr[role='row']")))
            print("Table loaded")
            
            # List to store the data
            data = []
            lines = cls.__driver.find_elements(By.CSS_SELECTOR, "#tablePositionsForm\\:tablePositions_data tr[role='row']")
            print(f"Found {len(lines)} valid lines")
            
            print("Reading the lines of the table")
            for line in lines:
                try:
                    elements = {
                        'tracker': line.find_element(By.CSS_SELECTOR, "td:nth-child(1)"),
                        'datetime': line.find_element(By.CSS_SELECTOR, "td:nth-child(2)"),
                        'address': line.find_element(By.CSS_SELECTOR, "td:nth-child(3)"),
                        'speed': line.find_element(By.CSS_SELECTOR, "td:nth-child(4)"),
                        'ignition': line.find_element(By.CSS_SELECTOR, "td:nth-child(5) img"),
                        'battery': line.find_element(By.CSS_SELECTOR, "td:nth-child(6)"),
                        'temperature': line.find_element(By.CSS_SELECTOR, "td:nth-child(7)"),
                        'humidity': line.find_element(By.CSS_SELECTOR, "td:nth-child(8)"),
                        'signal': line.find_element(By.CSS_SELECTOR, "td:nth-child(9) img"),
                        'gps': line.find_element(By.CSS_SELECTOR, "td:nth-child(10) img")
                    }
                    # Identify missing elements
                    missing_elements = [k for k, v in elements.items() if v is None]
                    
                    if missing_elements:
                        tracker_text = elements['tracker'].text if elements['tracker'] else "Tracker not found"
                        print(f"Missing elements for {tracker_text}: {', '.join(missing_elements)}")
                        continue
                    
                    # Auxiliary function to get the text content of a node
                    def text_content(node):
                        # Get the text without inner span elements
                        text = node.text
                        spans = node.find_elements(By.TAG_NAME, "span")
                        for span in spans:
                            text = text.replace(span.text, "")
                        return text.strip()
                    
                    data.append({
                        'tracker': text_content(elements['tracker']),
                        'datetime': text_content(elements['datetime']),
                        'address': text_content(elements['address']),
                        'speed': text_content(elements['speed']),
                        'ignition': elements['ignition'].get_attribute("title"),
                        'battery': text_content(elements['battery']),
                        'temperature': text_content(elements['temperature']),
                        'humidity': text_content(elements['humidity']),
                        'signal': elements['signal'].get_attribute("alt"),
                        'gps': elements['gps'].get_attribute("alt")
                    })
                        
                except Exception as e:
                    print(f"Error processing line: {str(e)}")
                    continue
            
            print("Creating the DataFrame")
            if data:
                # Create DataFrame
                df = pd.DataFrame(data)
                print("DataFrame created successfully!")
                return df
            else:
                print("No data was collected")
                return None
            
        except Exception as e:
            print(f"Error creating DataFrame: {str(e)}")
            raise e
    
    @classmethod
    def __transform_tracker(cls, text):
        if pd.isna(text):
            return pd.NA, pd.NA

        # Look for the pattern: text (code) or only code
        pattern = r'^(?:([^(]+)\s*)?(?:\(([^)]+)\))?$'
        match = re.match(pattern, text)
        
        if match:
            driver, truck_cab = match.groups()
            driver = driver.strip() if driver else pd.NA
            truck_cab = truck_cab if truck_cab else text
            return driver, truck_cab
        
        return pd.NA, text

        # Apply the function and create new columns
        # df[['driver', 'truck_cab']] = pd.DataFrame(df['tracker'].apply(split_tracker).tolist())

        return df
    
    @classmethod
    def get_locations(cls, total_pages: int) -> pd.DataFrame:
        dfs_pages = []
        
        print("Starting to read the pages")
        print(f"Total of pages: {total_pages}")
        for page in range(0, total_pages):
            print(f"Reading page {page + 1} of {total_pages}")
            
            # Read the lines of the page
            df_page = cls.__read_rows(page)
            
            if df_page is not None:
                dfs_pages.append(df_page)
            
            # Check if there is a next page
            next_button = cls.__driver.find_element(By.CSS_SELECTOR, r"#tablePositionsForm\:tablePositions_paginator_bottom a[aria-label='Next Page']")
            if next_button:
                # Check if the button is disabled
                button_class = next_button.get_attribute("class")
                if "ui-state-disabled" in button_class:
                    print("Next page button is disabled")
                    break
                # Click on the next page button
                next_button.click()
                print("Clicked on the next page button")
                
                # Wait for the table to update
                cls.__wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, r"#tablePositionsForm\:tablePositions_data tr[role='row']")))
            else:
                print("Next page button not found")
                break
                        
        # Concatenate all DataFrames
        if dfs_pages:
            df_final = pd.concat(dfs_pages, ignore_index=True)
            print("Data from all pages concatenated successfully!")
            
            try:
                df_final[['driver', 'truck_cab']] = pd.DataFrame(df_final['tracker'].apply(cls.__transform_tracker).tolist())
                # df_final.to_csv('df_final.csv', index=False)
            except Exception as e:
                print(f"Error transforming tracker: {str(e)}")
                raise e
            
            return df_final
        else:
            print("No data was collected")
            return None  
    
    @classmethod
    def close_browser(cls):
        if cls.__driver:
            cls.__driver.quit()
        if cls.__display:
            cls.__display.stop()
        print("Browser and display closed successfully")
