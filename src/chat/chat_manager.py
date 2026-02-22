"""
chat_manager.py
Author: https://github.com/lendrixxx
Description:
  This file defines the ChatManager class which is the main handler for
  interactions between the Telegram bot and the chats it is being used in.
"""

from __future__ import annotations

import logging
import threading
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

import telebot

from common.data import SORTED_DAYS, STUDIO_LOCATIONS_MAP
from common.query_data import QueryData
from common.studio_data import StudioData
from common.studio_type import StudioType


class ChatManager:
    """
    Manages chat data and interactions between the Telegram bot and chats. This class
    handles query data, messages to be edited or deleted, and communication with chats.

    Attributes:
      - logger (logging.Logger): Logger for logging messages.
      - bot (telebot.TeleBot): The Telegram bot instance.
      - chat_query_data (dict[int, QueryData]): Dictionary of chat ids and query data.
      - chat_message_ids_to_delete (dict[int, list[int]]): Dictionary of chat ids and message ids to delete.
      - chat_messages_to_edit (dict[int, MessagesToEdit]): Dictionary of chat ids and messages to edit.

    """

    logger: logging.Logger
    bot: telebot.TeleBot
    chat_query_data: dict[int, QueryData]
    chat_message_ids_to_delete: dict[int, list[int]]
    chat_messages_to_edit: dict[int, ChatManager.MessagesToEdit]
    chat_locks: dict[int, threading.Lock]
    locks_lock = threading.Lock()

    @dataclass
    class MessagesToEdit:
        """
        Stores messages that may need to be edited in a chat.

        Attributes:
          - days_selection_message (Optional[telebot.types.Message]): Message for selecting days.
          - studios_selection_message (Optional[telebot.types.Message]): Message for selecting studios.
          - locations_selection_message (Optional[telebot.types.Message]): Message for selecting studio locations.

        """

        days_selection_message: Optional[telebot.types.Message]
        studios_selection_message: Optional[telebot.types.Message]
        locations_selection_message: Optional[telebot.types.Message]

        def __init__(self) -> None:
            """
            Initializes the MessagesToEdit instance with None values.
            """
            self.days_selection_message = None
            self.studios_selection_message = None
            self.locations_selection_message = None

    def __init__(self, logger: logging.Logger, bot: telebot.TeleBot) -> None:
        """
        Initializes the ChatManager instance.

        Args:
          - logger (logging.Logger): The logger for logging messages.
          - bot (telebot.TeleBot): The Telegram bot instance.

        """
        self.logger = logger
        self.bot = bot
        self.chat_query_data: dict[int, QueryData] = {}
        self.chat_message_ids_to_delete: dict[int, list[int]] = {}
        self.chat_messages_to_edit: dict[int, ChatManager.MessagesToEdit] = {}
        self.chat_locks: dict[int, threading.Lock] = {}
        self.locks_lock = threading.Lock()

    def _get_chat_lock(self, chat_id: int) -> threading.Lock:
        with self.locks_lock:
            if chat_id not in self.chat_locks:
                self.chat_locks[chat_id] = threading.Lock()
            return self.chat_locks[chat_id]

    def reset_query_and_messages_to_edit_data(self, chat_id: int) -> None:
        """
        Resets the query data and messages to edit for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to reset data.

        """
        with self._get_chat_lock(chat_id):
            self.chat_query_data[chat_id] = QueryData(
                studios=None,
                current_studio=StudioType.Null,
                weeks=1,
                days=SORTED_DAYS,
                start_times=[],
                class_name_filter="",
            )
            self.chat_messages_to_edit[chat_id] = ChatManager.MessagesToEdit()

    def update_query_data_current_studio(self, chat_id: int, current_studio: StudioType) -> None:
        """
        Updates the currently selected studio in the query data for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - current_studio (StudioType): The selected studio type.

        """
        with self._get_chat_lock(chat_id):
            self.chat_query_data[chat_id].current_studio = current_studio

    def update_query_data_studios(self, chat_id: int, studios: dict[StudioType, StudioData]) -> None:
        """
        Updates the selected studios in the query data for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - studios (dict[StudioType, StudioData]): The selected studios to update the query data with.

        """
        with self._get_chat_lock(chat_id):
            self.chat_query_data[chat_id].studios = studios

    def update_query_data_select_all_studios(self, chat_id: int) -> None:
        """
        Updates the selected studios in the query data of the specified chat to all be
        selected.

        Args:
          - chat_id (int): The ID of the chat to update.

        """
        with self._get_chat_lock(chat_id):
            self.chat_query_data[chat_id].studios = {
                StudioType.Rev: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.Rev]),
                StudioType.Barrys: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.Barrys]),
                StudioType.AbsoluteSpin: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.AbsoluteSpin]),
                StudioType.AbsolutePilates: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.AbsolutePilates]),
                StudioType.AllySpin: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.AllySpin]),
                StudioType.AllyPilates: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.AllyPilates]),
                StudioType.AllyRecovery: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.AllyRecovery]),
                StudioType.Anarchy: StudioData(locations=STUDIO_LOCATIONS_MAP[StudioType.Anarchy]),
            }

    def update_query_data_days(self, chat_id: int, days: list[str]) -> None:
        """
        Updates the selected days in the query data of the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - days (list[str]): The list of selected days to update the query data with.

        """
        with self._get_chat_lock(chat_id):
            self.chat_query_data[chat_id].days = days

    def update_query_data_weeks(self, chat_id: int, weeks: int) -> None:
        """
        Updates the number of weeks selected in the query data of the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - weeks (int): The number of weeks to update the query data with.

        """
        with self._get_chat_lock(chat_id):
            self.chat_query_data[chat_id].weeks = weeks

    def update_studios_selection_message(self, chat_id: int, studios_selection_message: telebot.types.Message) -> None:
        """
        Updates the studios selection message for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - studios_selection_message (telebot.types.Message):
            The studios selection message to update the existing stored message with.

        """
        with self._get_chat_lock(chat_id):
            self.chat_messages_to_edit[chat_id].studios_selection_message = studios_selection_message

    def update_locations_selection_message(
        self,
        chat_id: int,
        locations_selection_message: telebot.types.Message,
    ) -> None:
        """
        Updates the locations selection message for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - locations_selection_message (telebot.types.Message):
            The locations selection message to update the existing stored message with.

        """
        with self._get_chat_lock(chat_id):
            self.chat_messages_to_edit[chat_id].locations_selection_message = locations_selection_message

    def update_days_selection_message(self, chat_id: int, days_selection_message: telebot.types.Message) -> None:
        """
        Updates the days selection message for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to update.
          - days_selection_message (telebot.types.Message):
            The days selection message to update the existing stored message with.

        """
        with self._get_chat_lock(chat_id):
            self.chat_messages_to_edit[chat_id].days_selection_message = days_selection_message

    def add_message_id_to_delete(self, chat_id: int, message_id: int) -> None:
        """
        Adds a message ID to the list of messages to delete for the specified chat on
        the next call to send_prompt.

        Args:
          - chat_id (int): The ID of the chat to add a message to be deleted.
          - message_id (int): The ID of the message to be deleted.

        """
        with self._get_chat_lock(chat_id):
            if chat_id in self.chat_message_ids_to_delete:
                self.chat_message_ids_to_delete[chat_id].append(message_id)
            else:
                self.chat_message_ids_to_delete[chat_id] = [message_id]

    def get_query_data(self, chat_id: int) -> QueryData:
        """
        Retrieves the query data for the specified chat.

        Args:
          - chat_id (int): The ID of the chat to retrieve query data.

        Returns:
          QueryData: The stored query data for the specified chat.

        """
        with self._get_chat_lock(chat_id):
            return deepcopy(self.chat_query_data[chat_id])

    def get_studios_selection_message(self, chat_id: int) -> telebot.types.Message:
        """
        Retrieves the studios selection message that was stored.

        Args:
          - chat_id (int): The ID of the chat to retrieve the studios selection message.

        Returns:
          telebot.types.Message: The stored studios selection message for the specified chat.

        """
        with self._get_chat_lock(chat_id):
            return deepcopy(self.chat_messages_to_edit[chat_id].studios_selection_message)

    def get_locations_selection_message(self, chat_id: int) -> telebot.types.Message:
        """
        Retrieves the locations selection message that was stored.

        Args:
          - chat_id (int): The ID of the chat to retrieve the locations selection message.

        Returns:
          telebot.types.Message: The stored locations selection message for the specified chat.

        """
        with self._get_chat_lock(chat_id):
            return deepcopy(self.chat_messages_to_edit[chat_id].locations_selection_message)

    def get_days_selection_message(self, chat_id: int) -> telebot.types.Message:
        """
        Retrieves the days selection message that was stored.

        Args:
          - chat_id (int): The ID of the chat to retrieve the days selection message.

        Returns:
          telebot.types.Message: The stored days selection message for the specified chat.

        """
        with self._get_chat_lock(chat_id):
            return deepcopy(self.chat_messages_to_edit[chat_id].days_selection_message)

    def send_prompt(
        self,
        chat_id: int,
        text: str,
        reply_markup: telebot.types.InlineKeyboardMarkup,
        delete_sent_msg_in_future: bool,
    ) -> telebot.types.Message:
        """
        Sends a message to the chat and optionally schedules it for deletion on the next
        call to send_prompt.

        Args:
          - chat_id (int): The ID of the chat to send the prompt to.
          - text (str): The message to send to the chat.
          - reply_markup (Optional[telebot.types.InlineKeyboardMarkup]): The reply markup to use.
          - delete_sent_msg_in_future (bool):
            True if the message should be deleted on the next call to send_prompt, false otherwise.

        Returns:
          telebot.types.Message: The sent message object.

        """
        with self._get_chat_lock(chat_id):
            message_ids_to_delete = self.chat_message_ids_to_delete.pop(chat_id, None)

        if message_ids_to_delete is not None:
            try:
                self.bot.delete_messages(chat_id=chat_id, message_ids=message_ids_to_delete)
            except Exception as e:
                self.logger.warning(f"Failed to delete messages - {e}")

        sent_msg = self.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
        if delete_sent_msg_in_future:
            self.add_message_id_to_delete(chat_id=chat_id, message_id=sent_msg.id)

        return sent_msg
