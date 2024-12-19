from prefect import flow, variables
from pipeline.tasks import (
    get_positron_locations_data, 
    update_excel_data, 
    get_on_redis
)
from prefect.blocks.system import Secret


@flow(
  log_prints=True
)
def update_excel_locations_data():
        
    redis_secrets = get_on_redis(
        host=str(Secret.load('redis-host').get()),
        port=int(Secret.load('redis-port').get()),
        username=str(Secret.load('redis-username').get()),
        password=str(Secret.load('redis-password').get()),
        name='microsoft_personal_token'
    )
    
    new_data = get_positron_locations_data(
        username=str(Secret.load('positron-username').get()),
        password=str(Secret.load('positron-password').get()),
        headless=True
    )
    
    excel_data = update_excel_data(
        new_data=new_data, 
        client_id=str(Secret.load('microsoft-client-id').get()), 
        scopes=variables.Variable.get('positron').get('scopes'), 
        redirect_uri=str(Secret.load('microsoft-redirect-uri').get()), 
        token=redis_secrets,
        file_id=str(Secret.load('microsoft-excel-file-id').get()), 
        worksheet_name=str(Secret.load('microsoft-excel-worksheet-name').get())
    )


if __name__ == "__main__":
    update_excel_locations_data()


