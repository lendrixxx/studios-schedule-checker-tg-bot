"""
test_studios_manager.py
Author: https://github.com/lendrixxx
Description: This file tests the implementation of the StudiosManager class.
"""

from datetime import date

import pytest_mock
from readerwriterlock.rwlock import RWLockFair

from common.class_data import ClassData
from common.result_data import ResultData
from studios.studio_manager import StudioManager
from studios.studios_manager import StudiosManager
from tests.conftest import is_classes_dict_equal


def test_init(
    mocker: pytest_mock.MockerFixture,
) -> None:
    """
    Test initialization of StudiosManager object.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """
    # Setup mocks
    mock_get_hapana_security_token = mocker.patch("studios.studios_manager.get_hapana_security_token")
    mock_get_hapana_security_token.return_value = "test security token"
    mock_logger = mocker.Mock()

    # Create ResultData object
    studios_manager = StudiosManager(logger=mock_logger)

    # Assert that the object is created as expected
    assert studios_manager.logger == mock_logger
    assert isinstance(studios_manager.cached_result_data_lock, RWLockFair)
    assert studios_manager.cached_result_data.classes == {}
    assert "Absolute" in studios_manager.studios
    assert "Ally" in studios_manager.studios
    assert "Anarchy" in studios_manager.studios
    assert "Barrys" in studios_manager.studios
    assert "Rev" in studios_manager.studios
    assert isinstance(studios_manager.studios["Absolute"], StudioManager)
    assert isinstance(studios_manager.studios["Ally"], StudioManager)
    assert isinstance(studios_manager.studios["Anarchy"], StudioManager)
    assert isinstance(studios_manager.studios["Barrys"], StudioManager)
    assert isinstance(studios_manager.studios["Rev"], StudioManager)


def test_start(
    mocker: pytest_mock.MockerFixture,
    sample_class_data: ClassData,
) -> None:
    """
    Test start flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - sample_class_data (ClassData): Sample ClassData object for the test.

    """
    test_absolute_schedule = ResultData(classes={date(2025, 1, 1): [sample_class_data]})
    test_ally_schedule = ResultData(classes={date(2025, 1, 2): [sample_class_data]})
    test_anarchy_schedule = ResultData(classes={date(2025, 1, 3): [sample_class_data]})
    test_barrys_schedule = ResultData(classes={date(2025, 1, 4): [sample_class_data]})
    test_rev_schedule = ResultData(classes={date(2025, 1, 5): [sample_class_data]})

    # Setup mocks
    mock_get_hapana_security_token = mocker.patch("studios.studios_manager.get_hapana_security_token")
    mock_get_hapana_security_token.return_value = "test security token"
    mock_logger = mocker.Mock()
    mock_absolute_studio_manager = mocker.Mock()
    mock_absolute_studio_manager.get_schedule.return_value = test_absolute_schedule
    mock_ally_studio_manager = mocker.Mock()
    mock_ally_studio_manager.get_schedule.return_value = test_ally_schedule
    mock_anarchy_studio_manager = mocker.Mock()
    mock_anarchy_studio_manager.get_schedule.return_value = test_anarchy_schedule
    mock_barrys_studio_manager = mocker.Mock()
    mock_barrys_studio_manager.get_schedule.return_value = test_barrys_schedule
    mock_rev_studio_manager = mocker.Mock()
    mock_rev_studio_manager.get_schedule.return_value = test_rev_schedule

    # Create ResultData object
    studios_manager = StudiosManager(logger=mock_logger)
    studios_manager.studios["Absolute"] = mock_absolute_studio_manager
    studios_manager.studios["Ally"] = mock_ally_studio_manager
    studios_manager.studios["Anarchy"] = mock_anarchy_studio_manager
    studios_manager.studios["Barrys"] = mock_barrys_studio_manager
    studios_manager.studios["Rev"] = mock_rev_studio_manager

    # Call the function to test
    studios_manager.start()
    cached_result_data = studios_manager.get_cached_result_data()

    # Assert that the response is as expected
    expected_classes = {
        date(2025, 1, 1): sample_class_data,
        date(2025, 1, 2): sample_class_data,
        date(2025, 1, 3): sample_class_data,
        date(2025, 1, 4): sample_class_data,
        date(2025, 1, 5): sample_class_data,
    }
    is_classes_dict_equal(expected=expected_classes, actual=cached_result_data)


def test_schedule_update_cached_result_data_and_notify_waitlist_available(
    mocker: pytest_mock.MockerFixture,
) -> None:
    """
    Test schedule_update_cached_result_data_and_notify_waitlist_available flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """
    # Setup mocks
    mock_get_hapana_security_token = mocker.patch("studios.studios_manager.get_hapana_security_token")
    mock_get_hapana_security_token.return_value = "test security token"

    mock_schedule_every = mocker.Mock()
    mock_schedule = mocker.patch("studios.studios_manager.schedule")
    mock_schedule.every.return_value = mock_schedule_every

    mock_logger = mocker.Mock()

    # Create ResultData object
    studios_manager = StudiosManager(logger=mock_logger)

    # Call the function to test
    studios_manager.schedule_update_cached_result_data_and_notify_waitlist_available()

    # Assert that flow was called with the expected arguments
    mock_schedule_every.minutes.do.assert_called_once_with(
        job_func=studios_manager.update_cached_result_data_and_notify_waitlist_available
    )
