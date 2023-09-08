from argparse import ArgumentParser
from enum import IntEnum
from typing import Any, Dict
from functools import partial

from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
import toml

from data_store import IDataStore, InMemoryDataStore, RedisDataStore
from email_handler import EmailHandler
from fetcher import Fetcher
from utils import is_url

class State(IntEnum):
    GET_EMAIL = 0
    GET_INPUT = 1

class Fetchbot:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.data_store: IDataStore = None

        redis_config = config.get('Redis')

        if redis_config is not None:
            self.data_store = RedisDataStore(redis_config)
        else:
            self.data_store = InMemoryDataStore()

        self.fetcher = Fetcher(config['Fetcher'])
        self.email_handler = EmailHandler(config['EmailHandler'])
        self.email_handler.load_password()
        self.token = config['Telegram']['api_token']

    def run(self) -> None:
        """Run the bot."""
        # Create the Application and pass it your bot's token.
        application = Application.builder().token(self.token).build()

        # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                State.GET_EMAIL: [
                    MessageHandler(
                        filters.TEXT,
                        self.save_email
                    )
                ],
                State.GET_INPUT: [
                    MessageHandler(
                        filters.TEXT,
                        partial(self.handle_input, True)
                    )
                ],
            },
            fallbacks=[MessageHandler(filters.Regex("^Done$"), None)],
        )

        application.add_handler(conv_handler)

        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_email = self.data_store.get(update.message.from_user.id)

        if user_email is None:
            await update.message.reply_text('Please input your email:')
            return State.GET_EMAIL
        else:
            await update.message.reply_text('Send me a url or a text')
            return State.GET_INPUT

    async def done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return ConversationHandler.END

    async def handle_input(self, send_email: bool, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = update.message.text
        user_email = self.data_store.get(update.message.from_user.id)

        if send_email:
            if user_email is None:
                return State.GET_EMAIL

            if is_url(message):
                file_path = self.fetcher.fetch_and_convert(message)
            else:
                file_path = self.fetcher.convert_text('from_tg', message)

            self.email_handler.send_email(user_email, 'From Fetchbot', '', [file_path])
            self.fetcher.delete_cached_files()

        return ConversationHandler.END

    async def save_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = update.message.text
        user = update.message.from_user

        self.data_store.set(user.id, message)

        update.message.reply_text('Email saved')

        return State.GET_INPUT

if __name__ == '__main__':
    parser = ArgumentParser()

    with open('config.toml', 'r') as config_file:
        config_dict = toml.load(config_file)

    fetchbot = Fetchbot(config_dict)
    fetchbot.run()
