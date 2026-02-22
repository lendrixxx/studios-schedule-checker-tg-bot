"""
result_data.py
Author: https://github.com/lendrixxx
Description:
  This file defines the ResultData class used to store class schedules and
  provide functionality for filtering classes based on various query parameters.
"""

from __future__ import annotations

import calendar
from copy import copy
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import pytz

from common.class_data import ClassData
from common.query_data import QueryData
from common.studio_location import StudioLocation
from common.studio_type import StudioType


class ResultData:
    """
    Class to represent the data for class schedules of various studios.

    Attributes:
      - classes (dict[date, list[ClassData]]): Dictionary of dates and details of classes.

    """

    classes: dict[date, list[ClassData]]

    def __init__(self, classes: Optional[dict[date, list[ClassData]]] = None) -> None:
        """
        Initializes the ResultData instance.

        Args:
          - classes (dict[date, list[ClassData]]): The dictionary of dates and details of classes.

        """
        self.classes = {} if classes is None else classes

    def add_classes(self, classes: dict[date, list[ClassData]]) -> None:
        """
        Adds classes to the given date.

        Args:
          - classes (dict[date, list[ClassData]]): The dictionary of dates and details of classes to add.

        """
        if classes is None:
            return

        for classes_date in classes:
            if classes_date in self.classes:
                self.classes[classes_date].extend(classes[classes_date])
            else:
                self.classes[classes_date] = copy(classes[classes_date])

    def get_data(self, query: QueryData) -> ResultData:
        """
        Filters and retrieves class data based on the provided query parameters.

        Args:
          - query (QueryData): The query parameters for filtering class data.

        Returns:
          ResultData: A new ResultData instance containing the filtered class data.

        """
        if len(self.classes) == 0:
            return ResultData()

        classes: dict[date, list[ClassData]] = {}
        current_sg_time = datetime.now(tz=pytz.timezone("Asia/Singapore"))
        current_sg_date = current_sg_time.date()
        for week in range(0, query.weeks):
            date_to_check = current_sg_date + timedelta(weeks=week)
            for day in range(7):
                if "All" not in query.days and calendar.day_name[date_to_check.weekday()] not in query.days:
                    date_to_check = date_to_check + timedelta(days=1)
                    continue

                if date_to_check in self.classes:
                    for class_details in self.classes[date_to_check]:
                        if class_details.studio not in query.studios:
                            continue

                        if (
                            query.class_name_filter != ""
                            and query.class_name_filter.lower() not in class_details.name.lower()
                        ):
                            continue

                        query_locations = query.get_studio_locations(class_details.studio)
                        if StudioLocation.All not in query_locations and class_details.location not in query_locations:
                            continue

                        is_by_instructor = (
                            "All" in query.studios[class_details.studio].instructors
                            or class_details.studio == StudioType.AllyRecovery
                            or any(
                                instructor.lower() == class_details.instructor.lower()
                                for instructor in query.studios[class_details.studio].instructors
                            )
                            or any(
                                instructor.lower() in class_details.instructor.lower().split(" ")
                                for instructor in query.studios[class_details.studio].instructors
                            )
                            or any(
                                instructor.lower() == class_details.instructor.lower().split(".")[0]
                                for instructor in query.studios[class_details.studio].instructors
                            )
                        )
                        if not is_by_instructor:
                            continue

                        class_time = datetime.strptime(class_details.time, "%I:%M %p")
                        if week == 0 and day == 0:  # Skip classes that have already ended
                            if (
                                current_sg_time.hour > class_time.hour
                                or current_sg_time.hour == class_time.hour
                                and current_sg_time.minute > class_time.minute
                            ):
                                continue

                        if len(query.start_times) > 0:
                            within_start_times = False
                            for start_time_from, start_time_to in query.start_times:
                                class_time_within_query_time_from = (
                                    class_time.hour > start_time_from.hour
                                    or class_time.hour == start_time_from.hour
                                    and class_time.minute >= start_time_from.minute
                                )
                                class_time_within_query_time_to = (
                                    class_time.hour < start_time_to.hour
                                    or class_time.hour == start_time_to.hour
                                    and class_time.minute <= start_time_to.minute
                                )
                                if class_time_within_query_time_from and class_time_within_query_time_to:
                                    within_start_times = True
                                    break

                            if not within_start_times:
                                continue

                        classes.setdefault(date_to_check, []).append(class_details)
                date_to_check = date_to_check + timedelta(days=1)

        result = ResultData(classes)
        return result

    def get_result_str(self) -> str:
        """
        Returns a formatted string of the classes.

        Returns:
          str: A string representing the classes.

        """
        if len(self.classes) == 0:
            return "No classes found"

        result_str = ""
        for classes_date in sorted(self.classes):
            date_str = f"*{calendar.day_name[classes_date.weekday()]}, {classes_date.strftime('%d %B')}*"
            result_str += f"{date_str}\n"

            for class_details in sorted(self.classes[classes_date]):
                result_str += class_details.get_string(include_availability=True, include_capacity_info=True)
                result_str += "\n"
            result_str += "\n"

        return result_str

    def get_class_data(self, class_id: str, class_date: Optional[date]) -> Optional[Tuple[date, ClassData]]:
        for current_class_date, class_datas in self.classes.items():
            if class_date is not None:
                if class_date != current_class_date:
                    continue

            for class_data in class_datas:
                if class_data.class_id == class_id:
                    return current_class_date, copy(class_data)
        return None

    def __add__(self, other: ResultData) -> ResultData:
        """
        Merges two ResultData instances.

        Args:
          - other (ResultData): The other ResultData object to add.

        Returns:
          ResultData: The combined ResultData instance.

        """
        result = self
        result.add_classes(classes=other.classes)
        return result
