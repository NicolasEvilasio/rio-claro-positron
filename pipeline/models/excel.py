import requests
import pandas as pd
from urllib.parse import quote


class Excel:
    __client_id = None
    # __client_secret = None
    # __tenant_id = None
    __scope = None
    __redirect_uri = None
    __authorization_code = None
    __token = None
    __file_id = None
    __worksheet_name = None
    __url_base = 'https://login.microsoftonline.com/common/oauth2/v2.0'
    
    @classmethod
    def start_session(
        cls, 
        client_id: str, 
        # client_secret: str, 
        # tenant_id: str, 
        scopes: list, 
        redirect_uri: str, 
        token: str = None, 
        auth_code: str = None, 
        file_id: str = None,
        worksheet_name: str = None
    ):
        cls.__client_id = client_id
        # cls.__client_secret = client_secret
        # cls.__tenant_id = tenant_id
        cls.__redirect_uri = redirect_uri
        cls.__file_id = file_id
        cls.__worksheet_name = worksheet_name
        cls.__set_scope(scopes)
        
        if token:
            cls.__token = token
        elif auth_code:
            cls.__authenticate(auth_code)


    @classmethod
    def __set_scope(cls, scopes: list):
        cls.__scope = ' '.join(scopes)
        
    @classmethod
    def get_scope(cls):
        return cls.__scope
    
    @classmethod
    def get_authorization_url(cls):
        endpoint = '/authorize'
        params = {
            'client_id': cls.__client_id,
            'response_type': 'code',
            'redirect_uri': cls.__redirect_uri,
            'scope': cls.__scope
        }
        url = f'{cls.__url_base}{endpoint}'
        return url
    
    @classmethod
    def set_authorization_code(cls, authorization_code: str):
        cls.__authorization_code = authorization_code

    @classmethod
    def __authenticate(cls, auth_code: str):
        endpoint = '/token'
        token_url = cls.__url_base + endpoint

        params = {
            'client_id': cls.__client_id,
            'code': auth_code,
            'redirect_uri': cls.__redirect_uri,
            'grant_type': 'authorization_code'
        }

        try:
            response = requests.post(token_url, params=params)
            response.raise_for_status()
            token = response.json()
            cls.__token = token
            print('Token generated successfully')
            
        except Exception as e:
            print(f'Error getting token: \n')
            raise e

    @classmethod
    def __refresh_token(cls):
        endpoint = '/token'
        token_url = cls.__url_base + endpoint
        
        params = {
            'client_id': cls.__client_id,
            'grant_type': 'refresh_token',
            'refresh_token': cls.__token['refresh_token'],
            'scope': cls.__scope,
        }

        try:
            response = requests.post(token_url, data=params)
            response.raise_for_status()
            token = response.json()
            cls.__token = token
            print('Token renewed successfully')
        except Exception as e:
            print(f'Error renewing token: \n')
            raise e

    @classmethod
    def update_sheet(cls, data: pd.DataFrame):
        headers = {
            'Authorization': f'Bearer {cls.__token["access_token"]}',
            'Content-Type': 'application/json'
        }

        url_get = f'https://graph.microsoft.com/v1.0/me/drive/items/{cls.__file_id}/workbook/worksheets/{cls.__worksheet_name}/usedRange'

        # Get data from sheet
        response_get = requests.get(url_get, headers=headers)
        if response_get.status_code == 200:
            sheet_data = response_get.json()
            values = sheet_data.get('values', [])

            for index, row in data.iterrows():
                truck_cab = row['truck_cab']
                address = row['address']
                address_timestamp = row['datetime']

                # Search for the row where column "E" matches the "truck_cab" value
                row_index = None
                for i, sheet_row in enumerate(values):
                    if len(sheet_row) > 4 and sheet_row[4] == truck_cab:  # Column "E"
                        row_index = i + 1  # Add 1 for Excel index
                        break

                if row_index:
                    # Update cell in columns "O:P" for the found row
                    range_address = f'O{row_index}:P{row_index}'
                    url_update = f'https://graph.microsoft.com/v1.0/me/drive/items/{cls.__file_id}/workbook/worksheets/{cls.__worksheet_name}/range(address=\'{range_address}\')'

                    # Update data
                    update_data = {
                        'values': [[address, address_timestamp]]
                    }

                    # Make request to update cell
                    response_update = requests.patch(url_update, json=update_data, headers=headers)
                    if not response_update.status_code == 200:
                        print(f'Error updating cell: {response_update.status_code}, {response_update.text}')
                else:
                    print(f"Value '{truck_cab}' not found in column E.")
        else:
            raise Exception(f'Error getting sheet data: {response_get.status_code}, {response_get.text}')
                        
        print('Sheet updated successfully')
        