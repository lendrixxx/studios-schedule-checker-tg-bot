"""
zingfit.py
Author: https://github.com/lendrixxx
Description:
  This file defines functions to handle the retrieving of class schedules and instructor IDs for Zingfit studios.
"""

import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from datetime import date, datetime
from typing import Callable, Optional

import pytz
import requests
from bs4 import BeautifulSoup

from common.capacity_info import CapacityInfo
from common.class_availability import ClassAvailability
from common.class_data import ClassData
from common.data import RESPONSE_AVAILABILITY_MAP
from common.result_data import ResultData
from common.studio_location import StudioLocation
from common.studio_type import StudioType


def send_get_schedule_request(
    studio_url_subdomain: str,
    locations: list[StudioLocation],
    location_to_site_id_map: dict[StudioLocation, int],
    week: int,
) -> requests.models.Response:
    """
    Sends a GET request to retrieve the class schedule for the specified locations and
    week.

    Args:
      - studio_url_subdomain (str): The subdomain of the studio.
      - locations (list[StudioLocation]): The list of studio locations to retrieve the schedule for.
      - location_to_site_id_map (dict[StudioLocation, int]): Dictionary of studio location and site IDs.
      - week (int): The week number to retrieve the schedule for.

    Returns:
      - requests.models.Response: The response object containing the schedule data.

    """
    url = f"https://{studio_url_subdomain}.zingfit.com/reserve/index.cfm"
    params: dict[str, str | int] = {"wk": week, "action": "Reserve.chooseClass"}

    site_param_name = "site"
    for location in locations:
        params[site_param_name] = location_to_site_id_map[location]
        if site_param_name == "site":
            site_param_name = "site2"
        elif site_param_name != "site5":  # API only accepts up to site5
            site_param_name = site_param_name[:-1] + str(int(site_param_name[-1]) + 1)
        else:
            break

    return requests.get(url=url, params=params)


def get_schedule_from_response_soup(
    logger: logging.Logger,
    soup: BeautifulSoup,
    studio_name: str,
    table_heading_date_format: str,
    room_id_to_studio_type_map: dict[str, StudioType],
    room_id_to_studio_location_map: dict[str, StudioLocation],
    clean_class_name_func: Optional[Callable[[str], str]],
) -> dict[date, list[ClassData]]:
    """
    Parses the response soup to extract the class schedule data.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - soup (BeautifulSoup): The parsed HTML response from the schedule request.
      - studio_name (str): Name of studio to use for logging.
      - table_heading_date_format (str): The date format of the table heading. e.g. "%m.%d"
      - room_id_to_studio_type_map (dict[str, StudioType]): The dictionary of room IDs and studio types.
      - room_id_to_studio_location_map (dict[str, StudioType]): The dictionary of room IDs and studio locations.
      - clean_class_name_func (Optional[Callable[[str], str]]): Optional function to format the raw class name string.

    Returns:
      - dict[date, list[ClassData]]: Dictionary of dates and details of classes.

    """
    schedule_table = soup.find(name="table", id="reserve", class_="scheduleTable")
    if schedule_table is None:
        logger.warning(f"Failed to get {studio_name} schedule - Schedule table not found: {soup}")
        return {}

    if schedule_table.thead is None:
        logger.warning(f"Failed to get {studio_name} schedule - Schedule table head not found: {schedule_table}")
        return {}

    if schedule_table.tbody is None:
        # No classes for the week
        return {}

    schedule_table_head_row = schedule_table.thead.find(name="tr")
    if schedule_table_head_row is None:
        logger.warning(
            f"Failed to get {studio_name} schedule - Schedule table head row not found: {schedule_table.thead}"
        )
        return {}

    schedule_table_body_row = schedule_table.tbody.find(name="tr")
    if schedule_table_body_row is None:
        logger.warning(f"Failed to get {studio_name} schedule - Schedule table body row not found: {schedule_table}")
        return {}

    schedule_table_head_data_list = schedule_table_head_row.find_all(name="td")
    schedule_table_head_data_list_len = len(schedule_table_head_data_list)
    if schedule_table_head_data_list_len == 0:
        logger.warning(
            f"Failed to get {studio_name} schedule - Schedule table head data is null: {schedule_table_head_row}"
        )
        return {}

    schedule_table_body_data_list = schedule_table_body_row.find_all(name="td")
    schedule_table_body_data_list_len = len(schedule_table_body_data_list)
    if schedule_table_body_data_list_len == 0:
        logger.warning(
            f"Failed to get {studio_name} schedule - Schedule table body data is null: {schedule_table_body_row}"
        )
        return {}

    if schedule_table_head_data_list_len != schedule_table_body_data_list_len:
        logger.warning(
            f"Failed to get {studio_name} schedule - Schedule table head and body list length does not match: "
            f"Head data: {schedule_table_head_data_list}\nBody data: {schedule_table_body_data_list}"
        )
        return {}

    result_dict = {}
    current_year = datetime.now(tz=pytz.timezone("Asia/Singapore")).year
    for index, schedule_table_head_data in enumerate(schedule_table_head_data_list):
        schedule_table_body_data = schedule_table_body_data_list[index]
        date_string = schedule_table_head_data.find(name="span", class_="thead-date").get_text().strip()
        current_date = datetime.strptime(date_string, table_heading_date_format).date()
        current_date = current_date.replace(year=current_year)
        reserve_table_body_data_div_list = schedule_table_body_data.find_all(name="div")
        if len(reserve_table_body_data_div_list) == 0:
            # Reserve table data div might be empty because schedule is not shown for the week
            continue

        for reserve_table_body_data_div in reserve_table_body_data_div_list:
            reserve_table_body_data_div_class_list = reserve_table_body_data_div.get("class")
            if len(reserve_table_body_data_div_class_list) < 2:
                availability = ClassAvailability.Null  # Class is over
            else:
                availability = RESPONSE_AVAILABILITY_MAP[reserve_table_body_data_div_class_list[1]]

            schedule_class_span = reserve_table_body_data_div.find(name="span", class_="scheduleClass")
            if schedule_class_span is None:
                # Check if class was cancelled or is an actual error
                is_cancelled = reserve_table_body_data_div.find(name="span", class_="scheduleCancelled")
                if is_cancelled is None:
                    logger.warning(f"Failed to get {studio_name} session name: {reserve_table_body_data_div}")
                continue
            class_name = schedule_class_span.get_text().strip()
            if clean_class_name_func is not None:
                class_name = clean_class_name_func(class_name)

            schedule_instruc_span = reserve_table_body_data_div.find(name="span", class_="scheduleInstruc")
            if schedule_instruc_span is None:
                logger.warning(f"Failed to get {studio_name} session instructor: {reserve_table_body_data_div}")
                continue

            schedule_time_span = reserve_table_body_data_div.find(name="span", class_="scheduleTime")
            if schedule_time_span is None:
                logger.warning(f"Failed to get {studio_name} session time: {reserve_table_body_data_div}")
                continue
            schedule_time = schedule_time_span.get_text().strip()
            schedule_time = schedule_time[: schedule_time.find("M") + 1]

            room = reserve_table_body_data_div.get("data-room")
            if room is None:
                logger.warning(f"Failed to get {studio_name} session room: {reserve_table_body_data_div}")
                continue

            try:
                studio = room_id_to_studio_type_map[room]
            except Exception as e:
                logger.warning(f"Failed to get {studio_name} session studio type for room '{room}' - {e}")
                studio = StudioType.Unknown

            try:
                location = room_id_to_studio_location_map[room]
            except Exception as e:
                logger.warning(f"Failed to get {studio_name} session studio location for room '{room}' - {e}")
                location = StudioLocation.Unknown

            class_id = reserve_table_body_data_div.get("data-classid")

            class_details = ClassData(
                studio=studio,
                location=location,
                name=class_name,
                instructor=schedule_instruc_span.get_text().strip(),
                time=schedule_time,
                availability=availability,
                capacity_info=CapacityInfo(),
                class_id=class_id,
            )

            if current_date not in result_dict:
                result_dict[current_date] = [copy(class_details)]
            else:
                result_dict[current_date].append(copy(class_details))

    return result_dict


def get_instructorid_map_from_response_soup(
    logger: logging.Logger,
    soup: BeautifulSoup,
    studio_name: str,
) -> dict[str, str]:
    """
    Parses the response soup to extract the IDs of instructors.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - soup (BeautifulSoup): The parsed HTML response from the schedule request.
      - studio_name (str): Name of studio to use for logging.

    Returns:
      - dict[str, str]: Dictionary of instructor names and IDs.

    """
    reserve_filter = soup.find(name="ul", id="reserveFilter")
    if reserve_filter is None:
        # No classes for the week so there is no instructor filter as well
        return {}

    instructor_filter = reserve_filter.find(name="li", id="reserveFilter1")
    if instructor_filter is None:
        logger.warning(
            f"Failed to get {studio_name} list of instructors - Instructor filter not found: {reserve_filter}"
        )
        return {}

    instructorid_map: dict[str, str] = {}
    for instructor in instructor_filter.find_all(name="li"):
        instructor_name = " ".join(instructor.get_text().strip().lower().split())
        instructor_name = instructor_name.replace("\n", " ")
        if instructor.a is None:
            logger.warning(
                f"Failed to get {studio_name} id of instructor {instructor_name} - A tag is null: {instructor}"
            )
            continue

        href = instructor.a.get("href")
        if href is None:
            logger.warning(
                f"Failed to get {studio_name} id of instructor {instructor_name} - Href is null: {instructor.a}"
            )
            continue

        match = re.search(r"instructorid=(\d+)", href)
        if match is None:
            logger.warning(
                f"Failed to get {studio_name} id of instructor {instructor_name} - Regex failed to match: {href}"
            )
            continue

        instructorid_map[instructor_name] = str(match.group(1))

    return instructorid_map


def get_zingfit_schedule_and_instructorid_map(
    logger: logging.Logger,
    studio_name: str,
    studio_url_subdomain: str,
    table_heading_date_format: str,
    max_weeks: int,
    location_to_site_id_map: dict[StudioLocation, int],
    room_id_to_studio_type_map: dict[str, StudioType],
    room_id_to_studio_location_map: dict[str, StudioLocation],
    clean_class_name_func: Optional[Callable[[str], str]],
) -> tuple[ResultData, dict[str, str]]:
    """
    Retrieves class schedules and instructor ID mappings.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - studio_name (str): Name of studio to use for logging.
      - studio_url_subdomain (str): The subdomain of the studio.
      - table_heading_date_format (str): The date format of the table heading. e.g. "%m.%d"
      - max_weeks (int): Number of weeks to retrieve schedule for.
      - location_to_site_id_map (dict[StudioLocation, int]): Dictionary of studio location and site IDs.
      - room_id_to_studio_type_map (dict[str, StudioType]): The dictionary of room IDs and studio types.
      - room_id_to_studio_location_map (dict[str, StudioType]): The dictionary of room IDs and studio locations.
      - clean_class_name_func (Optional[Callable[[str], str]]): Optional function to format the raw class name string.

    Returns:
      - tuple[ResultData, dict[str, str]]: A tuple containing schedule data and instructor ID mappings.

    """
    result = ResultData()
    instructorid_map: dict[str, str] = {}
    result_lock = threading.Lock()
    instructorid_map_lock = threading.Lock()

    def _get_zingfit_schedule_and_instructorid_map(locations: list[StudioLocation]) -> None:
        """
        Helper to retrieve class schedules and instructor ID mappings. Stores results
        directly in result and instructorid_map objects defined in the main
        get_zingfit_schedule_and_instructorid_map function.

        Args:
          - locations (list[StudioLocation]): List of locations to retrieve schedule for.

        """

        def _get_zingfit_schedule_and_instructorid_map_for_single_week(week: int) -> None:
            """
            Helper to retrieve class schedules and instructor ID mappings for a single
            week. Stores results directly in result and instructorid_map objects defined
            in the main get_zingfit_schedule_and_instructorid_map function.

            Args:
              - week (int): The week number to retrieve the schedule for.

            """
            get_schedule_response = send_get_schedule_request(
                studio_url_subdomain=studio_url_subdomain,
                locations=locations,
                location_to_site_id_map=location_to_site_id_map,
                week=week,
            )
            soup = BeautifulSoup(markup=get_schedule_response.text, features="html.parser")
            get_schedule_response.close()

            # Get schedule
            date_class_data_list_dict = get_schedule_from_response_soup(
                logger=logger,
                soup=soup,
                studio_name=studio_name,
                table_heading_date_format=table_heading_date_format,
                room_id_to_studio_type_map=room_id_to_studio_type_map,
                room_id_to_studio_location_map=room_id_to_studio_location_map,
                clean_class_name_func=clean_class_name_func,
            )
            with result_lock:
                result.add_classes(classes=date_class_data_list_dict)

            # Get instructor id map
            current_instructorid_map = get_instructorid_map_from_response_soup(
                logger=logger, soup=soup, studio_name=studio_name
            )
            with instructorid_map_lock:
                instructorid_map.update(current_instructorid_map)

        # REST API can only select one week at a time
        with ThreadPoolExecutor() as executor:
            executor.map(_get_zingfit_schedule_and_instructorid_map_for_single_week, range(max_weeks))

    locations = list(location_to_site_id_map)
    if len(locations) > 5:
        _get_zingfit_schedule_and_instructorid_map(locations=locations[0:5])
        locations = locations[5:]

    _get_zingfit_schedule_and_instructorid_map(locations=locations)

    return result, instructorid_map
