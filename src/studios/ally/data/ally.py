"""
ally.py
Author: https://github.com/lendrixxx
Description: This file contains data used for retrieving Ally schedules.
"""

from common.studio_location import StudioLocation
from common.studio_type import StudioType

# Max number of days that schedule is shown in advance
MAX_SCHEDULE_DAYS = 14

# Dictionary of room IDs and studio types
ROOM_ID_TO_STUDIO_TYPE_MAP = {
    "875a0965-6e22-4933-a1ab-cb15e23c32ad": StudioType.AllySpin,  # Cross Street Ride
    "d7e0eb9c-15f1-47e6-a35e-9909e7f73e1b": StudioType.AllyPilates,  # Cross Street Reformer Room 1
    "059778e5-2907-49e6-949a-0cc55ddacbc3": StudioType.AllyPilates,  # Cross Street Reformer Room 2
    "77462133-8166-4b53-b07c-061994a5a948": StudioType.AllyPilates,  # Cross Street Chair Pilates
    "7e03d6bb-9f2d-4dfd-84b4-5636541be9bb": StudioType.AllyRecovery,  # Cross Street Recovery Suite
    "ecb1b343-d997-4c2c-a7b0-a65bff47fe81": StudioType.AllySpin,  # Maxwell Ride
    "90975b8f-fa0e-4296-80a9-6064f27206df": StudioType.AllyPilates,  # Maxwell Reformer
    "a2e91a49-b932-441e-a055-c620ca8a3ab5": StudioType.AllyRecovery,  # Maxwell Recovery Suite
}

# Dictionary of room IDs and studio locations
ROOM_ID_TO_STUDIO_LOCATION_MAP = {
    "875a0965-6e22-4933-a1ab-cb15e23c32ad": StudioLocation.CrossStreet,  # Cross Street Ride
    "d7e0eb9c-15f1-47e6-a35e-9909e7f73e1b": StudioLocation.CrossStreet,  # Cross Street Reformer Room 1
    "059778e5-2907-49e6-949a-0cc55ddacbc3": StudioLocation.CrossStreet,  # Cross Street Reformer Room 2
    "77462133-8166-4b53-b07c-061994a5a948": StudioLocation.CrossStreet,  # Cross Street Chair Pilates
    "7e03d6bb-9f2d-4dfd-84b4-5636541be9bb": StudioLocation.CrossStreet,  # Cross Street Recovery Suite
    "ecb1b343-d997-4c2c-a7b0-a65bff47fe81": StudioLocation.Maxwell,  # Maxwell Ride
    "90975b8f-fa0e-4296-80a9-6064f27206df": StudioLocation.Maxwell,  # Maxwell Reformer
    "a2e91a49-b932-441e-a055-c620ca8a3ab5": StudioLocation.Maxwell,  # Maxwell Recovery Suite
}


# Function to clean class names
def clean_class_name(class_name: str) -> str:
    """
    Removes known location suffixes from a class name.
    """
    return class_name.replace(" (CROSS STREET)", "").replace(" (MAXWELL)", "")
