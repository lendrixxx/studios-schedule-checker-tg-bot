"""
ally.py
Author: https://github.com/lendrixxx
Description:
  This file defines functions to handle the retrieving of class schedules and instructor IDs
  for Ally studios.
"""

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Optional

import jwt
import pytz
import requests
import telebot

from chat.chat_manager import ChatManager
from common.capacity_info import CapacityInfo
from common.class_availability import ClassAvailability
from common.class_data import ClassData
from common.result_data import ResultData
from common.studio_location import StudioLocation
from common.studio_type import StudioType
from studios.ally.data.ally import (
    MAX_SCHEDULE_DAYS,
    ROOM_ID_TO_STUDIO_LOCATION_MAP,
    ROOM_ID_TO_STUDIO_TYPE_MAP,
    clean_class_name,
)

BASE_URL = "https://api.ally.family"
access_token = os.getenv("ALLY_ACCESS_TOKEN")
refresh_token = os.getenv("ALLY_REFRESH_TOKEN")


def check_access_token(
    logger: logging.Logger,
    ally_admin_telegram_chat_id: str,
    chat_manager: ChatManager,
) -> None:
    """
    Checks and refreshes token if it is expiring.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - ally_admin_telegram_chat_id (str): The chat id to use to retrieve ally OTP.
        Should be id of chat of username provided.
      - bot (telebot.TeleBot): The Telegram bot instance.
      - chat_manager (ChatManager): The manager handling chat data.

    Returns:
      - bool: True if successfully refreshed access token, false otherwise.

    """
    return
    if not is_access_token_expiring(logger, timedelta(days=1)):
        return

    if refresh_access_token(logger=logger):
        return

    text = "Ally access token is expiring. Please use /ally\\_login to refresh token"
    chat_manager.send_prompt(
        chat_id=ally_admin_telegram_chat_id,
        text=text,
        reply_markup=None,
        delete_sent_msg_in_future=False,
    )


def refresh_access_token(logger: logging.Logger) -> bool:
    """
    Refreshes access token with refresh token.

    Args:
      - logger (logging.Logger): Logger for logging messages.

    Returns:
      - bool: True if successfully refreshed access token, false otherwise.

    """
    global access_token, refresh_token
    if access_token is None or refresh_token is None:
        return False

    request_body = {
        "oldToken": access_token,
        "refreshToken": refresh_token,
    }
    response = requests.post(f"{BASE_URL}/auth/refresh-token", json=request_body)
    if response.status_code != 200:
        logger.warning(f"Failed to refresh Ally access token: Status: {response.status_code}, Data: {response.text}")
        return False

    response_json = response.json()
    try:
        access_token = response_json["accessToken"]
    except Exception as e:
        logger.warning(f"Failed to get Ally access token: {e}, Response: {response_json}")
        return False

    try:
        refresh_token = response_json["refreshToken"]
    except Exception as e:
        logger.warning(f"Failed to get Ally refresh token: {e}, Response: {response_json}")
        return False

    return True


def is_access_token_valid(logger: logging.Logger) -> bool:
    """
    Checks if access token is valid.

    Args:
      - logger (logging.Logger): Logger for logging messages.

    Returns:
      - bool: True if access token is valid, false otherwise.

    """
    if access_token is None:
        return False

    try:
        payload = jwt.decode(access_token, options={"verify_signature": False})
        exp = payload.get("exp")
        return exp is not None and datetime.now().timestamp() < exp
    except Exception as e:
        logger.warning(f"Failed to check if Ally access token is valid: {e}")
        return False


def is_access_token_expiring(logger: logging.Logger, within: timedelta) -> bool:
    """
    Checks if access token is expiring within the specified period.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - within (timedelta): Time window to check (e.g., timedelta(days=1)).

    Returns:
      - bool: True if access token expires within window, false otherwise.

    """
    if access_token is None:
        return True

    try:
        payload = jwt.decode(access_token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp is None:
            return False

        exp_datetime = datetime.fromtimestamp(exp, tz=pytz.timezone("UTC"))
        return exp_datetime - datetime.now(tz=pytz.timezone("UTC")) <= within
    except Exception as e:
        logger.warning(f"Failed to check if Ally access token is expiring: {e}")
        return True


def login(
    logger: logging.Logger,
    ally_username: str,
    ally_admin_telegram_chat_id: str,
    bot: telebot.TeleBot,
    chat_manager: ChatManager,
) -> None:
    """
    Logins and retrieves access and refresh tokens.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - ally_username (str): Email used to login.
      - ally_admin_telegram_chat_id (str): The chat id to use to retrieve ally OTP.
        Should be id of chat of username provided.
      - bot (telebot.TeleBot): The Telegram bot instance.
      - chat_manager (ChatManager): The manager handling chat data.

    """
    response = requests.post(f"{BASE_URL}/auth/sign-in", json={"email": ally_username})
    if response.status_code != 200:
        logger.warning(
            f"Failed to get Ally schedule - Failed to login: Status: {response.status_code}, Data: {response.text}"
        )
        return

    try:
        uid = response.json()["data"]["uid"]
    except Exception as e:
        logger.warning(f"Failed to get Ally schedule - Failed to get UID: {e}, Response: {response.text}")
        return

    response = requests.post(f"{BASE_URL}/auth/send-otp", json={"id": uid})
    if response.status_code != 200:
        f"Failed to get Ally schedule - Failed to send otp: Status: {response.status_code}, Data: {response.text}"
        return

    text = "Enter OTP for Ally"
    sent_msg = chat_manager.send_prompt(
        chat_id=ally_admin_telegram_chat_id,
        text=text,
        reply_markup=None,
        delete_sent_msg_in_future=True,
    )
    bot.register_next_step_handler(
        message=sent_msg,
        callback=update_global_tokens,
        chat_manager=chat_manager,
        uid=uid,
    )


def update_global_tokens(
    message: telebot.types.Message,
    chat_manager: ChatManager,
    uid: str,
) -> None:
    """
    Processes the user's OTP input, verifies it, and updates the global access and
    refresh tokens.

    Args:
      - message (telebot.types.Message): The message object containing user interaction data.
      - chat_manager (ChatManager): The manager handling chat data.
      - uid (str): The UID of the user that the OTP was sent to.

    """
    verify_otp_input_handler_response = verify_otp_input_handler(
        message=message,
        chat_manager=chat_manager,
        uid=uid,
    )
    if verify_otp_input_handler_response is not None:
        global access_token, refresh_token
        access_token, refresh_token = verify_otp_input_handler_response
        text = "Successfully authenticated for Ally!"
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)


def verify_otp_input_handler(
    message: telebot.types.Message,
    chat_manager: ChatManager,
    uid: str,
) -> Optional[tuple[str, str]]:
    """
    Processes the user's OTP input, verifies it, and retrieves new access and refresh
    tokens.

    Args:
      - message (telebot.types.Message): The message object containing user interaction data.
      - chat_manager (ChatManager): The manager handling chat data.
      - uid (str): The UID of the user that the OTP was sent to.

    Returns:
      - Optional[tuple[str, str]]: A tuple containing the new access token and refresh token
        if verification is successful, none otherwise.

    """
    message_without_whitespace = "".join(message.text.split())
    response = requests.post(
        f"{BASE_URL}/auth/verif-otp",
        json={
            "otp": message_without_whitespace,
            "id": uid,
        },
    )
    if response.status_code != 200:
        text = f"Failed to verify otp: Status: {response.status_code}, Data: {response.text}"
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)
        return None

    try:
        access_token = response.json()["data"]["accessToken"]
    except Exception as e:
        text = f"Failed to get access token: {e}, Response: {response.text}"
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)
        return None

    try:
        refresh_token = response.json()["data"]["refreshToken"]
    except Exception as e:
        text = f"Failed to get refresh token: {e}, response: {response.text}"
        chat_manager.send_prompt(chat_id=message.chat.id, text=text, reply_markup=None, delete_sent_msg_in_future=False)
        return None

    return (access_token, refresh_token)


def send_get_schedule_request(schedule_date: date) -> requests.models.Response:
    """
    Sends a GET request to retrieve the class schedule for the specified date.

    Args:
      - schedule_date (date): The date to retrieve the schedule for.

    Returns:
      - requests.models.Response: The response object containing the schedule data.

    """
    return requests.get(
        url=f"{BASE_URL}/booking/all/schedule/{schedule_date.isoformat()}",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def parse_get_schedule_response(
    logger: logging.Logger,
    response: requests.models.Response,
) -> dict[date, list[ClassData]]:
    """
    Parses the get schedule response to extract the class schedule data.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - response (requests.models.Response): The get schedule response from the schedule request.

    Returns:
      - dict[date, list[ClassData]]: Dictionary of dates and details of classes.

    """
    if response.status_code != 200:
        logger.warning(f"Failed to get Ally schedule - API callback error {response.status_code}")
        return {}

    result_dict: dict[date, list[ClassData]] = {}

    try:
        for item in response.json()["data"]:
            try:
                start_datetime = datetime.strptime(item["from"], "%Y-%m-%d %H:%M:%S")
                class_date = start_datetime.date()

                availability = (
                    ClassAvailability.Waitlist
                    if item.get("isWaitingList")
                    else ClassAvailability.Full if item.get("isFull") else ClassAvailability.Available
                )

                room_id = item["Room"]["id"]
                studio = ROOM_ID_TO_STUDIO_TYPE_MAP.get(room_id, StudioType.Unknown)
                location = ROOM_ID_TO_STUDIO_LOCATION_MAP.get(room_id, StudioLocation.Unknown)

                class_details = ClassData(
                    studio=studio,
                    location=location,
                    name=clean_class_name(item["ClassType"]["displayName"]),
                    instructor=item["Instructor"]["name"] if item["Instructor"] is not None else "",
                    time=start_datetime.strftime("%I:%M %p"),
                    availability=availability,
                    capacity_info=CapacityInfo(),
                    class_id=item["id"],
                )

                if class_date not in result_dict:
                    result_dict[class_date] = [class_details]
                else:
                    result_dict[class_date].append(class_details)

            except Exception as e:
                logger.warning(f"Failed to parse Ally class item: {item} - {e}")
    except Exception as e:
        logger.warning(f"Failed to get Ally schedule - {e}: {response.text}")
        return {}

    return result_dict


def get_ally_schedule(
    logger: logging.Logger,
) -> ResultData:
    """
    Retrieves all the available class schedules.

    Returns:
      - ResultData: The schedule data.

    """
    result = ResultData()
    result_lock = threading.Lock()
    start_date = datetime.now(tz=pytz.timezone("Asia/Singapore"))

    def _get_schedule_for_single_day(day_offset: int) -> None:
        schedule_date = start_date + timedelta(days=day_offset)
        get_schedule_response = send_get_schedule_request(schedule_date=schedule_date)
        date_class_data_list_dict = parse_get_schedule_response(logger=logger, response=get_schedule_response)
        with result_lock:
            result.add_classes(classes=date_class_data_list_dict)

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(_get_schedule_for_single_day, range(MAX_SCHEDULE_DAYS + 1))

    return result


def get_ally_instructorid_map(logger: logging.Logger) -> dict[str, str]:
    """
    Retrieves the IDs of instructors.

    Args:
      - logger (logging.Logger): Logger for logging messages.

    Returns:
      - dict[str, str]: Dictionary of instructor names and IDs.

    """
    params: dict[str, int] = {
        "page": 1,
        "pageSize": 1000,
    }
    response = requests.get(
        url=f"{BASE_URL}/instructor",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )

    instructorid_map: dict[str, str] = {}
    try:
        response_json = response.json()
        for item in response_json["data"]:
            try:
                instructorid_map[item["name"]] = item["id"]
            except Exception as e:
                logger.warning(f"Failed to get Ally instructor - {e}: {item}")
                continue
    except Exception as e:
        logger.warning(f"Failed to get Ally list of instructors - {e}: {response.text}")
        instructorid_map = {}

    return instructorid_map


def get_ally_schedule_and_instructorid_map(logger: logging.Logger) -> tuple[ResultData, dict[str, str]]:
    """
    Retrieves class schedules and instructor ID mappings.

    Args:
      - logger (logging.Logger): Logger for logging messages.

    Returns:
      - tuple[ResultData, dict[str, str]]: A tuple containing schedule data and instructor ID mappings.

    """
    return (ResultData(), {})
    if not is_access_token_valid(logger):
        return (ResultData(), {})

    return (
        get_ally_schedule(logger=logger),
        get_ally_instructorid_map(logger=logger),
    )
