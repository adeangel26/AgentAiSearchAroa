import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType, MessageRole, ListSortOrder
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the endpoint from environment variables
project_endpoint = os.getenv("PROJECT_ENDPOINT")

# Initialize the AIProjectClient
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)


# Obtener el ID de la conexión CognitiveSearch
conn_list = project_client.connections.list()
conn_id = ""
for conn in conn_list:
    if conn.type == "CognitiveSearch":
        conn_id = conn.id
        break
print(f"CognitiveSearch conn_id: {conn_id}")

index_name = os.getenv("AZURE_AI_SEARCH_INDEX")

if not conn_id or not index_name:
    print("ERROR: No se encontró una conexión CognitiveSearch o falta AZURE_AI_SEARCH_INDEX.")
    exit(1)

ai_search = AzureAISearchTool(
    index_connection_id=conn_id,
    index_name=index_name,
    query_type=AzureAISearchQueryType.SIMPLE,
    top_k=3,
    filter=""
)


# Define the model deployment name
model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

# Create an agent with the Azure AI Search tool
agent = project_client.agents.create_agent(
    model=model_deployment_name,
    name="Agente Buscador de Aroa",
    instructions="Eres un agente que puede buscar información en Azure AI Search.",
    tools=ai_search.definitions,
    tool_resources=ai_search.resources,
)
print(f"Created agent, ID: {agent.id}")

# Create a thread for communication
thread = project_client.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

# Send a message to the thread
message = project_client.agents.messages.create(
    thread_id=thread.id,
    role=MessageRole.USER,
    content="Cuáles son las 5 regiones más habituales del mundo del Surf?",
)
print(f"Created message, ID: {message['id']}")

# Create and process a run with the specified thread and agent
run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
print(f"Run finished with status: {run.status}")

# Check if the run failed
if run.status == "failed":
    print(f"Run failed: {run.last_error}")

# Fetch and log all messages in the thread
messages = project_client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
for message in messages:
    print(f"Role: {message.role}, Content: {message.content}")

# Delete the agent
project_client.agents.delete_agent(agent.id)
print("Deleted agent")