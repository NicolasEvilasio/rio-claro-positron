import redis
from pipeline.models.positron import Positron
from pipeline.models.excel import Excel
from prefect import flow, task
import pandas as pd
import sys
import os
from memory_profiler import profile

@task(retries=3)
@profile
def get_positron_locations_data(username: str, password: str) -> pd.DataFrame:
    # print(f"Memória antes de get_positron_locations_data: {get_memory_usage()}")
    Positron.start(username, password)
    total_pages = Positron.get_total_pages().get('total_pages')
    df = Positron.get_locations(total_pages)
    # print(f"Memória depois de get_positron_locations_data: {get_memory_usage()}")
    return df

@task
@profile
@profile
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
    # print(f"Memória antes de update_excel_data: {get_memory_usage()}")
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
    # print(f"Memória depois de update_excel_data: {get_memory_usage()}")
    
@task
@profile
@profile
def get_on_redis(
    host: str,
    port: int,
    username: str,
    password: str,
    name: str,
    decode_responses: bool = True
) -> str:
    # print(f"Memória antes de get_on_redis: {get_memory_usage()}")
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