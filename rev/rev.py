import calendar
import logging
import requests
from bs4 import BeautifulSoup
from common.data_types import ClassAvailability, ClassData, RESPONSE_AVAILABILITY_MAP, ResultData, StudioLocation, StudioType
from copy import copy
from datetime import datetime, timedelta
from rev.data import INSTRUCTORID_MAP, LOCATION_MAP, RESPONSE_LOCATION_TO_STUDIO_LOCATION_MAP

LOGGER = logging.getLogger(__name__)

def send_get_schedule_request(locations: list[StudioLocation], week: int, instructor: str):
    url = 'https://rhythmstudios.zingfit.com/reserve/index.cfm?action=Reserve.chooseClass'
    params = {'wk': week}

    if 'All' in locations:
      params = {**params, **{'site': 2, 'site2': 3, 'site3': 4, 'site4': 5, 'site5': 6}}
    else:
      site_param_name = 'site'
      for location in locations:
        params[site_param_name] = LOCATION_MAP[location]
        if site_param_name == 'site':
          site_param_name = 'site2'
        elif site_param_name != 'site5':
          site_param_name = site_param_name[:-1] + str(int(site_param_name[-1]) + 1)
        else:
          break

    if instructor != 'All':
      params = {**params, **{'instructorid': INSTRUCTORID_MAP[instructor]}}

    return requests.get(url=url, params=params)


def parse_get_schedule_response(response, week: int, days: list[str]) -> dict[datetime.date, list[ClassData]]:
  soup = BeautifulSoup(response.text, 'html.parser')
  reserve_table_list = [table for table in soup.find_all('table') if table.get('id') == 'reserve']
  reserve_table_list_len = len(reserve_table_list)
  if reserve_table_list_len != 1:
    LOGGER.warning(f'Failed to get schedule - Expected 1 reserve table, got {reserve_table_list_len} instead')
    return {}

  reserve_table = reserve_table_list[0]
  if reserve_table.tbody is None:
    return {}

  reserve_table_rows = reserve_table.tbody.find_all('tr')
  reserve_table_rows_len = len(reserve_table_rows)
  if reserve_table_rows_len != 1:
    LOGGER.warning(f'Failed to get schedule - Expected 1 schedule row, got {reserve_table_rows_len} rows instead')
    return {}

  reserve_table_datas = reserve_table_rows[0].find_all('td')
  if len(reserve_table_datas) == 0:
    LOGGER.warning('Failed to get schedule - Table data is null')
    return {}

  # Get yesterday's date and update date at the start of each loop
  current_date = datetime.now().date() + timedelta(weeks=week) - timedelta(days=1)
  result_dict = {}
  for reserve_table_data in reserve_table_datas:
    current_date = current_date + timedelta(days=1)
    if 'All' not in days and calendar.day_name[current_date.weekday()] not in days:
      continue

    result_dict[current_date] = []
    reserve_table_data_div_list = reserve_table_data.find_all('div')
    if len(reserve_table_data_div_list) == 0:
      LOGGER.warning('Failed to get schedule - Table data div is null')
      return {}

    for reserve_table_data_div in reserve_table_data_div_list:
      reserve_table_data_div_class_list = reserve_table_data_div.get('class')
      if len(reserve_table_data_div_class_list) < 2:
        availability = ClassAvailability.Null
      else:
        availability = RESPONSE_AVAILABILITY_MAP[reserve_table_data_div_class_list[1]]

      class_details = ClassData(studio=StudioType.Rev, location=StudioLocation.Null, name='', instructor='', time='', availability=availability)
      for reserve_table_data_div_span in reserve_table_data_div.find_all('span'):
        reserve_table_data_div_span_class_list = reserve_table_data_div_span.get('class')
        if len(reserve_table_data_div_span_class_list) == 0:
          LOGGER.warning('Failed to get schedule - Table data span class is null')
          continue

        reserve_table_data_div_span_class = reserve_table_data_div_span_class_list[0]
        if reserve_table_data_div_span_class == 'scheduleClass':
          schedule_class_str = str(reserve_table_data_div_span.contents[0].strip())
          name_location_split_pos = schedule_class_str.find(' @ ')
          class_name = schedule_class_str[:name_location_split_pos]
          class_details.name = class_name
          class_location_str = schedule_class_str[name_location_split_pos + 3:]
          if class_location_str in RESPONSE_LOCATION_TO_STUDIO_LOCATION_MAP:
            class_details.location = RESPONSE_LOCATION_TO_STUDIO_LOCATION_MAP[class_location_str]
          else:
            class_location_list = [value for key, value in RESPONSE_LOCATION_TO_STUDIO_LOCATION_MAP.items() if key in class_location_str]
            class_details.location = class_location_list[0]
        elif reserve_table_data_div_span_class == 'scheduleInstruc':
          class_details.instructor = str(reserve_table_data_div_span.contents[0].strip())
        elif reserve_table_data_div_span_class == 'scheduleTime':
          class_details.set_time(str(reserve_table_data_div_span.contents[0].strip()))
          result_dict[current_date].append(copy(class_details))

    if len(result_dict[current_date]) == 0:
      result_dict.pop(current_date)

  return result_dict

def get_rev_schedule(locations: list[StudioLocation], weeks: int, days: str, instructors: list[str]) -> ResultData:
  result = ResultData()
  # REST API can only select one instructor at a time
  for instructor in instructors:
    # REST API can only select one week at a time
    for week in range(0, weeks):
      get_schedule_response = send_get_schedule_request(locations=locations, instructor=instructor, week=week)
      date_class_data_list_dict = parse_get_schedule_response(get_schedule_response, week=week, days=days)
      result.add_classes(date_class_data_list_dict)

  return result
