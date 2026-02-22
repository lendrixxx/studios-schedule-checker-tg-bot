"""
anarchy.py
Author: https://github.com/lendrixxx
Description:
  This file defines functions to handle the retrieving of
  class schedules and instructor IDs for Anarchy studio.
"""

import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from datetime import date, datetime, timedelta
from html import unescape
from typing import Optional

import pytz
import requests
from bs4 import BeautifulSoup

from common.capacity_info import CapacityInfo
from common.class_availability import ClassAvailability
from common.class_data import ClassData
from common.result_data import ResultData
from common.studio_location import StudioLocation
from common.studio_type import StudioType


def send_get_schedule_request(start_date: date, end_date: date) -> requests.models.Response:
    """
    Sends a GET request to retrieve the class schedule for the specified date range.

    Args:
      - start_date (date): The start date to retrieve the schedule for.
      - end_date (date): The end date to retrieve the schedule for.

    Returns:
      - requests.models.Response: The response object containing the schedule data.

    """
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    url = "https://widgets.mindbodyonline.com/widgets/schedules/189924/load_markup"
    params = {
        "callback": "jQuery36403516351979316319_1742526275618",
        "options[start_date]": start_date_str,
        "options[end_date]": end_date_str,
    }

    return requests.get(url=url, params=params)


def get_schedule_from_response_soup(
    logger: logging.Logger,
    soup: BeautifulSoup,
) -> dict[date, list[ClassData]]:
    """
    Parses the response soup to extract the class schedule data.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - soup (BeautifulSoup): The parsed HTML response from the schedule request.

    Returns:
      - dict[date, list[ClassData]]: Dictionary of dates and details of classes.

    """
    session_div_list = [div for div in soup.find_all(name="div") if "bw-session" in div.get("class", default=[])]
    result_dict = {}
    for session_div in session_div_list:
        session_time_div = session_div.find(name="div", class_="bw-session__time")
        if session_time_div is None:
            logger.warning(f"Failed to get session time from session info: {session_div}")
            continue

        start_time_tag = session_time_div.find(name="time", class_="hc_starttime")
        if start_time_tag is None:
            logger.warning(f"Failed to get session time: {session_time_div}")
            continue

        start_datetime_str = start_time_tag.get("datetime")
        if start_datetime_str is None:
            logger.warning(f"Failed to get session datetime: {start_time_tag}")
            continue

        start_datetime = datetime.fromisoformat(start_datetime_str)
        session_name_div = session_div.find(name="div", class_="bw-session__name")
        if session_name_div is None:
            logger.warning(f"Failed to get session name: {session_div}")
            continue

        session_staff_div = session_div.find(name="div", class_="bw-session__staff")
        if session_staff_div is None:
            logger.warning(f"Failed to get session instructor: {session_div}")
            continue

        instructor_name = " ".join(session_staff_div.get_text().strip().lower().split())
        instructor_name = instructor_name.replace("\n", " ")
        class_details = ClassData(
            studio=StudioType.Anarchy,
            location=StudioLocation.Robinson,
            name=session_name_div.get_text().strip(),
            instructor=instructor_name,
            time=start_datetime.strftime("%I:%M %p"),
            availability=(
                ClassAvailability.Waitlist if "Join Waitlist" in session_div.text else ClassAvailability.Available
            ),
            capacity_info=CapacityInfo(),
        )

        start_date = start_datetime.date()
        if start_date not in result_dict:
            result_dict[start_date] = [copy(class_details)]
        else:
            result_dict[start_date].append(copy(class_details))

    return result_dict


def get_soup_from_response(logger: logging.Logger, response: requests.models.Response) -> Optional[BeautifulSoup]:
    """
    Parses the response to a BeautifulSoup.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - response (requests.models.Response): The response object to be parsed.

    Returns:
      - BeautifulSoup: The parsed response object.

    """
    match = re.search(r"^\w+\((.*)\);?$", response.text, re.DOTALL)
    if match:
        try:
            json_str = match.group(1)
            data = json.loads(s=json_str)
        except Exception as e:
            logger.warning(f"Failed to parse response to json {response.text} - {e}")
            return None
    else:
        logger.warning(f"Failed to parse response {response.text}")
        return None

    try:
        cleaned_html = unescape(s=data["class_sessions"])
    except Exception as e:
        logger.warning(f"Failed to parse html from response {data} - {e}")
        return None

    return BeautifulSoup(markup=cleaned_html, features="html.parser")


def get_instructorid_map_from_response_soup(logger: logging.Logger, soup: BeautifulSoup) -> dict[str, str]:
    """
    Parses the response soup to extract the IDs of instructors.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - soup (BeautifulSoup): The parsed HTML response from the schedule request.

    Returns:
      - dict[str, str]: Dictionary of instructor names and IDs.

    """
    session_div_list = [div for div in soup.find_all(name="div") if "bw-session" in div.get("class", default=[])]
    instructorid_map: dict[str, str] = {}
    for session_div in session_div_list:
        session_staff_div = session_div.find(name="div", class_="bw-session__staff")
        if session_staff_div is None:
            logger.warning(f"Failed to get session instructor: {session_div}")
            continue

        instructor_name = " ".join(session_staff_div.get_text().strip().lower().split())
        instructor_name = instructor_name.replace("\n", " ")
        instructor_id = session_div.get("data-bw-widget-trainer")
        if instructor_id is None:
            logger.warning(f"Failed to get instructor id of instructor {instructor_name}: {session_div}")
            continue

        instructorid_map[instructor_name] = instructor_id

    return instructorid_map


def get_anarchy_schedule_and_instructorid_map(logger: logging.Logger) -> tuple[ResultData, dict[str, str]]:
    """
    Retrieves class schedules and instructor ID mappings.

    Args:
      - logger (logging.Logger): Logger for logging messages.

    Returns:
      - tuple[ResultData, dict[str, str]]: A tuple containing schedule data and instructor ID mappings.

    """
    results: list[tuple[ResultData, dict[str, str]]] = []
    results_lock = threading.Lock()

    def _get_anarchy_schedule_and_instructorid_map(start_date: date, end_date: date) -> None:
        """
        Helper to retrieve class schedules and instructor ID mappings. Stores results
        directly in results object defined in the main
        get_anarchy_schedule_and_instructorid_map function.

        Args:
          - start_date (date): Start date of the schedule to retrieve.
          - end_date (date): End date of the schedule to retrieve.

        Returns:
          - tuple[ResultData, dict[str, str]]: A tuple containing schedule data and instructor ID mappings.

        """
        get_schedule_response = send_get_schedule_request(start_date=start_date, end_date=end_date)
        soup = get_soup_from_response(logger=logger, response=get_schedule_response)
        get_schedule_response.close()
        if soup is None:
            with results_lock:
                results.append((ResultData(), {}))
            return

        # Get schedule
        result = ResultData()
        date_class_data_list_dict = get_schedule_from_response_soup(logger=logger, soup=soup)
        result.add_classes(classes=date_class_data_list_dict)

        # Get instructor id map
        instructorid_map = get_instructorid_map_from_response_soup(logger=logger, soup=soup)
        with results_lock:
            results.append((result, instructorid_map))
        return

    current_date = datetime.now(tz=pytz.timezone("Asia/Singapore")).date()
    tomorrow_date = current_date + timedelta(days=1)
    end_date = current_date + timedelta(weeks=3)  # Anarchy schedule only shows up to 3 weeks in advance
    start_dates = [current_date, tomorrow_date]
    end_dates = [end_date, end_date]

    with ThreadPoolExecutor() as executor:
        executor.map(_get_anarchy_schedule_and_instructorid_map, start_dates, end_dates)

    # Anarchy schedule doesn't show for future dates if there are no more classes today
    for result, instructorid_map in results:
        if len(result.classes) != 0:
            return result, instructorid_map

    return ResultData(), {}
