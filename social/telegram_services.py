import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, ContextTypes
from telegram.ext._applicationbuilder import InitApplicationBuilder

from social.instagram_services import Instagram


class DangoBot:
    def __init__(self):
        self.builder: InitApplicationBuilder
        self._current_chat_id: int = None
        self._current_message_id: int = None
        self._current_reel_id: str = None

    def create(self, bot_token: str) -> None:
        """
        Creates and initializes an application with the provided bot token.

        This method builds an application instance using the provided bot token
        and assigns it to the `self.builder` attribute. This application instance
        is configured with no updater.

        Parameters:
            bot_token: A string representing the bot token used for authorization. It is
                required to configure the application.
        """
        self.builder = Application.builder().token(bot_token).updater(None).build()

    async def handle_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        Handles the '/start' command sent by the user. This is the initial interaction point
        where the bot responds with a message prompting the user to share a URL.
        """

        self._current_chat_id = None
        self._current_message_id = None
        self._current_reel_id = None

        await ctx.bot.set_my_commands([
            BotCommand("start", "Start the conversation"),
            BotCommand("dango", "Know more about my developer"),
        ])

        await update.message.reply_text("Send me a URL! 🍡")

    async def send_instagram_reel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        Sends an Instagram reel video as a response to a user's message containing the reel's
        link.
        """
        self._current_reel_id = None

        self._current_chat_id: int = update.message.chat_id
        self._current_message_id: int = update.message.message_id
        user_input: str = update.message.text

        try:
            await ctx.bot.send_chat_action(  # Show "sending a video..." status
                chat_id=self._current_chat_id, action="UPLOAD_VIDEO"
            )

            (self._current_reel_id, reel_kwargs) = Instagram.get_reel(user_input)  # Fetch video data

            await ctx.bot.send_video(
                chat_id=self._current_chat_id, reply_to_message_id=self._current_message_id, **reel_kwargs
            )

        except Exception as e:
            logging.error(e)
            await self.show_exception_message(ctx)  # Ask user to report the error

    async def show_exception_message(self, ctx: ContextTypes.DEFAULT_TYPE):
        """
        Displays an error message to the user and provides them with an option to report the issue for correction.
        """
        error_question_options = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Report URL for correction", callback_data="report_url")],
        ])

        await ctx.bot.send_message(
            text="An unexpected error occurred while trying to process this video. "
                 "Would you like the reel to be sent to the developer for correction?",
            chat_id=self._current_chat_id,
            reply_to_message_id=self._current_message_id,
            reply_markup=error_question_options
        )

    async def handle_report_error(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        Log the error and provide the user with a confirmation message.
        """
        logging.warning(f"A user reported an error with the reel {self._current_reel_id}")

        inline_keyboard_replacement = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Reported! ✅", callback_data="reported")],
        ])

        await ctx.bot.edit_message_reply_markup(
            chat_id=self._current_chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=inline_keyboard_replacement
        )

    async def handle_aboutme(self, update: Update, _: ContextTypes.DEFAULT_TYPE):

        await update.message.reply_text(
            "Developed by Dango🍡\n"
            "Website: https://dangos.dev\n"
            "Github: https://github.com/dangos-dev"
        )
