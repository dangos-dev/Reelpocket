import os
from contextlib import asynccontextmanager
from http import HTTPStatus
from optparse import OptionParser

import ngrok
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from social.instagram_services import Instagram
from social.telegram_services import DangoBot

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_DOMAIN: str = os.getenv("RAILWAY_PUBLIC_DOMAIN")
INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD")

# fileConfig("program_logs.ini")
# logger = logging.getLogger(__name__)

bot = DangoBot(TELEGRAM_BOT_TOKEN)
bot.create(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Sets the webhook for the Telegram Bot and manages its lifecycle (start/stop)."""
    await bot.builder.bot.setWebhook(WEBHOOK_DOMAIN)
    async with bot.builder:
        await bot.builder.start()
        yield
        await bot.builder.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/")
async def process_update(request: Request):
    """Handles incoming Telegram updates and processes them with the bot."""
    data = await request.json()
    update = Update.de_json(data, bot.builder.bot)
    await bot.builder.process_update(update)
    return Response(status_code=HTTPStatus.OK)


# Commands
bot.builder.add_handler(CommandHandler(command="start", callback=bot.handle_start))
bot.builder.add_handler(CommandHandler(command="dango", callback=bot.handle_aboutme))

# Instagram Reel URL input
bot.builder.add_handler(
    MessageHandler(
        filters=filters.Regex(r"^https://(?:www.)?instagram.com/reel/.*"),
        callback=bot.send_instagram_reel,
    )
)

# Instagram Post/Post URL input
bot.builder.add_handler(
    MessageHandler(
        filters=filters.Regex(r"^https://(?:www.)?instagram.com/p/.*"),
        callback=bot.send_instagram_photo,
    )
)

# Report error
bot.builder.add_handler(
    CallbackQueryHandler(pattern=r"^report_url$", callback=bot.handle_report_error)
)

if __name__ == "__main__":
    # For local testing

    parser = OptionParser()
    parser.add_option("--ngrok-token", dest="ngrok_token")
    parser.add_option("--ngrok-url", dest="ngrok_url")
    parser.add_option("--ngrok-port", dest="ngrok_port")

    (options, _) = parser.parse_args()

    # Ngrok
    ngrok.set_auth_token(options.ngrok_token)

    ngrok_tunnel = ngrok.connect(
        addr=int(options.ngrok_port),
        domain=options.ngrok_url
    )

    # Uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=int(options.ngrok_port)
    )
