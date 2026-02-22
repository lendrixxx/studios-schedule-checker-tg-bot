"""
test_zingfit.py
Author: https://github.com/lendrixxx
Description: This file tests the functions to retrieve information for Zingfit.
"""

import logging
from datetime import date
from typing import Callable, NamedTuple, Optional

import pytest
import pytest_mock
from bs4 import BeautifulSoup

from common.capacity_info import CapacityInfo
from common.class_availability import ClassAvailability
from common.class_data import ClassData
from common.studio_location import StudioLocation
from common.studio_type import StudioType
from studios.zingfit.data.absolute import LOCATION_TO_SITE_ID_MAP as ABSOLUTE_LOCATION_TO_SITE_ID_MAP
from studios.zingfit.data.absolute import MAX_SCHEDULE_WEEKS as ABSOLUTE_MAX_WEEKS
from studios.zingfit.data.absolute import ROOM_ID_TO_STUDIO_LOCATION_MAP as ABSOLUTE_ROOM_ID_TO_STUDIO_LOCATION_MAP
from studios.zingfit.data.absolute import ROOM_ID_TO_STUDIO_TYPE_MAP as ABSOLUTE_ROOM_ID_TO_STUDIO_TYPE_MAP
from studios.zingfit.data.absolute import TABLE_HEADING_DATE_FORMAT as ABSOLUTE_TABLE_HEADING_DATE_FORMAT
from studios.zingfit.data.absolute import URL_SUBDOMAIN as ABSOLUTE_URL_SUBDOMAIN
from studios.zingfit.zingfit import (
    get_instructorid_map_from_response_soup,
    get_schedule_from_response_soup,
    get_zingfit_schedule_and_instructorid_map,
    send_get_schedule_request,
)
from tests.conftest import is_classes_dict_equal
from tests.studios.zingfit.expected_results import (
    absolute_expected_results,
)


class GetScheduleTestArgs(NamedTuple):
    response_file_name: str
    table_heading_date_format: str
    room_id_to_studio_type_map: dict[str, StudioType]
    room_id_to_studio_location_map: dict[str, StudioLocation]
    clean_class_name_func: Optional[Callable[[str], str]]
    expected_result: dict[date, ClassData]


class GetInstructorIDTestArgs(NamedTuple):
    response_file_name: str
    expected_result: dict[str, str]


def test_send_get_schedule_request_single_location(mocker: pytest_mock.plugin.MockerFixture) -> None:
    """
    Test send_get_schedule_request with a single location flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """
    # Setup mocks
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200

    # Call the function to test
    location_to_site_id_map = {StudioLocation.Centrepoint: 1}
    locations = list(location_to_site_id_map)
    week = 1
    response = send_get_schedule_request(
        studio_url_subdomain=ABSOLUTE_URL_SUBDOMAIN,
        locations=locations,
        location_to_site_id_map=location_to_site_id_map,
        week=week,
    )

    # Assert that flow was called with the expected arguments
    mock_get.assert_called_once_with(
        url=f"https://{ABSOLUTE_URL_SUBDOMAIN}.zingfit.com/reserve/index.cfm",
        params={
            "wk": week,
            "site": location_to_site_id_map[locations[0]],
            "action": "Reserve.chooseClass",
        },
    )
    assert response.status_code == 200


def test_send_get_schedule_request_multiple_locations(mocker: pytest_mock.plugin.MockerFixture) -> None:
    """
    Test send_get_schedule_request with multiple locations flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """
    # Setup mocks
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200

    # Call the function to test
    location_to_site_id_map = {
        StudioLocation.Centrepoint: 1,
        StudioLocation.StarVista: 2,
        StudioLocation.MilleniaWalk: 3,
        StudioLocation.i12: 5,
        StudioLocation.GreatWorld: 6,
    }
    locations = list(location_to_site_id_map)
    week = 2
    response = send_get_schedule_request(
        studio_url_subdomain=ABSOLUTE_URL_SUBDOMAIN,
        locations=locations,
        location_to_site_id_map=location_to_site_id_map,
        week=week,
    )

    # Assert that flow was called with the expected arguments
    mock_get.assert_called_once_with(
        url=f"https://{ABSOLUTE_URL_SUBDOMAIN}.zingfit.com/reserve/index.cfm",
        params={
            "wk": week,
            "site": location_to_site_id_map[locations[0]],
            "site2": location_to_site_id_map[locations[1]],
            "site3": location_to_site_id_map[locations[2]],
            "site4": location_to_site_id_map[locations[3]],
            "site5": location_to_site_id_map[locations[4]],
            "action": "Reserve.chooseClass",
        },
    )
    assert response.status_code == 200


def test_send_get_schedule_request_multiple_locations_exceeded(mocker: pytest_mock.plugin.MockerFixture) -> None:
    """
    Test send_get_schedule_request with multiple locations exceeding number allowed by
    API flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """
    # Setup mocks
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200

    # Call the function to test
    location_to_site_id_map = {
        StudioLocation.Centrepoint: 1,
        StudioLocation.StarVista: 2,
        StudioLocation.MilleniaWalk: 3,
        StudioLocation.i12: 5,
        StudioLocation.GreatWorld: 6,
        StudioLocation.Raffles: 7,  # Entry should be ignored. API takes at most 5 locations
        StudioLocation.Robinson: 8,  # Entry should be ignored. API takes at most 5 locations
    }
    locations = list(location_to_site_id_map)
    week = 2
    response = send_get_schedule_request(
        studio_url_subdomain=ABSOLUTE_URL_SUBDOMAIN,
        locations=locations,
        location_to_site_id_map=location_to_site_id_map,
        week=week,
    )

    # Assert that flow was called with the expected arguments
    mock_get.assert_called_once_with(
        url=f"https://{ABSOLUTE_URL_SUBDOMAIN}.zingfit.com/reserve/index.cfm",
        params={
            "wk": week,
            "site": location_to_site_id_map[locations[0]],
            "site2": location_to_site_id_map[locations[1]],
            "site3": location_to_site_id_map[locations[2]],
            "site4": location_to_site_id_map[locations[3]],
            "site5": location_to_site_id_map[locations[4]],
            "action": "Reserve.chooseClass",
        },
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            GetScheduleTestArgs(
                response_file_name="absolute_raffles_6_to_12_apr.html",
                table_heading_date_format=ABSOLUTE_TABLE_HEADING_DATE_FORMAT,
                room_id_to_studio_type_map=ABSOLUTE_ROOM_ID_TO_STUDIO_TYPE_MAP,
                room_id_to_studio_location_map=ABSOLUTE_ROOM_ID_TO_STUDIO_LOCATION_MAP,
                clean_class_name_func=None,
                expected_result=absolute_expected_results.EXPECTED_RAFFLES_6_TO_12_APR_SCHEDULE,
            ),
            id="Absolute Raffles 6 to 12 April",
        ),
    ],
)
def test_get_schedule_from_response_soup_single_location(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
    args: GetScheduleTestArgs,
) -> None:
    """
    Test get_schedule_from_response_soup with a single location flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.
      - args (GetScheduleTestArgs): Provides arguments for the test case.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file(args.response_file_name), features="html.parser")

    # Call the function to test
    result = get_schedule_from_response_soup(
        logger=mock_logger,
        soup=mock_soup,
        studio_name="test studio",
        table_heading_date_format=args.table_heading_date_format,
        room_id_to_studio_type_map=args.room_id_to_studio_type_map,
        room_id_to_studio_location_map=args.room_id_to_studio_location_map,
        clean_class_name_func=args.clean_class_name_func,
    )

    # Assert that the response is as expected
    assert is_classes_dict_equal(
        expected=args.expected_result,
        actual=result,
    )


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            GetScheduleTestArgs(
                response_file_name="absolute_milleniawalk_and_i12_7_to_12_apr.html",
                table_heading_date_format=ABSOLUTE_TABLE_HEADING_DATE_FORMAT,
                room_id_to_studio_type_map=ABSOLUTE_ROOM_ID_TO_STUDIO_TYPE_MAP,
                room_id_to_studio_location_map=ABSOLUTE_ROOM_ID_TO_STUDIO_LOCATION_MAP,
                clean_class_name_func=None,
                expected_result=absolute_expected_results.EXPECTED_MW_AND_I12_7_TO_12_APR_SCHEDULE,
            ),
            id="Absolute Millenia Walk and i12 7 to 12 April",
        ),
    ],
)
def test_get_schedule_from_response_soup_multiple_locations(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
    args: GetScheduleTestArgs,
) -> None:
    """
    Test get_schedule_from_response_soup with multiple locations flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.
      - args (GetScheduleTestArgs): Provides arguments for the test case.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file(args.response_file_name), features="html.parser")

    # Call the function to test
    result = get_schedule_from_response_soup(
        logger=mock_logger,
        soup=mock_soup,
        studio_name="test studio",
        table_heading_date_format=args.table_heading_date_format,
        room_id_to_studio_type_map=args.room_id_to_studio_type_map,
        room_id_to_studio_location_map=args.room_id_to_studio_location_map,
        clean_class_name_func=args.clean_class_name_func,
    )

    # Assert that the response is as expected
    assert is_classes_dict_equal(
        expected=args.expected_result,
        actual=result,
    )


@pytest.mark.parametrize(
    ("response_file_name", "expected_warning_substrs"),
    [
        pytest.param(
            "invalid_schedule_missing_schedule_table.html",
            ["Failed to get test studio schedule - Schedule table not found: "],
            id="Missing schedule table",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_missing_thead.html",
            ["Failed to get test studio schedule - Schedule table head not found: "],
            id="Schedule table missing thead",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_missing_tbody.html",
            [],
            id="Schedule table missing tbody",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_thead_missing_tr.html",
            ["Failed to get test studio schedule - Schedule table head row not found: "],
            id="Schedule table thead missing tr",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_tbody_missing_tr.html",
            ["Failed to get test studio schedule - Schedule table body row not found: "],
            id="Schedule table tbody missing tr",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_thead_row_no_data.html",
            ["Failed to get test studio schedule - Schedule table head data is null: "],
            id="Schedule table thead row no data",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_tbody_row_no_data.html",
            ["Failed to get test studio schedule - Schedule table body data is null: "],
            id="Schedule table tbody row no data",
        ),
        pytest.param(
            "invalid_schedule_schedule_table_thead_tbody_data_mismatch.html",
            ["Failed to get test studio schedule - Schedule table head and body list length does not match: "],
            id="Schedule table thead and tbody different data length",
        ),
        pytest.param(
            "invalid_schedule_missing_data.html",
            [
                "Failed to get test studio session name: ",
                "Failed to get test studio session instructor: ",
                "Failed to get test studio session time: ",
                "Failed to get test studio session room: ",
            ],
            id="Schedule missing class name/instructor/time/room",
        ),
    ],
)
def test_get_schedule_from_response_soup_invalid_soup(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
    response_file_name: str,
    expected_warning_substrs: list[str],
) -> None:
    """
    Test get_schedule_from_response_soup with invalid soup flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.
      - response_file_name (str): Name of response file to use for the test.
      - expected_warning_substrs (list[str]):
        List of expected warning messages to be logged. Does not include dump of soup.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file(response_file_name), features="html.parser")

    # Call the function to test
    result = get_schedule_from_response_soup(
        logger=mock_logger,
        soup=mock_soup,
        studio_name="test studio",
        table_heading_date_format=ABSOLUTE_TABLE_HEADING_DATE_FORMAT,
        room_id_to_studio_type_map={},
        room_id_to_studio_location_map={},
        clean_class_name_func=None,
    )

    # Assert that the response is as expected
    assert is_classes_dict_equal(expected={}, actual=result)

    # Assert that flow was called with the expected arguments
    assert mock_logger.warning.call_count == len(expected_warning_substrs)
    for expected_warning_substr in expected_warning_substrs:
        assert any(expected_warning_substr in str(call_args[0][0]) for call_args in mock_logger.warning.call_args_list)


def test_get_schedule_from_response_soup_failed_to_map_room(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
) -> None:
    """
    Test get_schedule_from_response_soup failure to map room id to studio type and
    location flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file("single_class_response.html"), features="html.parser")

    # Call the function to test
    result = get_schedule_from_response_soup(
        logger=mock_logger,
        soup=mock_soup,
        studio_name="test studio",
        table_heading_date_format=ABSOLUTE_TABLE_HEADING_DATE_FORMAT,
        room_id_to_studio_type_map={},
        room_id_to_studio_location_map={},
        clean_class_name_func=None,
    )

    # Assert that the response is as expected
    expected_result = {
        date(2025, 4, 7): [
            ClassData(
                studio=StudioType.Unknown,
                location=StudioLocation.Unknown,
                name="CYCLE - F15 + Absolute 45",
                instructor="Triscilla",
                time="7:15 AM",
                availability=ClassAvailability.Available,
                capacity_info=CapacityInfo(),
            )
        ]
    }
    assert is_classes_dict_equal(expected=expected_result, actual=result)


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            GetInstructorIDTestArgs(
                response_file_name="absolute_raffles_6_to_12_apr.html",
                expected_result=absolute_expected_results.EXPECTED_RAFFLES_6_TO_12_APR_INSTRUCTORID_MAP,
            ),
            id="Absolute Raffles 6 to 12 April",
        ),
    ],
)
def test_get_instructorid_map_from_response_soup_single_location(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
    args: GetInstructorIDTestArgs,
) -> None:
    """
    Test get_instructorid_map_from_response_soup with a single location flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.
      - args (GetInstructorIDTestArgs): Provides arguments for the test case.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file(args.response_file_name), features="html.parser")

    # Call the function to test
    instructorid_map = get_instructorid_map_from_response_soup(
        logger=mock_logger, soup=mock_soup, studio_name="test studio"
    )

    # Assert that the response is as expected
    assert instructorid_map == args.expected_result


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            GetInstructorIDTestArgs(
                response_file_name="absolute_milleniawalk_and_i12_7_to_12_apr.html",
                expected_result=absolute_expected_results.EXPECTED_MW_AND_I12_7_TO_12_APR_INSTRUCTORID_MAP,
            ),
            id="Absolute Millenia Walk and i12 7 to 12 April",
        ),
    ],
)
def test_get_instructorid_map_from_response_soup_multiple_locations(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
    args: GetInstructorIDTestArgs,
) -> None:
    """
    Test get_instructorid_map_from_response_soup with a multiple locations flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.
      - args (GetInstructorIDTestArgs): Provides arguments for the test case.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file(args.response_file_name), features="html.parser")

    # Call the function to test
    instructorid_map = get_instructorid_map_from_response_soup(
        logger=mock_logger, soup=mock_soup, studio_name="test studio"
    )

    # Assert that the response is as expected
    assert instructorid_map == args.expected_result


@pytest.mark.parametrize(
    ("response_file_name", "expected_warning_substrs"),
    [
        pytest.param(
            "invalid_instructors_missing_reserve_filter.html",
            [],
            id="Missing reserve filter",
        ),
        pytest.param(
            "invalid_instructors_missing_reserve_filter_1.html",
            ["Failed to get test studio list of instructors - Instructor filter not found: "],
            id="Missing reserve filter 1",
        ),
        pytest.param(
            "invalid_instructors_missing_data.html",
            [
                "Failed to get test studio id of instructor aminah - A tag is null: ",
                "Failed to get test studio id of instructor belle - Href is null: ",
                "Failed to get test studio id of instructor brian - Regex failed to match: ",
            ],
            id="Instructors missing or invalid 'a' tag/href/regex",
        ),
    ],
)
def test_get_instructorid_map_from_response_soup_invalid_soup(
    mocker: pytest_mock.plugin.MockerFixture,
    load_response_file: Callable[[str], str],
    response_file_name: str,
    expected_warning_substrs: list[str],
) -> None:
    """
    Test get_instructorid_map_from_response_soup with invalid soup flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.
      - response_file_name (str): Name of response file to use for the test.
      - expected_warning_substrs (list[str]):
        List of expected warning messages to be logged. Does not include dump of soup.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_soup = BeautifulSoup(markup=load_response_file(response_file_name), features="html.parser")

    # Call the function to test
    instructorid_map = get_instructorid_map_from_response_soup(
        logger=mock_logger, soup=mock_soup, studio_name="test studio"
    )

    # Assert that the response is as expected
    assert instructorid_map == {}

    # Assert that flow was called with the expected arguments
    assert mock_logger.warning.call_count == len(expected_warning_substrs)
    for expected_warning_substr in expected_warning_substrs:
        assert any(expected_warning_substr in str(call_args[0][0]) for call_args in mock_logger.warning.call_args_list)


def test_get_zingfit_schedule_and_instructorid_map_absolute_flow(
    mocker: pytest_mock.plugin.MockerFixture, load_response_file: Callable[[str], str]
) -> None:
    """
    Test get_zingfit_schedule_and_instructorid_map for absolute flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - load_response_file (Callable[[str], str]): Fixture that loads file content from the example_responses folder.

    """
    # Setup mocks
    mock_logger = mocker.Mock(spec=logging.Logger)

    mock_week_0_first_request_response = mocker.Mock()
    mock_week_0_first_request_response.text = load_response_file("absolute_centrepoint_7_to_13_apr.html")

    mock_week_0_second_request_response = mocker.Mock()
    mock_week_0_second_request_response.text = load_response_file("absolute_greatworld_8_to_13_apr.html")

    mock_week_1_first_request_response = mocker.Mock()
    mock_week_1_first_request_response.text = load_response_file("absolute_centrepoint_14_to_20_apr.html")

    mock_week_1_second_request_response = mocker.Mock()
    mock_week_1_second_request_response.text = load_response_file("absolute_greatworld_14_to_20_apr.html")

    mocker.patch(
        "requests.get",
        side_effect=[
            mock_week_0_first_request_response,
            mock_week_0_second_request_response,
            mock_week_1_first_request_response,
            mock_week_1_second_request_response,
        ],
    )

    # Call the function to test
    schedule, instructorid_map = get_zingfit_schedule_and_instructorid_map(
        logger=mock_logger,
        studio_name="test studio",
        studio_url_subdomain=ABSOLUTE_URL_SUBDOMAIN,
        table_heading_date_format=ABSOLUTE_TABLE_HEADING_DATE_FORMAT,
        max_weeks=ABSOLUTE_MAX_WEEKS,
        location_to_site_id_map=ABSOLUTE_LOCATION_TO_SITE_ID_MAP,
        room_id_to_studio_type_map=ABSOLUTE_ROOM_ID_TO_STUDIO_TYPE_MAP,
        room_id_to_studio_location_map=ABSOLUTE_ROOM_ID_TO_STUDIO_LOCATION_MAP,
        clean_class_name_func=None,
    )

    # Assert that the response is as expected
    assert is_classes_dict_equal(
        expected=absolute_expected_results.EXPECTED_CTP_AND_GW_7_TO_20_APR_SCHEDULE,
        actual=schedule.classes,
    )
    assert instructorid_map == absolute_expected_results.EXPECTED_CTP_AND_GW_7_TO_20_APR_INSTRUCTORID_MAP
