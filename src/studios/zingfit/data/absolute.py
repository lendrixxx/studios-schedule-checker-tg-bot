"""
absolute.py
Author: https://github.com/lendrixxx
Description: This file contains data used for retrieving Absolute schedules.
"""

from common.studio_location import StudioLocation
from common.studio_type import StudioType

# URL subdomain
URL_SUBDOMAIN = "absoluteboutiquefitness"

# Max number of weeks that schedule is shown in advance
MAX_SCHEDULE_WEEKS = 2

# Date format of the table heading
TABLE_HEADING_DATE_FORMAT = "%d.%m"

# Dictionary of studio locations and site id params used in get request
LOCATION_TO_SITE_ID_MAP = {
    StudioLocation.Centrepoint: 1,
    StudioLocation.StarVista: 2,
    StudioLocation.MilleniaWalk: 3,
    StudioLocation.i12: 5,
    StudioLocation.GreatWorld: 6,
    StudioLocation.Raffles: 8,
}

# Dictionary of room IDs and studio types
ROOM_ID_TO_STUDIO_TYPE_MAP = {
    "2318746084081403485": StudioType.AbsolutePilates,  # Centrepoint Wunda Chair
    "831322535101466334": StudioType.AbsolutePilates,  # Centrepoint Reformer Room 1
    "1180495114737288579": StudioType.AbsolutePilates,  # Centrepoint Reformer Room 2
    "816664672039076934": StudioType.AbsoluteSpin,  # Centrepoint Ride
    "831322688713656132": StudioType.AbsolutePilates,  # i12 Reformer Room 1
    "2049314421699774164": StudioType.AbsolutePilates,  # i12 Reformer Room 2
    "1120160541927540298": StudioType.AbsoluteSpin,  # i12 Ride
    "1666936824318133997": StudioType.AbsolutePilates,  # Star Vista Reformer
    "831321640959739033": StudioType.AbsoluteSpin,  # Star Vista Ride
    "2062965464820090493": StudioType.AbsolutePilates,  # Raffles Place Reformer Room 1
    "2062965605622876053": StudioType.AbsolutePilates,  # Raffles Place Reformer Room 2
    "2062965745611965609": StudioType.AbsoluteSpin,  # Raffles Place Ride
    "1973969112329618498": StudioType.AbsolutePilates,  # Great World Reformer
    "979675880630519234": StudioType.AbsoluteSpin,  # Millenia Walk Ride
    "2490861537367951014": StudioType.AbsolutePilates,  # Millenia Walk Pilates
}

# Dictionary of room IDs and studio locations
ROOM_ID_TO_STUDIO_LOCATION_MAP = {
    "2318746084081403485": StudioLocation.Centrepoint,  # Centrepoint Wunda Chair
    "831322535101466334": StudioLocation.Centrepoint,  # Centrepoint Reformer Room 1
    "1180495114737288579": StudioLocation.Centrepoint,  # Centrepoint Reformer Room 2
    "816664672039076934": StudioLocation.Centrepoint,  # Centrepoint Ride
    "831322688713656132": StudioLocation.i12,  # i12 Reformer Room 1
    "2049314421699774164": StudioLocation.i12,  # i12 Reformer Room 2
    "1120160541927540298": StudioLocation.i12,  # i12 Ride
    "1666936824318133997": StudioLocation.StarVista,  # Star Vista Reformer
    "831321640959739033": StudioLocation.StarVista,  # Star Vista Ride
    "2062965464820090493": StudioLocation.Raffles,  # Raffles Place Reformer Room 1
    "2062965605622876053": StudioLocation.Raffles,  # Raffles Place Reformer Room 2
    "2062965745611965609": StudioLocation.Raffles,  # Raffles Place Ride
    "1973969112329618498": StudioLocation.GreatWorld,  # Great World Reformer
    "979675880630519234": StudioLocation.MilleniaWalk,  # Millenia Walk Ride
    "2490861537367951014": StudioLocation.MilleniaWalk,  # Millenia Walk Pilates
}
