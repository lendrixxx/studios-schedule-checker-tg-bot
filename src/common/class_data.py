"""
class_data.py
Author: https://github.com/lendrixxx
Description: This file defines the ClassData class used to store the details of a single class.
"""

from dataclasses import dataclass
from datetime import datetime

from common.capacity_info import CapacityInfo
from common.class_availability import ClassAvailability
from common.studio_location import StudioLocation
from common.studio_type import StudioType


@dataclass
class ClassData:
    """
    Class to represent a single class's details including studio, location, instructor,
    time, availability, and capacity.

    Attributes:
      - studio (StudioType): Type of the studio.
      - location (StudioLocation): Location of the studio.
      - name (str): Name of the class.
      - instructor (str): Name of the instructor.
      - time (str): Scheduled time of the class.
      - availability (ClassAvailability): Availability status of the class.
      - capacity_info (CapacityInfo): Capacity information of the class.
      - class_id (str): ID of the class.

    """

    studio: StudioType
    location: StudioLocation
    name: str
    instructor: str
    time: str
    availability: ClassAvailability
    capacity_info: CapacityInfo
    class_id: str

    def __init__(
        self,
        studio: StudioType,
        location: StudioLocation,
        name: str,
        instructor: str,
        time: str,
        availability: ClassAvailability,
        capacity_info: CapacityInfo,
        class_id: str = "",
    ) -> None:
        """
        Initializes the ClassData instance.

        Args:
          - studio (StudioType): The type of the studio.
          - location (StudioLocation): The location of the studio.
          - name (str): The name of the class.
          - instructor (str): The name of the instructor.
          - time (str): The scheduled time of the class.
          - availability (ClassAvailability): The availability status of the class.
          - capacity_info (CapacityInf): The capacity information of the class.
          - class_id (str): The ID of the class.

        """
        self.studio = studio
        self.location = location
        self.name = name.replace("*", r"\*").replace("_", r"\_").replace("`", r"\`")
        self.instructor = instructor
        self.time = time
        self.availability = availability
        self.capacity_info = capacity_info
        self.class_id = class_id

    def __eq__(self, other: object) -> bool:
        """
        Equality check between the ClassData and another object. Only checks studio,
        location, class name, instructor, and time.

        Args:
          - other (object): The other object to compare.

        Returns:
          bool: True if both objects are equal, false otherwise.

        """
        if not isinstance(other, ClassData):
            return False

        return (
            self.studio == other.studio
            and self.location == other.location
            and self.name == other.name
            and self.instructor == other.instructor
            and self.time == other.time
            and self.class_id == other.class_id
        )

    def __lt__(self, other: "ClassData") -> bool:
        """
        Comparison between two ClassData objects with the following priority:
        Time, studio, location, instructor, class name, availability, capacity info

        Args:
          - other (ClassData): The other ClassData object to compare.

        Returns:
          bool: True if the current object's is less than the other, false otherwise.

        """
        self_key = (
            datetime.strptime(self.time, "%I:%M %p"),
            self.studio,
            self.location,
            self.instructor,
            self.name,
            self.availability,
            self.capacity_info,
        )
        other_key = (
            datetime.strptime(other.time, "%I:%M %p"),
            other.studio,
            other.location,
            other.instructor,
            other.name,
            other.availability,
            other.capacity_info,
        )
        return self_key < other_key

    def get_string(self, include_availability: bool, include_capacity_info: bool) -> str:
        availability_str = ""
        if include_availability:
            if self.availability == ClassAvailability.Waitlist:
                availability_str = "[W] "
            elif self.availability == ClassAvailability.Full:
                availability_str = "[F] "
            elif self.availability == ClassAvailability.Cancelled:
                availability_str = "[Cancelled] "

        result_str = ""
        if self.location == StudioLocation.Null:
            result_str += f"*{availability_str + self.time}* - " f"{self.name} ({self.instructor})"
        else:
            result_str += (
                f"*{availability_str + self.time}* - {self.name} " f"@ {self.location.value} ({self.instructor})"
            )

        if include_capacity_info:
            if self.capacity_info.has_info:
                if self.availability == ClassAvailability.Waitlist:
                    result_str += f" - {self.capacity_info.waitlist_reserved} Member(s) on Waitlist"
                else:
                    result_str += f" - {self.capacity_info.remaining} Spot(s) Remaining"

        if self.class_id != "":
            result_str += f" `{self.class_id}`"

        return result_str
