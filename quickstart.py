import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool, AzureAISearchTool
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env automáticamente
load_dotenv()

# Get PROJECT_ENDPOINT from environment or show error if not set
project_endpoint = os.environ.get("PROJECT_ENDPOINT")
if not project_endpoint:
    raise EnvironmentError("La variable de entorno PROJECT_ENDPOINT no está definida. Por favor, defínela antes de ejecutar el script.")

# Create an Azure AI Client from an endpoint, copied from your Azure AI Foundry project.
# You need to login to Azure subscription via Azure CLI and set the environment variables

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
)

# Crear la herramienta de Azure AI Search usando la variable de entorno y el nombre del índice
azure_ai_search_connection = os.environ.get("AZURE_AI_SEARCH_CONNECTION")
if not azure_ai_search_connection:
    raise EnvironmentError("La variable de entorno AZURE_AI_SEARCH_CONNECTION no está definida en tu .env. Por favor, agrégala.")

azure_ai_search_index = os.environ.get("AZURE_AI_SEARCH_INDEX")
if not azure_ai_search_index:
    raise EnvironmentError("La variable de entorno AZURE_AI_SEARCH_INDEX no está definida en tu .env. Por favor, agrégala con el nombre del índice de Azure AI Search.")

azure_ai_search_tool = AzureAISearchTool(azure_ai_search_connection, azure_ai_search_index)
    


code_interpreter = CodeInterpreterTool()
with project_client:
    # Crear el agente con la herramienta de Azure AI Search y el Code Interpreter
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],  # Model deployment name
        name="Agente de Aroa",  # Name of the agent
        instructions="You are a helpful agent",  # Instructions for the agent
        tools=[azure_ai_search_tool.definitions, code_interpreter.definitions],  # Attach the tools
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")
    
    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",  # Role of the message sender
        content="What is the weather in Seattle today?",  # Message content
    )
    print(f"Created message, ID: {message['id']}")
    
    # Create and process an agent run
    run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")
    
    # Check if the run failed
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    
    # Fetch and log all messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message.role}, Content: {message.content}")
    
    # Delete the agent when done
    # project_client.agents.delete_agent(agent.id)
    # print("Deleted agent")