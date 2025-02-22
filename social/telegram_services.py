import logging
from functools import wraps

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, InputMediaPhoto
from telegram.constants import ChatAction
from telegram.ext import Application, ContextTypes
from telegram.ext._applicationbuilder import InitApplicationBuilder

from social.instagram_services import Instagram


class DangoBot:
    def __init__(self, bot_token: str):
        self.builder: InitApplicationBuilder = Application.builder().token(bot_token).updater(None).build()
        self._current_chat_id: int = None
        self._current_message_id: int = None
        self._current_shortcode: str = None

    def create(self, username: str, password: str) -> None:
        """
        Creates and initializes an application with the provided bot token.

        This method builds an application instance using the provided bot token
        and assigns it to the `self.builder` attribute. This application instance
        is configured with no updater.

        Parameters:
            bot_token: A string representing the bot token used for authorization. It is
                required to configure the application.
        """

        self.instagram = Instagram(username, password)

    @staticmethod
    def instagram_caller(func):
        @wraps(func)
        async def wrapper(self, update: Update, *args, **kwargs):
            if update and update.message:
                self._current_chat_id = update.message.chat_id
                self._current_message_id = update.message.message_id

            return await func(self, update, *args, **kwargs)

        return wrapper

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

    @instagram_caller
    async def send_instagram_reel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        Sends an Instagram reel video as a response to a user's message containing the reel's
        link.
        """
        user_input: str = update.message.text

        try:
            await ctx.bot.send_chat_action(  # Show "sending a video..." status
                chat_id=self._current_chat_id, action=ChatAction.UPLOAD_VIDEO
            )

            self._current_shortcode = self.instagram.get_shortcode(user_input, "reel")
            reel_kwargs = self.instagram.get_reel(self._current_shortcode)  # Fetch reel data

            await ctx.bot.send_video(
                chat_id=self._current_chat_id, reply_to_message_id=self._current_message_id, **reel_kwargs
            )

        except Exception as e:
            logging.error(e)
            await self.show_exception_message(ctx)  # Ask user to report the error

    @instagram_caller
    async def send_instagram_photo(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        Sends an Instagram reel video as a response to a user's message containing the reel's
        link.
        """
        user_input: str = update.message.text

        try:
            await ctx.bot.send_chat_action(  # Show "sending a photo..." status
                chat_id=self._current_chat_id, action=ChatAction.UPLOAD_PHOTO
            )

            self._current_shortcode = self.instagram.get_shortcode(user_input, "p")
            media_photos = self.instagram.get_photo(self._current_shortcode)  # Fetch post data

            if not media_photos:
                await ctx.bot.send_message(
                    chat_id=self._current_chat_id,
                    reply_to_message_id=self._current_message_id,
                    text="This post does not contain any media."
                )
                return

            if len(media_photos["photos"]) == 1:
                await ctx.bot.send_photo(
                    chat_id=self._current_chat_id,
                    reply_to_message_id=self._current_message_id,
                    caption=media_photos["caption"],
                    photo=media_photos["photos"][0]
                )

            else:
                photo_groups = list(self._chunk_list(media_photos["photos"], 10))
                for group in photo_groups:
                    await ctx.bot.send_media_group(
                        chat_id=self._current_chat_id,
                        reply_to_message_id=self._current_message_id,
                        media=[InputMediaPhoto(photo) for photo in group],
                        caption=media_photos["caption"]
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
        logging.warning(f"A user reported an error with the reel {self._current_shortcode}")

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

    @staticmethod
    def _chunk_list(lst, n):
        """
        Divide una lista en sublistas de tamaño `n`.
        """
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
