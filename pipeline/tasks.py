import redis
from pipeline.models.selenium_positron import Positron
from pipeline.models.excel import Excel
from prefect import task
import pandas as pd

@task(retries=3)
def get_positron_locations_data(username: str, password: str, headless: bool = True) -> pd.DataFrame:
    Positron.set_headless(headless)
    Positron.start(username, password)
    total_pages = Positron.get_total_pages().get('total_pages')
    df = Positron.get_locations(total_pages)
    Positron.close_browser()
    return df

@task
def update_excel_data(
        new_data: pd.DataFrame,
        client_id: str, 
        scopes: list, 
        redirect_uri: str, 
        token: dict, 
        file_id: str, 
        worksheet_name: str,
        authorization_code: str = None
) -> None:     
    if authorization_code:
        Excel.set_authorization_code(authorization_code=authorization_code)

    Excel.start_session(client_id=client_id, 
                        scopes=scopes, 
                        redirect_uri=redirect_uri,
                        token = token,
                        file_id=file_id,
                        worksheet_name=worksheet_name
        )
    
    Excel._Excel__refresh_token()
    Excel.update_sheet(data=new_data)
    
@task
def get_on_redis(
    host: str,
    port: int,
    username: str,
    password: str,
    name: str,
    decode_responses: bool = True
) -> str:
    r = redis.Redis(
        host=host,
        port=port,
        decode_responses=decode_responses,
        username=username,
        password=password,
    )
    result = r.hgetall(name=name)
    return result

# @task
def set_on_redis(
    host: str,
    port: int,
    username: str,
    password: str,
    name: str,
    value: str = None,
    mapping: dict = {}
) -> None:
    r = redis.Redis(
        host=host,
        port=port,
        username=username,
        password=password,
    )
    if value:
        r.hset(name=name, mapping=value)
    else:
        r.hset(name=name, mapping=mapping)