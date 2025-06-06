from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from google.cloud import bigquery

# Your existing FastAPI application
app = FastAPI()

# define your BigQuery client
client = bigquery.Client.from_service_account_json(
    "/app/secrets/bq-sample-project-456713-ef11d647744f.json",
    project="bq-sample-project-456713"
)

# Define your endpoints as you normally would
@app.get("/get_data_from_bigquery/{query}", operation_id="get_data_from_bigquery")
async def get_data_from_bigquery(query: str):
    # Comfirm the query is safe to execute
    if "DROP" in query or "DELETE" in query or "UPDATE" in query:
        return {"error": "Unsafe query detected. Query execution aborted."}
    # Execute the query
    query_job = client.query(query)
    # Wait for the job to complete
    results = query_job.result()
    # Process the results
    print(f"Query results: {results}")
    return {"query_results": [dict(row) for row in results]}

@app.get("/get_project_list_from_bigquery", operation_id="get_project_list_from_bigquery")
async def get_project_list_from_bigquery():
    # Get the list of projects
    projects = client.list_projects()
    # Process the projects
    project_list = [project.project_id for project in projects]
    return {"projects": project_list}

@app.get("/get_dataset_list_from_bigquery/{project_id}", operation_id="get_dataset_list_from_bigquery")
async def get_dataset_list_from_bigquery(project_id: str):
    # Get the list of datasets for the given project
    datasets = client.list_datasets(project=project_id)
    # Process the datasets
    dataset_list = [dataset.dataset_id for dataset in datasets]
    return {"datasets": dataset_list}

@app.get("/get_table_list_from_bigquery/{project_id}/{dataset_id}", operation_id="get_table_list_from_bigquery")
async def get_table_list_from_bigquery(project_id: str, dataset_id: str):
    # Get the list of tables for the given project and dataset
    dataset_id = f"{project_id}.{dataset_id}"
    tables = client.list_tables(dataset_id)
    # Process the tables
    table_list = [table.table_id for table in tables]
    return {"tables": table_list}

@app.get("/get_table_schema_from_bigquery/{project_id}/{dataset_id}/{table_id}", operation_id="get_table_schema_from_bigquery")
async def get_table_schema_from_bigquery(project_id: str, dataset_id: str, table_id: str):
    # Get the schema for the given project, dataset, and table
    table_ref = client.dataset(dataset_id, project=project_id).table(table_id)
    table = client.get_table(table_ref)
    # Process the schema with datatypes
    schema = {field.name: field.field_type for field in table.schema}
    return {"schema": schema}

@app.get("/create_logistic_reg_model_by_bigquery_ml/{model_name}/{project_id}/{dataset_id}/{train_table_id}/{target_variable}", operation_id="create_logistic_reg_model_by_bigquery_ml")
async def create_logistic_reg_model_by_bigquery_ml(model_name: str, project_id: str, dataset_id: str, train_table_id: str, target_variable: str):
    
    # Execute the query
    query = f"""
        CREATE OR REPLACE MODEL `{project_id}.{dataset_id}.{model_name}`
        OPTIONS(
          model_type='logistic_reg'
        ) AS
        SELECT
          {target_variable} as label,
          * except({target_variable})
        FROM
          `{project_id}.{dataset_id}.{train_table_id}`
    """
    
    query_job = client.query(query)
    # Wait for the job to complete
    query_job.result()
    
    return {"model_name": model_name, "status": "Model created successfully"}

@app.get("/predict_by_bigquery_ml/{model_name}/{project_id}/{dataset_id}/{test_table_id}/{id}/{limit}", operation_id="predict_by_bigquery_ml")
async def predict_by_bigquery_ml(model_name: str, project_id: str, dataset_id: str, test_table_id: str, id: str, limit: int):

    # Execute the query
    query = f"""
        SELECT
            {id} as id,
            predicted_label
        FROM
            ML.PREDICT(MODEL `{project_id}.{dataset_id}.{model_name}`, (
            SELECT
                *
            FROM
                `{project_id}.{dataset_id}.{test_table_id}`
            ))
        ORDER BY
            id
        LIMIT {limit}
    """
    
    query_job = client.query(query)
    # Wait for the job to complete
    results = query_job.result()
    
    return {"predictions": [dict(row) for row in results]}

# Add the MCP server to your FastAPI app
mcp = FastApiMCP(
    app,  
    name="My API MCP",  # Name for your MCP server
    description="MCP server for my API",  # Description
    base_url="http://localhost:8000",  # Where your API is running
    describe_all_responses=True,  # Describe all responses
    describe_full_response_schema=True  # Describe full response schema
)

# Mount the MCP server to your FastAPI app
mcp.mount()
