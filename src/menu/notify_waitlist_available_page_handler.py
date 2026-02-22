"""
notify_waitlist_available_page_handler.py
Author: https://github.com/lendrixxx
Description: This file defines callback queries related to getting notifications when a waitlist spot is available.
"""

import calendar
import logging
import time
from datetime import datetime

import telebot

from chat.chat_manager import ChatManager
from common.class_availability import ClassAvailability
from common.result_data import ResultData
from history.history_manager import HistoryManager
from studios.studios_manager import StudiosManager


def notify_waitlist_available_message_handler(
    message: telebot.types.Message,
    logger: logging.Logger,
    bot: telebot.TeleBot,
    chat_manager: ChatManager,
    history_manager: HistoryManager,
    studios_manager: StudiosManager,
    full_result_data: ResultData,
) -> None:
    """
    Initiates notifying for waitlist mode and prompts the user for structured query
    input.

    Args:
      - message (telebot.types.Message): The message object containing user interaction data.
      - logger (logging.Logger): Logger for logging messages.
      - bot (telebot.TeleBot): The instance of the Telegram bot.
      - chat_manager (ChatManager): The manager handling chat data.
      - history_manager (HistoryManager): The manager handling user history data.
      - studios_manager (StudiosManager): The manager handling studios data.
      - full_result_data (ResultData): The schedule data of all the available classes.

    """
    history_manager.add(
        timestamp=int(time.time()),
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        command="notify_waitlist_available",
    )
    text = (
        "Please enter the class id and date (yyyy-mm-dd) of the class to be notified of when waitlist is available\n"
        "\n"
        "*e.g.:*\n"
        "MzNxWEI1cHRSZ2tmUnZDRnFTWGs5dz09\n"
        "2025-08-23\n"
    )

    chat_manager.add_message_id_to_delete(chat_id=message.chat.id, message_id=message.id)
    sent_msg = chat_manager.send_prompt(
        chat_id=message.chat.id,
        text=text,
        reply_markup=None,
        delete_sent_msg_in_future=False,
    )
    bot.register_next_step_handler(
        message=sent_msg,
        callback=notify_waitlist_available_input_handler,
        logger=logger,
        chat_manager=chat_manager,
        studios_manager=studios_manager,
        full_result_data=full_result_data,
    )


def notify_waitlist_available_input_handler(
    message: telebot.types.Message,
    logger: logging.Logger,
    chat_manager: ChatManager,
    studios_manager: StudiosManager,
    full_result_data: ResultData,
) -> None:
    """
    Processes the user's input, validates it, and subscribes to be notified for the
    specified classes.

    Args:
      - message (telebot.types.Message): The message object containing user interaction data.
      - logger (logging.Logger): Logger for logging messages.
      - chat_manager (ChatManager): The manager handling chat data.
      - studios_manager (StudiosManager): The manager handling studios data.
      - full_result_data (ResultData): The schedule data of all the available classes.

    """
    chat_manager.add_message_id_to_delete(chat_id=message.chat.id, message_id=message.id)
    input_str_list = message.text.splitlines()

    if len(input_str_list) != 2:
        text = "Failed to handle query. Unexpected format received."
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)
        return

    class_id = input_str_list[0]
    date_str = input_str_list[1]
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        text = f"Failed to handle query. Unexpected date format received - {e}"
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)
        return

    confirmation_text = "Subscribing to be notified when the following class is available for waitlist:\n"
    result = full_result_data.get_class_data(class_id=class_id, class_date=date_obj)
    if result is not None:
        class_date, class_data = result
        class_date_str = f"*{calendar.day_name[class_date.weekday()]}, {class_date.strftime('%d %B')}*"
        if class_data.availability == ClassAvailability.Full:
            confirmation_text += (
                class_date_str + " " + class_data.get_string(include_availability=False, include_capacity_info=False)
            )
        else:
            class_info_str = class_data.get_string(include_availability=False, include_capacity_info=False)
            text = f"{class_date_str} {class_info_str} is not full"
            chat_manager.send_prompt(
                chat_id=message.chat.id,
                text=text,
                reply_markup=None,
                delete_sent_msg_in_future=False,
            )
            return
    else:
        text = f"Failed to find class with id {class_id}."
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)
        return

    chat_manager.send_prompt(
        chat_id=message.chat.id,
        text=confirmation_text,
        reply_markup=None,
        delete_sent_msg_in_future=False,
    )
    studios_manager.add_class_to_notify_waitlist(chat_id=message.chat.id, class_id=class_id, class_date=date_obj)
