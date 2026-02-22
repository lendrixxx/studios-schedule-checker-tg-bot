"""
menu_manager.py
Author: https://github.com/lendrixxx
Description:
  This file defines the MenuManager class which is the main handler for the menus to be
  used for interactions between the Telegram bot and the chats it is being used in.
"""

import logging
from typing import Optional

import telebot

from chat.chat_manager import ChatManager
from chat.keyboard_manager import KeyboardManager
from history.history_manager import HistoryManager
from menu import (
    days_page_handler,
    get_schedule_handler,
    instructors_page_handler,
    main_page_handler,
    name_filter_page_handler,
    nerd_page_handler,
    notify_waitlist_available_page_handler,
    start_page_handler,
    studios_page_handler,
    time_page_handler,
    weeks_page_handler,
)
from studios.ally.ally import login as ally_login
from studios.studios_manager import StudiosManager


class MenuManager:
    """
    MenuManager handles setting up various message and callback query handlers for the
    Telegram bot. It is responsible for managing user interactions related to studios,
    instructors, schedules, and more.

    Attributes:
      - logger (logging.Logger): Logger for logging messages.
      - bot (telebot.TeleBot): The Telegram bot instance.
      - chat_manager (ChatManager): The manager handling chat data.
      - keyboard_manager (KeyboardManager): The manager handling keyboard generation and interaction.
      - studios_manager (StudiosManager): The manager handling studios data.
      - history_manager (HistoryManager): The manager handling user history data.

    """

    logger: logging.Logger
    bot: telebot.TeleBot
    chat_manager: ChatManager
    keyboard_manager: KeyboardManager
    studios_manager: StudiosManager
    history_manager: HistoryManager

    def __init__(
        self,
        logger: logging.Logger,
        bot: telebot.TeleBot,
        chat_manager: ChatManager,
        keyboard_manager: KeyboardManager,
        studios_manager: StudiosManager,
        history_manager: HistoryManager,
        ally_admin_telegram_chat_id: Optional[str],
    ) -> None:
        """
        Initializes the MenuManager instance.

        Args:
          - logger (logging.Logger): Logger for logging messages.
          - bot (telebot.TeleBot): The Telegram bot instance.
          - chat_manager (ChatManager): The manager handling chat data.
          - keyboard_manager (KeyboardManager): The manager handling keyboard generation and interaction.
          - studios_manager (StudiosManager): The manager handling studios data.
          - history_manager (HistoryManager): The manager handling user history data.
          - ally_admin_telegram_chat_id (str): The chat id to use to retrieve ally OTP.
            Should be id of chat of username provided.

        """
        self.logger = logger
        self.bot = bot
        self.chat_manager = chat_manager
        self.keyboard_manager = keyboard_manager
        self.studios_manager = studios_manager
        self.history_manager = history_manager
        self.ally_admin_telegram_chat_id = ally_admin_telegram_chat_id

        self.setup_message_handlers()
        self.setup_callback_query_handlers()

    def setup_callback_query_handlers(self) -> None:
        """
        Sets up all the callback query handlers for the different steps and stages of
        user interaction.
        """

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "main-page-handler")
        def main_page_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            main_page_handler.main_page_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "studios")
        def studios_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            studios_page_handler.studios_callback_query_handler(
                query=query,
                bot=self.bot,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "studios-selection")
        def studios_selection_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            studios_page_handler.studios_selection_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "locations")
        def locations_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            studios_page_handler.locations_callback_query_handler(
                query=query,
                bot=self.bot,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "instructors-selection")
        def instructors_selection_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.instructors_selection_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "show-instructors")
        def show_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.show_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                studios_manager=self.studios_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "rev-instructors")
        def rev_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.rev_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Rev"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "barrys-instructors")
        def barrys_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.barrys_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Barrys"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "absolute-spin-instructors")
        def absolute_spin_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.absolute_spin_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Absolute"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "absolute-pilates-instructors")
        def absolute_pilates_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.absolute_pilates_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Absolute"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "ally-spin-instructors")
        def ally_spin_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.ally_spin_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Ally"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "ally-pilates-instructors")
        def ally_pilates_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.ally_pilates_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Ally"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "anarchy-instructors")
        def anarchy_instructors_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            instructors_page_handler.anarchy_instructors_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                bot=self.bot,
                instructorid_map=self.studios_manager.studios["Anarchy"].get_instructorid_map(),
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "weeks-selection")
        def weeks_selection_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            weeks_page_handler.weeks_selection_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "weeks")
        def weeks_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            weeks_page_handler.weeks_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "days")
        def days_page_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            days_page_handler.days_page_callback_query_handler(
                query=query,
                bot=self.bot,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "days-selection")
        def days_selection_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            days_page_handler.days_selection_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "days-next")
        def days_next_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            days_page_handler.days_next_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "time-selection")
        def time_selection_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            time_page_handler.time_selection_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "time-selection-add")
        def time_selection_add_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            time_page_handler.time_selection_add_callback_query_handler(
                query=query,
                logger=self.logger,
                bot=self.bot,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "time-selection-remove")
        def time_selection_remove_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            time_page_handler.time_selection_remove_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "remove-timeslot")
        def time_selection_remove_timeslot_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            time_page_handler.time_selection_remove_timeslot_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "time-selection-reset")
        def time_selection_reset_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            time_page_handler.time_selection_reset_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "class-name-filter-selection")
        def class_name_filter_selection_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            name_filter_page_handler.class_name_filter_selection_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "class-name-filter-add")
        def class_name_filter_set_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            name_filter_page_handler.class_name_filter_set_callback_query_handler(
                query=query,
                bot=self.bot,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "class-name-filter-reset")
        def class_name_filter_reset_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            name_filter_page_handler.class_name_filter_reset_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
            )

        @self.bot.callback_query_handler(func=lambda query: eval(query.data)["step"] == "get-schedule")
        def get_schedule_callback_query_handler(query: telebot.types.CallbackQuery) -> None:
            get_schedule_handler.get_schedule_callback_query_handler(
                query=query,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                full_result_data=self.studios_manager.get_cached_result_data(),
            )

    def setup_message_handlers(self) -> None:
        """
        Sets up all the message handlers for the different commands.
        """

        @self.bot.message_handler(commands=["start"])
        def start_message_handler(message: telebot.types.Message) -> None:
            start_page_handler.start_message_handler(
                message=message,
                chat_manager=self.chat_manager,
                keyboard_manager=self.keyboard_manager,
                history_manager=self.history_manager,
            )

        @self.bot.message_handler(commands=["nerd"])
        def nerd_message_handler(message: telebot.types.Message) -> None:
            nerd_page_handler.nerd_message_handler(
                message=message,
                logger=self.logger,
                bot=self.bot,
                chat_manager=self.chat_manager,
                history_manager=self.history_manager,
                studios_manager=self.studios_manager,
                full_result_data=self.studios_manager.get_cached_result_data(),
            )

        @self.bot.message_handler(commands=["instructors"])
        def instructors_message_handler(message: telebot.types.Message) -> None:
            instructors_page_handler.instructors_message_handler(
                message=message,
                chat_manager=self.chat_manager,
                history_manager=self.history_manager,
                studios_manager=self.studios_manager,
            )

        @self.bot.message_handler(commands=["notify_waitlist_available"])
        def notify_waitlist_available_message_handler(message: telebot.types.Message) -> None:
            notify_waitlist_available_page_handler.notify_waitlist_available_message_handler(
                message=message,
                logger=self.logger,
                bot=self.bot,
                chat_manager=self.chat_manager,
                history_manager=self.history_manager,
                studios_manager=self.studios_manager,
                full_result_data=self.studios_manager.get_cached_result_data(),
            )

        @self.bot.message_handler(commands=["ally_login"])
        def ally_login_message_handler(message: telebot.types.Message) -> None:
            if self.ally_admin_telegram_chat_id is None:
                return

            # Only allow the admin to login
            if str(message.chat.id) != str(self.ally_admin_telegram_chat_id):
                return

            self.chat_manager.add_message_id_to_delete(chat_id=message.chat.id, message_id=message.id)
            sent_msg = self.chat_manager.send_prompt(
                chat_id=message.chat.id,
                text="Please enter the email to login",
                reply_markup=None,
                delete_sent_msg_in_future=True,
            )

            def ally_login_message_get_username_handler(message: telebot.types.Message) -> None:
                ally_login(
                    logger=self.logger,
                    ally_username=message.text.strip(),
                    ally_admin_telegram_chat_id=self.ally_admin_telegram_chat_id,
                    bot=self.bot,
                    chat_manager=self.chat_manager,
                )

            self.bot.register_next_step_handler(
                message=sent_msg,
                callback=ally_login_message_get_username_handler,
            )
