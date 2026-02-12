import os

class DefaultConfig:
    """ Configuration for the bot. """
    PORT = 3978
    
    # Azure Bot Settings
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    # Azure AI Search Settings
    AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
    AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY", "")
    AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "")

    # Azure OpenAI (APIM) Settings
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "") # Your APIM URL
    AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")           # APIM Subscription Key
    AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    # Arize Phoenix Settings
    ARIZE_COLLECTOR_ENDPOINT = os.environ.get("ARIZE_COLLECTOR_ENDPOINT", "https://otlp.arize.com/v1/traces")
    ARIZE_SPACE_ID = os.environ.get("ARIZE_SPACE_ID", "")
    ARIZE_API_KEY = os.environ.get("ARIZE_API_KEY", "")
