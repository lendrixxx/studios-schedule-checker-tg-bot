"""
hapana.py
Author: https://github.com/lendrixxx
Description:
  This file defines functions to handle the retrieving of class schedules and instructor IDs for Hapana studios.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import pytz
import requests

from common.capacity_info import CapacityInfo
from common.class_data import ClassData
from common.data import RESPONSE_AVAILABILITY_MAP
from common.result_data import ResultData
from common.studio_location import StudioLocation
from common.studio_type import StudioType


def send_get_schedule_request(
    location: StudioLocation,
    start_date: date,
    end_date: datetime,
    security_token: str,
    location_to_site_id_map: dict[str, str],
) -> requests.models.Response:
    """
    Sends a GET request to retrieve the class schedule for the specified locations and
    week.

    Args:
      - location (StudioLocation): The studio location to retrieve the schedule for.
      - start_date (date): The start date to retrieve the schedule for.
      - end_date (date): The end date to retrieve the schedule for.
      - security_token (str): Security token used for sending requests.
      - location_to_site_id_map (dict[str, str]): Dictionary of location and site IDs.

    Returns:
      - requests.models.Response: The response object containing the schedule data.

    """
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    url = "https://widgetapi.hapana.com/v2/wAPI/site/sessions"
    params = {
        "sessionCategory": "classes",
        "siteID": location_to_site_id_map[location],
        "startDate": start_date_str,
        "endDate": end_date_str,
    }
    headers = {
        "Content-Type": "application/json",
        "Securitytoken": security_token,
    }
    return requests.get(url=url, params=params, headers=headers)


def parse_get_schedule_response(
    logger: logging.Logger,
    studio_name: str,
    response: requests.models.Response,
    room_id_to_studio_type_map: dict[str, StudioType],
    room_name_to_studio_location_map: dict[str, StudioLocation],
    location: StudioLocation,
    location_to_site_id_map: dict[str, str],
) -> dict[date, list[ClassData]]:
    """
    Parses the get schedule response to extract the class schedule data.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - studio_name (str): Name of studio to use for logging.
      - response (requests.models.Response): The get schedule response from the schedule request.
      - room_id_to_studio_type_map (dict[str, StudioType]): The dictionary of room IDs and studio types.
      - room_name_to_studio_location_map (dict[str, StudioLocation]):
        The dictionary of room name strings and studio locations.
      - location (StudioLocation): The studio location to retrieve the schedule for.
      - location_to_site_id_map (dict[str, str]): Dictionary of location and site IDs.

    Returns:
      - dict[date, list[ClassData]]: Dictionary of dates and details of classes.

    """
    if response.status_code != 200:
        logger.warning(f"Failed to get {studio_name} schedule - API callback error {response.status_code}")
        return {}

    result_dict = {}
    try:
        response_json = response.json()
        if "success" not in response_json:
            logger.warning(f"Failed to get {studio_name} schedule - API callback failed: {response_json}")
            return {}
    except Exception as e:
        logger.warning(f"Failed to get {studio_name} schedule - {e}: {response.text}")
        return {}

    for data in response_json["data"]:
        try:
            if data["sessionStatus"] == "complete":
                continue

            class_date_str = data["sessionDate"]
            class_date = datetime.strptime(class_date_str, "%Y-%m-%d").date()
            instructors = []
            for instructorData in data["instructorData"]:
                instructors.append(instructorData["instructorName"])
            instructor_str = " / ".join(instructors)

            class_name = data["sessionName"]
            class_name_location_split_pos = class_name.find(" @ ")
            cleaned_class_name = class_name[:class_name_location_split_pos]
            class_time = datetime.strptime(data["startTime"], "%H:%M:%S")
            class_time_str = class_time.strftime("%I:%M %p").lstrip("0")

            room_name = data["roomName"]
            if room_name in room_id_to_studio_type_map:
                studio = room_id_to_studio_type_map[room_name]
            else:
                logger.warning(
                    f"Failed to map room name '{room_name}' to studio type for {studio_name}: "
                    f"Class name: {class_name}, Instructor: {instructor_str}, Time: {class_time_str}"
                )
                studio = StudioType.Unknown

            class_id = ""
            if room_name in room_name_to_studio_location_map:
                location = room_name_to_studio_location_map[room_name]
                class_id = f"{data['sessionID']}|{location_to_site_id_map[location]}|{class_date_str}"
            else:
                logger.warning(
                    f"Failed to map room name '{room_name}' to studio location for {studio_name}: "
                    f"Class name: {class_name}, Instructor: {instructor_str}, Time: {class_time_str}"
                )
                location = StudioLocation.Unknown
                cleaned_class_name += " @ " + room_name

            class_details = ClassData(
                studio=studio,
                location=location,
                name=cleaned_class_name,
                instructor=instructor_str,
                time=class_time_str,
                availability=RESPONSE_AVAILABILITY_MAP[data["sessionStatus"]],
                capacity_info=CapacityInfo(
                    has_info=True,
                    capacity=data["capacity"],
                    remaining=data["remaining"],
                    waitlist_capacity=data["waitlistCapacity"],
                    waitlist_reserved=data["waitlistReserved"],
                ),
                class_id=class_id,
            )

            if class_date not in result_dict:
                result_dict[class_date] = [class_details]
            else:
                result_dict[class_date].append(class_details)

        except Exception as e:
            logger.warning(f"Failed to get details of class for {studio_name} - {e}. Data: {data}")

    return result_dict


def get_hapana_schedule(
    logger: logging.Logger,
    studio_name: str,
    security_token: str,
    location_to_site_id_map: dict[str, str],
    room_id_to_studio_type_map: dict[str, StudioType],
    room_name_to_studio_location_map: dict[str, StudioLocation],
) -> ResultData:
    """
    Retrieves all the available class schedules.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - studio_name (str): Name of studio to use for logging.
      - security_token (str): Security token used for sending requests.
      - location_to_site_id_map (dict[str, str]): Dictionary of location strings and site IDs.
      - room_id_to_studio_type_map (dict[str, StudioType]): The dictionary of room IDs and studio types.
      - room_name_to_studio_location_map (dict[str, StudioLocation]):
        The dictionary of room name strings and studio locations.

    Returns:
      - ResultData: The schedule data.

    """
    start_date = datetime.now(tz=pytz.timezone("Asia/Singapore"))
    end_date = start_date + timedelta(weeks=4)  # Rev schedule only shows up to 4 weeks in advance
    result = ResultData()
    result_lock = threading.Lock()

    def _get_hapana_schedule_for_single_location(location: str) -> None:
        """
        Helper to retrieve schedule for a single location. Stores results directly in
        result object defined in the main get_hapana_schedule function.

        Args:
          - location (str): The location to retrieve the schedule for.

        """
        get_schedule_response = send_get_schedule_request(
            location=location,
            start_date=start_date,
            end_date=end_date,
            security_token=security_token,
            location_to_site_id_map=location_to_site_id_map,
        )
        date_class_data_list_dict = parse_get_schedule_response(
            logger=logger,
            studio_name=studio_name,
            response=get_schedule_response,
            room_id_to_studio_type_map=room_id_to_studio_type_map,
            room_name_to_studio_location_map=room_name_to_studio_location_map,
            location=location,
            location_to_site_id_map=location_to_site_id_map,
        )
        get_schedule_response.close()
        with result_lock:
            result.add_classes(classes=date_class_data_list_dict)

    # REST API can only select one location at a time
    with ThreadPoolExecutor() as executor:
        executor.map(_get_hapana_schedule_for_single_location, ["Bugis", "Orchard", "TJPG"])

    return result


def get_instructorid_map(
    logger: logging.Logger,
    studio_name: str,
    security_token: str,
    location_to_site_id_map: dict[str, str],
) -> dict[str, str]:
    """
    Retrieves the IDs of instructors.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - studio_name (str): Name of studio to use for logging.
      - security_token (str): Security token used for sending requests.
      - location_to_site_id_map (dict[str, str]): Dictionary of location strings and site IDs.

    Returns:
      - dict[str, str]: Dictionary of instructor names and IDs.

    """
    url = "https://widgetapi.hapana.com/v2/wAPI/site/instructor"
    headers = {
        "Content-Type": "application/json",
        "Securitytoken": security_token,
    }

    instructorid_map: dict[str, str] = {}
    instructorid_map_lock = threading.Lock()

    def _get_hapana_instructorid_map_for_single_location(location: str) -> None:
        """
        Helper to retrieve IDs of instructors for a single location. Stores results
        directly in result object defined in the main get_instructorid_map function.

        Args:
          - location (str): The location to retrieve IDs for.

        """
        params = {"siteID": location_to_site_id_map[location]}
        response = requests.get(url=url, params=params, headers=headers)
        if response.status_code != 200:
            logger.warning(
                f"Failed to get {studio_name} list of instructors for {location} - "
                f"API callback error {response.status_code}"
            )
            return

        try:
            response_json = response.json()
            if not response_json["success"]:
                logger.warning(
                    f"Failed to get {studio_name} list of instructors for {location} - "
                    f"API callback failed: {response_json}"
                )
                return

            with instructorid_map_lock:
                for data in response_json["data"]:
                    instructorid_map[data["instructorName"].lower()] = data["instructorID"]

        except Exception as e:
            logger.warning(f"Failed to get {studio_name} list of instructors for {location} - {e}")
            return

    # REST API can only select one location at a time
    with ThreadPoolExecutor() as executor:
        executor.map(_get_hapana_instructorid_map_for_single_location, location_to_site_id_map.keys())

    return instructorid_map


def get_hapana_schedule_and_instructorid_map(
    logger: logging.Logger,
    studio_name: str,
    security_token: str,
    location_to_site_id_map: dict[str, str],
    room_id_to_studio_type_map: dict[str, StudioType],
    room_name_to_studio_location_map: dict[str, StudioLocation],
) -> tuple[ResultData, dict[str, str]]:
    """
    Retrieves class schedules and instructor ID mappings.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - studio_name (str): Name of studio to use for logging.
      - security_token (str): Security token used for sending requests.
      - location_to_site_id_map (dict[str, str]): Dictionary of location strings and site IDs.
      - room_id_to_studio_type_map (dict[str, StudioType]): The dictionary of room IDs and studio types.
      - room_name_to_studio_location_map (dict[str, StudioLocation]):
        The dictionary of room name strings and studio locations.

    Returns:
      - tuple[ResultData, dict[str, str]]: A tuple containing schedule data and instructor ID mappings.

    """
    return (
        get_hapana_schedule(
            logger=logger,
            studio_name=studio_name,
            security_token=security_token,
            location_to_site_id_map=location_to_site_id_map,
            room_id_to_studio_type_map=room_id_to_studio_type_map,
            room_name_to_studio_location_map=room_name_to_studio_location_map,
        ),
        get_instructorid_map(
            logger=logger,
            studio_name=studio_name,
            security_token=security_token,
            location_to_site_id_map=location_to_site_id_map,
        ),
    )


def get_hapana_security_token(logger: logging.Logger, studio_name: str, site_id: str) -> str:
    """
    Retrieves security token to be used for sending requests.

    Args:
      - logger (logging.Logger): Logger for logging messages.
      - studio_name (str): Name of studio to use for logging.
      - site_id (str): ID of site to retrieve security token for.

    Returns:
      - str: Security token to be used for sending requests.

    """
    url = "https://widgetapi.hapana.com/v2/wAPI/site/settings"
    headers = {"wID": site_id}
    response = requests.get(url=url, headers=headers)

    if response.status_code != 200:
        logger.warning(f"Failed to get {studio_name} security token - API callback error {response.status_code}")
        return ""

    try:
        response_json = response.json()
    except Exception as e:
        logger.warning(f"Failed to get {studio_name} security token - {e}: {response.text}")
        return ""

    if "securityToken" not in response_json:
        logger.warning(
            f"Failed to get {studio_name} security token - 'securityToken' not found in response: {response_json}"
        )
        return ""

    security_token = response_json["securityToken"]
    logger.info(f"Successfully retrieved {studio_name} security token!")
    return security_token
