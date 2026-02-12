import sys
import traceback
from datetime import datetime
from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapterSettings, 
    TurnContext, 
    BotFrameworkAdapter,
    MemoryStorage, 
    ConversationState
)
from botbuilder.schema import Activity, ActivityTypes

from config import DefaultConfig
from bot import MyRagBot

CONFIG = DefaultConfig()

# Create Adapter
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Create Memory (Volatile / Short Term)
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)

# Create Bot
BOT = MyRagBot(CONFIG, CONVERSATION_STATE)

async def messages(req: web.Request) -> web.Response:
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return web.Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        return web.Response(status=201)
    except Exception as exception:
        print(f"Error: {exception}")
        traceback.print_exc()
        return web.Response(status=500)

app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(app, host="0.0.0.0", port=CONFIG.PORT)
    except Exception as error:
        raise error
