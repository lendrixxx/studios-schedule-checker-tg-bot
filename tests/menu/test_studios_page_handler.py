"""
test_studios_page_handler.py
Author: https://github.com/lendrixxx
Description: This file tests the functions of the studios page handler.
"""

from typing import NamedTuple

import pytest
import pytest_mock
import telebot

import menu.studios_page_handler as studios_page_handler
from common.studio_data import StudioData
from common.studio_location import StudioLocation
from common.studio_type import StudioType


def test_studios_selection_callback_query_handler(mocker: pytest_mock.plugin.MockerFixture) -> None:
    """
    Test for studios_selection_callback_query_handler.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """

    test_chat_id = 123
    expected_query_str = "Ally (Spin) - CrossStreet"

    # Setup mocks
    mock_chat = mocker.Mock(id=test_chat_id)
    mock_message = mocker.Mock(spec=telebot.types.Message, chat=mock_chat)
    mock_query = mocker.Mock(spec=telebot.types.CallbackQuery, message=mock_message)

    mock_query_data = mocker.Mock()
    mock_query_data.get_query_str.return_value = expected_query_str

    mock_chat_manager = mocker.Mock()
    mock_chat_manager.get_query_data.return_value = mock_query_data

    sent_msg_mock = mocker.Mock()
    mock_chat_manager.send_prompt.return_value = sent_msg_mock

    mock_keyboard_manager = mocker.Mock()
    mock_keyboard_manager.get_studios_keyboard.return_value = "Mock Keyboard"

    # Run function to test
    studios_page_handler.studios_selection_callback_query_handler(
        query=mock_query,
        chat_manager=mock_chat_manager,
        keyboard_manager=mock_keyboard_manager,
    )

    # Assert that flow was called with the expected arguments
    mock_chat_manager.send_prompt.assert_called_once_with(
        chat_id=test_chat_id,
        text=f"*Currently selected studio(s)*\n{expected_query_str}",
        reply_markup="Mock Keyboard",
        delete_sent_msg_in_future=True,
    )

    mock_chat_manager.update_studios_selection_message.assert_called_once_with(
        chat_id=test_chat_id,
        studios_selection_message=sent_msg_mock,
    )


class StudiosCallbackQueryHandlerArgs(NamedTuple):
    initial_studios: dict[StudioType, StudioData]
    query_data: dict[str, str]
    expected_query_str: str
    is_update_query_data_current_studio_called: bool
    current_studio: StudioType
    is_select_location_handler_called: bool
    selected_location: StudioLocation
    is_locations_handler_called: bool
    is_update_query_data_studios_called: bool
    expected_update_query_data_studios: dict[StudioType, StudioData]
    is_update_query_data_select_all_studios_called: bool
    is_message_edited: bool


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={},
                query_data={"studios": "AllySpin"},
                expected_query_str="AllySpin",
                is_update_query_data_current_studio_called=True,
                current_studio=StudioType.AllySpin,
                is_select_location_handler_called=True,
                selected_location=StudioLocation.CrossStreet,
                is_locations_handler_called=False,
                is_update_query_data_studios_called=True,
                expected_update_query_data_studios={
                    StudioType.AllySpin: StudioData(locations=[StudioLocation.CrossStreet]),
                },
                is_update_query_data_select_all_studios_called=False,
                is_message_edited=True,
            ),
            id="Select Ally (Spin) studio",
        ),
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={},
                query_data={"studios": "All"},
                expected_query_str="All studios selected",
                is_update_query_data_current_studio_called=False,
                current_studio=StudioType.All,
                is_select_location_handler_called=False,
                selected_location=StudioLocation.Null,
                is_locations_handler_called=False,
                is_update_query_data_studios_called=False,
                expected_update_query_data_studios={},
                is_update_query_data_select_all_studios_called=True,
                is_message_edited=True,
            ),
            id="Select All studios",
        ),
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={
                    StudioType.Anarchy: StudioData(
                        locations=[StudioLocation.Robinson], instructors=["Anarchy Instructor"]
                    ),
                    StudioType.Barrys: StudioData(
                        locations=[StudioLocation.Orchard, StudioLocation.Raffles],
                        instructors=["Barrys Instructor", "Barrys Instructor 2"],
                    ),
                },
                query_data={"studios": "Null"},
                expected_query_str="No studio selected",
                is_update_query_data_current_studio_called=False,
                current_studio=StudioType.All,
                is_select_location_handler_called=False,
                selected_location=StudioLocation.Null,
                is_locations_handler_called=False,
                is_update_query_data_studios_called=True,
                expected_update_query_data_studios={},
                is_update_query_data_select_all_studios_called=False,
                is_message_edited=True,
            ),
            id="Deselect all studios",
        ),
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={
                    StudioType.Anarchy: StudioData(
                        locations=[StudioLocation.Robinson], instructors=["Anarchy Instructor"]
                    ),
                },
                query_data={"studios": "Anarchy"},
                expected_query_str="No studio selected",
                is_update_query_data_current_studio_called=True,
                current_studio=StudioType.Anarchy,
                is_select_location_handler_called=True,
                selected_location=StudioLocation.Robinson,
                is_locations_handler_called=False,
                is_update_query_data_studios_called=True,
                expected_update_query_data_studios={},
                is_update_query_data_select_all_studios_called=False,
                is_message_edited=True,
            ),
            id="Deselect selected Anarchy studio",
        ),
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={
                    StudioType.AbsoluteSpin: StudioData(
                        locations=[StudioLocation.MilleniaWalk, StudioLocation.StarVista],
                        instructors=["Spin Instructor"],
                    ),
                },
                query_data={"studios": "Rev"},
                expected_query_str="Mock query str",
                is_update_query_data_current_studio_called=True,
                current_studio=StudioType.Rev,
                is_select_location_handler_called=False,
                selected_location=StudioLocation.Robinson,
                is_locations_handler_called=True,
                is_update_query_data_studios_called=False,
                expected_update_query_data_studios={},
                is_update_query_data_select_all_studios_called=False,
                is_message_edited=False,
            ),
            id="Selcet Rev when Absolute (Spin) is already selected",
        ),
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={
                    StudioType.Anarchy: StudioData(locations=[StudioLocation.Robinson], instructors=["Instructor"]),
                    StudioType.Barrys: StudioData(locations=[StudioLocation.Orchard], instructors=["Test Instructor"]),
                },
                query_data={"studios": "Anarchy"},
                expected_query_str="Mock query str",
                is_update_query_data_current_studio_called=True,
                current_studio=StudioType.Anarchy,
                is_select_location_handler_called=True,
                selected_location=StudioLocation.Robinson,
                is_locations_handler_called=False,
                is_update_query_data_studios_called=True,
                expected_update_query_data_studios={
                    StudioType.Barrys: StudioData(locations=[StudioLocation.Orchard], instructors=["Test Instructor"]),
                },
                is_update_query_data_select_all_studios_called=False,
                is_message_edited=True,
            ),
            id="Unselect Anarchy when Anarchy and Barrys are both selected",
        ),
        pytest.param(
            StudiosCallbackQueryHandlerArgs(
                initial_studios={
                    StudioType.Rev: StudioData(
                        locations=[StudioLocation.TJPG, StudioLocation.Bugis], instructors=["Instructor"]
                    ),
                },
                query_data={"studios": "Rev"},
                expected_query_str="Mock query str",
                is_update_query_data_current_studio_called=True,
                current_studio=StudioType.Rev,
                is_select_location_handler_called=False,
                selected_location=StudioLocation.TJPG,
                is_locations_handler_called=True,
                is_update_query_data_studios_called=False,
                expected_update_query_data_studios={},
                is_update_query_data_select_all_studios_called=False,
                is_message_edited=False,
            ),
            id="Select Rev when Rev is already selected",
        ),
    ],
)
def test_studios_callback_query_handler(
    mocker: pytest_mock.plugin.MockerFixture,
    args: StudiosCallbackQueryHandlerArgs,
) -> None:
    """
    Test for the studios_callback_query_handler function.

    Args:
        mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities.
        args (StudiosCallbackQueryHandlerArgs): Provides arguments for the test case.

    """
    test_chat_id = 123
    test_studios_selection_message_chat_id = 234
    test_studios_selection_message_message_id = 567

    # Setup mocks
    mock_chat = mocker.Mock(id=test_chat_id)
    mock_message = mocker.Mock(spec=telebot.types.Message, chat=mock_chat)
    mock_query = mocker.Mock(spec=telebot.types.CallbackQuery, message=mock_message)
    mock_query.data = str(args.query_data)

    mock_query_data = mocker.Mock()
    mock_query_data.get_query_str.return_value = args.expected_query_str
    mock_query_data.studios = args.initial_studios
    mock_query_data.current_studio = args.current_studio

    sent_msg_mock = mocker.Mock()
    mock_chat_manager = mocker.Mock()
    mock_chat_manager.send_prompt.return_value = sent_msg_mock
    mock_chat_manager.get_query_data.return_value = mock_query_data
    mock_chat_manager.get_studios_selection_message.return_value = mocker.Mock(
        chat=mocker.Mock(id=test_studios_selection_message_chat_id),
        id=test_studios_selection_message_message_id,
    )

    mock_keyboard_manager = mocker.Mock()
    mock_keyboard_manager.get_locations_keyboard.return_value = "Mock Keyboard"

    mock_bot = mocker.Mock()

    # Spy on select_location_handler and locations_handler
    select_location_handler_spy = mocker.spy(studios_page_handler, "select_location_handler")
    locations_handler_spy = mocker.spy(studios_page_handler, "locations_handler")

    # Call the function to test
    studios_page_handler.studios_callback_query_handler(
        query=mock_query,
        bot=mock_bot,
        chat_manager=mock_chat_manager,
        keyboard_manager=mock_keyboard_manager,
    )

    # Assert that flow was called with the expected arguments
    if args.is_update_query_data_current_studio_called:
        mock_chat_manager.update_query_data_current_studio.assert_called_with(
            chat_id=test_chat_id,
            current_studio=args.current_studio,
        )
    else:
        mock_chat_manager.update_query_data_current_studio.assert_not_called()

    if args.is_select_location_handler_called:
        select_location_handler_spy.assert_called_once_with(
            message=mock_message,
            selected_studio_location=args.selected_location,
            chat_manager=mock_chat_manager,
        )
    else:
        select_location_handler_spy.assert_not_called()

    if args.is_locations_handler_called:
        locations_handler_spy.assert_called_once_with(
            message=mock_message,
            chat_manager=mock_chat_manager,
            keyboard_manager=mock_keyboard_manager,
        )
        mock_chat_manager.send_prompt.assert_called_once_with(
            chat_id=test_chat_id,
            text=f"*Currently selected studio(s)*\n{args.expected_query_str}",
            reply_markup="Mock Keyboard",
            delete_sent_msg_in_future=True,
        )
        mock_chat_manager.update_locations_selection_message.assert_called_once_with(
            chat_id=test_chat_id,
            locations_selection_message=sent_msg_mock,
        )
    else:
        locations_handler_spy.assert_not_called()

    if args.is_update_query_data_studios_called:
        mock_chat_manager.update_query_data_studios.assert_called_with(
            chat_id=test_chat_id,
            studios=args.expected_update_query_data_studios,
        )
    else:
        mock_chat_manager.update_query_data_studios.assert_not_called()

    if args.is_update_query_data_select_all_studios_called:
        mock_chat_manager.update_query_data_select_all_studios.assert_called_once()
    else:
        mock_chat_manager.update_query_data_select_all_studios.assert_not_called()

    if args.is_message_edited:
        mock_bot.edit_message_text.assert_called_with(
            chat_id=test_studios_selection_message_chat_id,
            message_id=test_studios_selection_message_message_id,
            text=f"*Currently selected studio(s)*\n{args.expected_query_str}",
            reply_markup=mock_keyboard_manager.get_studios_keyboard.return_value,
            parse_mode="Markdown",
        )
    else:
        mock_bot.edit_message_text.assert_not_called()
