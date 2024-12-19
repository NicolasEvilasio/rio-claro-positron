import math
from playwright.sync_api import sync_playwright
import pandas as pd
import re


class Positron:
    __username = None
    __password = None
    __page = None
    __url = "https://www.positronrt.com.br/rastreador5"
    headless = True
    
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
        print("Configurando o playwright para abrir o browser")
        p = sync_playwright().start()
        
        print("Iniciando o browser")
        browser = p.chromium.launch(
            headless=True,
            chromium_sandbox=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-zygote',
                '--disable-gpu',
                '--deterministic-fetch',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-software-rasterizer',
                '--disable-features=site-per-process',
            ]
        )
        print("Browser iniciado com sucesso")
        
        try:
            print("Criando uma nova página")
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            cls.__page = context.new_page()
            print("Página criada com sucesso")
        except Exception as e:
            print(f"Error creating page: {str(e)}")
            raise e

    @classmethod
    def __authenticate(cls):
        try:
            print("Navegando para a página de login")
            endpoint = '/login.xhtml'
            cls.__page.goto(cls.__url + endpoint, wait_until='domcontentloaded')
            
            print("Esperando o carregamento dos campos de usuário e senha")
            # Wait until the username and password fields are loaded
            cls.__page.wait_for_selector("#j_username", timeout=5000)
            cls.__page.wait_for_selector("#password", timeout=5000)
            
            print("Preenchendo o campo de usuário")
            # Fill in the username field
            cls.__page.fill("#j_username", cls.__username)
            cls.__page.dispatch_event("#j_username", "input")
            
            print("Preenchendo o campo de senha")
            # Fill in the password field
            cls.__page.fill("#password", cls.__password)
            cls.__page.dispatch_event("#password", "input")
            
            print("Alterando a classe do botão e removendo o atributo 'disabled'")
            # Change the button class and remove the 'disabled' attribute
            cls.__page.evaluate("""
                var button = document.querySelector('#enterButton');
                button.className = 'ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only';
                button.removeAttribute('disabled');
                button.setAttribute('aria-disabled', 'false');
            """)
            
            print("Clicando no botão de login")
            # Click the enter button
            cls.__page.click("#enterButton")
            
            print("Esperando o carregamento de um elemento específico após o login")
            # Wait until a specific element appears after login
            cls.__page.wait_for_selector(".topbar-items.fadeInDown.animated", timeout=10000)
            print("Login realizado com sucesso")
            
        except Exception as e:
            raise e
            
    @classmethod
    def get_total_pages(cls) -> dict:
        try:
            print("Navegando para a página de posições")
            endpoint = '/position.xhtml'
            cls.__page.goto(cls.__url + endpoint, wait_until='domcontentloaded')
            
            print("Esperando o carregamento do dropdown")
            # Wait for the dropdown to load
            cls.__page.wait_for_selector(r"#selectionForm\:selectionType_label", timeout=30000)
            
            print("Esperando um curto período para garantir que a página carregou completamente")
            # Wait for a short time to ensure the page loaded completely
            cls.__page.wait_for_timeout(2000)
            
            try:
                print("Clicando para selecionar 'All Trackers'")
                # Click to select "All Trackers"
                cls.__page.click(r"#selectionForm\:selectionType_label")
                cls.__page.wait_for_timeout(1000)  # Wait for the dropdown to open
                cls.__page.click(r"#selectionForm\:selectionType_0")
                
                print("Esperando o carregamento da tabela")
                # Wait for the table to update
                cls.__page.wait_for_selector(r"#tablePositionsForm\:tablePositions_data", timeout=30000)
                cls.__page.wait_for_load_state('domcontentloaded')
                
                # Wait for the table to load
                cls.__page.wait_for_selector(r"#tablePositionsForm\:tablePositions_data tr[role='row']", timeout=10000)
                print("Table loaded")

                # Try to get the total number of plates
                total_element = cls.__page.wait_for_selector(r"#tablePositionsForm\:tablePositions\:tableTotal", timeout=30000)
                
                if total_element:
                    total_plates = total_element.text_content()
                    print(f"Total of plates found: {total_plates}")
                else:
                    print("Total element not found")
                    raise Exception("Total element not found")
                
                print("Buscando o número de placas por página")
                # Get the number of plates per page
                select_element = cls.__page.query_selector('[name="tablePositionsForm:tablePositions_rppDD"]')
                if select_element:
                    html_select = select_element.inner_html()
                    import re
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
            print(f"Esperando a página {page_number + 1} ser ativa no paginador inferior")
            # Wait until the correct page is active in the lower paginator
            seletor = rf"#tablePositionsForm\:tablePositions_paginator_bottom .ui-paginator-pages a[aria-label='Page {page_number + 1}'].ui-state-active"
            cls.__page.wait_for_selector(
                seletor,
                timeout=10000
            )
            print(f"Page {page_number + 1} is active")
            
            # Wait until the table is loaded
            cls.__page.wait_for_selector(r"#tablePositionsForm\:tablePositions\:exportCsv", timeout=10000)
            cls.__page.wait_for_selector(r"#tablePositionsForm\:tablePositions_data tr[role='row']", timeout=10000)
            print("Table loaded")
            
            # List to store the data
            data = []
            lines = cls.__page.query_selector_all(r"#tablePositionsForm\:tablePositions_data tr[role='row']")
            print(f"Found {len(lines)} valid lines")
            
            print("Lendo as linhas da tabela")
            for line in lines:
                try:
                    elements = {
                        'tracker': line.query_selector("td:nth-child(1)"),
                        'datetime': line.query_selector("td:nth-child(2)"),
                        'address': line.query_selector("td:nth-child(3)"),
                        'speed': line.query_selector("td:nth-child(4)"),
                        'ignition': line.query_selector("td:nth-child(5) img"),
                        'battery': line.query_selector("td:nth-child(6)"),
                        'temperature': line.query_selector("td:nth-child(7)"),
                        'humidity': line.query_selector("td:nth-child(8)"),
                        'signal': line.query_selector("td:nth-child(9) img"),
                        'gps': line.query_selector("td:nth-child(10) img")
                    }
                    
                    # Identify missing elements
                    missing_elements = [k for k, v in elements.items() if v is None]
                    
                    if missing_elements:
                        tracker_text = elements['tracker'].inner_text() if elements['tracker'] else "Tracker not found"
                        print(f"Missing elements for {tracker_text}: {', '.join(missing_elements)}")
                        continue
                    
                    # Auxiliary function to get the text content of a node
                    text_content = lambda node: node.evaluate("""
                        (node) => {
                            const clone = node.cloneNode(true); 
                            clone.querySelector('span')?.remove(); 
                            return clone.textContent.trim();
                        }
                    """)
                    
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
            
            print("Criando o DataFrame")
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
    def __transform_tracker(cls, text) -> tuple:
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

    @classmethod
    def get_locations(cls, total_pages) -> pd.DataFrame:
        dfs_pages = []
        
        print("Iniciando a leitura das páginas")
        print(f"Total of pages: {total_pages}")
        for page in range(0, total_pages):
            print(f"Reading page {page + 1} of {total_pages}")
            
            # Read the lines of the page
            df_page = cls.__read_rows(page)
            
            if df_page is not None:
                dfs_pages.append(df_page)
            
            # Check if there is a next page
            next_button = cls.__page.query_selector(r"#tablePositionsForm\:tablePositions_paginator_bottom a[aria-label='Next Page']")
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
                cls.__page.wait_for_selector(r"#tablePositionsForm\:tablePositions_data tr[role='row']", timeout=10000)
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
    