"""
test_app.py
Author: https://github.com/lendrixxx
Description: This file tests the implementation of the App class.
"""

import logging
import signal
from typing import Callable, NamedTuple
from unittest.mock import Mock

import pytest
import pytest_mock

from app.app import App


class EnvVarValues(NamedTuple):
    render_external_url: str
    webhook_path: str
    bot_token: str
    port: str


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> EnvVarValues:
    """
    Fixture to set up environment variables.

    Args:
      - monkeypatch (pytest.MonkeyPatch): Provides mocking utilities for patching environment variables.

    """
    values = EnvVarValues(
        render_external_url="https://example.com",
        webhook_path="webhook_path",
        bot_token="bot_token",
        port="8080",
    )
    monkeypatch.setenv("RENDER_EXTERNAL_URL", values.render_external_url)
    monkeypatch.setenv("WEBHOOK_PATH", values.webhook_path)
    monkeypatch.setenv("BOOKER_BOT_TOKEN", values.bot_token)
    monkeypatch.setenv("PORT", values.port)
    return values


class MockAppObjects(NamedTuple):
    mock_logger: Mock
    mock_logging_get_logger: Mock
    mock_logging_basic_config: Mock
    mock_bot: Mock
    mock_telebot_constructor: Mock
    mock_start_command: Mock
    mock_nerd_command: Mock
    mock_instructors_command: Mock
    mock_telebot_bot_command: Mock
    mock_chat_manager: Mock
    mock_chat_manager_constructor: Mock
    mock_keyboard_manager: Mock
    mock_keyboard_manager_constructor: Mock
    mock_studios_manager: Mock
    mock_studios_manager_constructor: Mock
    mock_history_manager: Mock
    mock_history_manager_constructor: Mock
    mock_server: Mock
    mock_server_constructor: Mock
    mock_menu_manager: Mock
    mock_menu_manager_constructor: Mock
    mock_stop_event: Mock
    mock_threading_event_constructor: Mock
    mock_keep_alive_thread: Mock
    mock_server_thread: Mock
    mock_studios_manager_thread: Mock
    mock_threading_thread_constructor: Mock


@pytest.fixture
def mock_app_objects_factory(
    mocker: pytest_mock.plugin.MockerFixture,
) -> Callable[[], MockAppObjects]:
    """
    Fixture to set up mock app objects.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.

    """

    def _mock_app_objects() -> MockAppObjects:
        mock_logger = mocker.Mock()
        mock_logging_get_logger = mocker.patch("app.app.logging.getLogger")
        mock_logging_get_logger.return_value = mock_logger
        mock_logging_basic_config = mocker.patch("app.app.logging.basicConfig")

        mock_bot = mocker.Mock()
        mock_telebot_constructor = mocker.patch("app.app.telebot.TeleBot")
        mock_telebot_constructor.return_value = mock_bot
        mock_start_command = mocker.Mock()
        mock_nerd_command = mocker.Mock()
        mock_instructors_command = mocker.Mock()
        mock_telebot_bot_command = mocker.patch(
            "app.app.telebot.types.BotCommand",
            side_effect=[
                mock_start_command,
                mock_nerd_command,
                mock_instructors_command,
            ],
        )

        mock_chat_manager = mocker.Mock()
        mock_chat_manager_constructor = mocker.patch("app.app.ChatManager")
        mock_chat_manager_constructor.return_value = mock_chat_manager

        mock_keyboard_manager = mocker.Mock()
        mock_keyboard_manager_constructor = mocker.patch("app.app.KeyboardManager")
        mock_keyboard_manager_constructor.return_value = mock_keyboard_manager

        mock_studios_manager = mocker.Mock()
        mock_studios_manager_constructor = mocker.patch("app.app.StudiosManager")
        mock_studios_manager_constructor.return_value = mock_studios_manager

        mock_history_manager = mocker.Mock()
        mock_history_manager_constructor = mocker.patch("app.app.HistoryManager")
        mock_history_manager_constructor.return_value = mock_history_manager

        mock_server = mocker.Mock()
        mock_server_constructor = mocker.patch("app.app.Server")
        mock_server_constructor.return_value = mock_server

        mock_menu_manager = mocker.Mock()
        mock_menu_manager_constructor = mocker.patch("app.app.MenuManager")
        mock_menu_manager_constructor.return_value = mock_menu_manager

        mock_stop_event = mocker.Mock()
        mock_threading_event_constructor = mocker.patch("app.app.threading.Event")
        mock_threading_event_constructor.return_value = mock_stop_event

        mock_keep_alive_thread = mocker.Mock()
        mock_server_thread = mocker.Mock()
        mock_studios_manager_thread = mocker.Mock()
        mock_threading_thread_constructor = mocker.patch(
            "app.app.threading.Thread",
            side_effect=[
                mock_keep_alive_thread,
                mock_server_thread,
                mock_studios_manager_thread,
            ],
        )
        return MockAppObjects(
            mock_logger=mock_logger,
            mock_logging_get_logger=mock_logging_get_logger,
            mock_logging_basic_config=mock_logging_basic_config,
            mock_bot=mock_bot,
            mock_telebot_constructor=mock_telebot_constructor,
            mock_start_command=mock_start_command,
            mock_nerd_command=mock_nerd_command,
            mock_instructors_command=mock_instructors_command,
            mock_telebot_bot_command=mock_telebot_bot_command,
            mock_chat_manager=mock_chat_manager,
            mock_chat_manager_constructor=mock_chat_manager_constructor,
            mock_keyboard_manager=mock_keyboard_manager,
            mock_keyboard_manager_constructor=mock_keyboard_manager_constructor,
            mock_studios_manager=mock_studios_manager,
            mock_studios_manager_constructor=mock_studios_manager_constructor,
            mock_history_manager=mock_history_manager,
            mock_history_manager_constructor=mock_history_manager_constructor,
            mock_server=mock_server,
            mock_server_constructor=mock_server_constructor,
            mock_menu_manager=mock_menu_manager,
            mock_menu_manager_constructor=mock_menu_manager_constructor,
            mock_stop_event=mock_stop_event,
            mock_threading_event_constructor=mock_threading_event_constructor,
            mock_keep_alive_thread=mock_keep_alive_thread,
            mock_server_thread=mock_server_thread,
            mock_studios_manager_thread=mock_studios_manager_thread,
            mock_threading_thread_constructor=mock_threading_thread_constructor,
        )

    return _mock_app_objects


def test_app_initialization(
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
) -> None:
    """
    Test App initialization. Checks that environment variables and objects were
    constructed sucessfully.

    Args:
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
        Function to create and patch mock objects for creation of App object.
      - mock_env_vars (EnvVarValues): Environment variable values that were set.

    """
    # Setup mocks
    mock_app_objects = mock_app_objects_factory()

    # Create App object
    app = App()

    # Assert that flow was called with the expected arguments
    mock_app_objects.mock_logging_get_logger.assert_called_once_with("app.app")
    mock_app_objects.mock_logging_basic_config.assert_called_once_with(
        format="%(asctime)s %(filename)s:%(lineno)d [Thread-%(thread)d][%(levelname)-1s] %(message)s",
        level=logging.INFO,
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    mock_app_objects.mock_telebot_constructor.assert_called_once_with(token=mock_env_vars.bot_token)
    assert mock_app_objects.mock_telebot_bot_command.call_count == 3
    mock_app_objects.mock_bot.set_my_commands.assert_called_once_with(
        commands=[
            mock_app_objects.mock_start_command,
            mock_app_objects.mock_nerd_command,
            mock_app_objects.mock_instructors_command,
        ],
    )

    mock_app_objects.mock_chat_manager_constructor.assert_called_once_with(
        logger=mock_app_objects.mock_logger, bot=mock_app_objects.mock_bot
    )
    mock_app_objects.mock_keyboard_manager_constructor.assert_called_once()
    mock_app_objects.mock_studios_manager_constructor.assert_called_once_with(logger=mock_app_objects.mock_logger)
    mock_app_objects.mock_history_manager_constructor.assert_called_once_with(logger=mock_app_objects.mock_logger)
    mock_app_objects.mock_server_constructor.assert_called_once_with(
        logger=mock_app_objects.mock_logger,
        base_url=mock_env_vars.render_external_url,
        port=int(mock_env_vars.port),
        bot=mock_app_objects.mock_bot,
        webhook_path=mock_env_vars.webhook_path,
    )
    mock_app_objects.mock_menu_manager_constructor.assert_called_once_with(
        logger=mock_app_objects.mock_logger,
        bot=mock_app_objects.mock_bot,
        chat_manager=mock_app_objects.mock_chat_manager,
        keyboard_manager=mock_app_objects.mock_keyboard_manager,
        studios_manager=mock_app_objects.mock_studios_manager,
        history_manager=mock_app_objects.mock_history_manager,
    )
    mock_app_objects.mock_threading_event_constructor.assert_called_once_with()
    assert mock_app_objects.mock_threading_thread_constructor.call_count == 3

    # Assert that the object is created as expected
    assert app.logger == mock_app_objects.mock_logger
    assert app.base_url == mock_env_vars.render_external_url
    assert app.webhook_path == mock_env_vars.webhook_path
    assert app.server_port == int(mock_env_vars.port)
    assert app.bot == mock_app_objects.mock_bot
    assert app.bot_token == mock_env_vars.bot_token
    assert app.chat_manager == mock_app_objects.mock_chat_manager
    assert app.keyboard_manager == mock_app_objects.mock_keyboard_manager
    assert app.studios_manager == mock_app_objects.mock_studios_manager
    assert app.history_manager == mock_app_objects.mock_history_manager
    assert app.server == mock_app_objects.mock_server
    assert app.menu_manager == mock_app_objects.mock_menu_manager
    assert app.stop_event == mock_app_objects.mock_stop_event
    assert app.keep_alive_thread == mock_app_objects.mock_keep_alive_thread
    assert app.server_thread == mock_app_objects.mock_server_thread
    assert app.studios_manager_thread == mock_app_objects.mock_studios_manager_thread


class LoadEnvVarsMissingVarsArgs(NamedTuple):
    env_var_to_delete: str
    is_required: bool


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            LoadEnvVarsMissingVarsArgs(
                env_var_to_delete="RENDER_EXTERNAL_URL",
                is_required=True,
            ),
            id="Render external URL not set",
        ),
        pytest.param(
            LoadEnvVarsMissingVarsArgs(
                env_var_to_delete="WEBHOOK_PATH",
                is_required=True,
            ),
            id="Webhook path not set",
        ),
        pytest.param(
            LoadEnvVarsMissingVarsArgs(
                env_var_to_delete="BOOKER_BOT_TOKEN",
                is_required=True,
            ),
            id="Bot token not set",
        ),
        pytest.param(
            LoadEnvVarsMissingVarsArgs(
                env_var_to_delete="PORT",
                is_required=False,
            ),
            id="Port not set",
        ),
    ],
)
def test_load_env_vars_missing_variables(
    mocker: pytest_mock.plugin.MockerFixture,
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
    monkeypatch: pytest.MonkeyPatch,
    args: LoadEnvVarsMissingVarsArgs,
) -> None:
    """
    Test load_env_vars missing environment variables flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - mock_env_vars (EnvVarValues): Environment variable values that were set.
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
        Function to create and patch mock objects for creation of App object.
      - monkeypatch (pytest.MonkeyPatch): Provides mocking utilities for patching environment variables.
      - args (LoadEnvVarsMissingVarsArgs): Provides arguments for the test case.

    """
    mock_exit = mocker.patch("app.app.exit")

    # Setup mocks
    _ = mock_app_objects_factory()

    # Delete env var
    monkeypatch.delenv(args.env_var_to_delete, raising=False)

    # Create App object
    _ = App()

    # Assert that flow was called with the expected arguments
    if args.is_required:
        mock_exit.assert_called_once_with(1)
    else:
        mock_exit.assert_not_called()


def test_load_env_vars_incorrect_port_type(
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test load_env_vars missing environment variables flow.

    Args:
      - mock_env_vars (EnvVarValues): Environment variable values that were set.
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
        Function to create and patch mock objects for creation of App object.
      - monkeypatch (pytest.MonkeyPatch): Provides mocking utilities for patching environment variables.

    """
    # Setup mocks
    _ = mock_app_objects_factory()

    # Set PORT environment variable to non integer value
    monkeypatch.setenv("PORT", "not_an_int")

    # Create App object
    app = App()

    # Assert that the port is as expected
    assert app.server_port == 80


def test_set_webhook(
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
) -> None:
    """
    Test set_webhook flow.

    Args:
      - mock_env_vars (EnvVarValues): Environment variable values that were set.
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
        Function to create and patch mock objects for creation of App object.

    """
    # Setup mocks
    mock_app_objects = mock_app_objects_factory()

    # Create App object
    app = App()

    # Call the function to test
    app.set_webhook()

    # Assert that flow was called with the expected arguments
    mock_app_objects.mock_bot.set_webhook.assert_called_once_with(url=f"{app.base_url}/{app.webhook_path}")
    mock_app_objects.mock_logger.info.assert_called_once_with("Webhook for Telegram bot successfully set!")


def test_keep_alive(
    mocker: pytest_mock.plugin.MockerFixture,
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
) -> None:
    """
    Test keep_alive flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - mock_env_vars (EnvVarValues): Environment variable values that were set.
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
        Function to create and patch mock objects for creation of App object.

    """
    # Setup mocks
    _ = mock_app_objects_factory()

    mock_schedule_every = mocker.Mock()
    mock_schedule = mocker.patch("app.app.schedule")
    mock_schedule.every.return_value = mock_schedule_every

    # Create App object
    app = App()

    # Call the function to test
    app.keep_alive()

    # Assert that flow was called with the expected arguments
    mock_schedule.every.assert_called_once_with(5)
    mock_schedule_every.minutes.do.assert_called_once_with(job_func=app.server.ping_self)


def test_shutdown(
    mocker: pytest_mock.plugin.MockerFixture,
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
) -> None:
    """
    Test shutdown flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - mock_env_vars (EnvVarValues): Environment variable values that were set.
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
      Function to create and patch mock objects for creation of App object.

    """
    # Setup mocks
    mock_app_objects = mock_app_objects_factory()

    mock_exit = mocker.patch("app.app.exit")

    # Create App object
    app = App()

    # Call the function to test
    app.shutdown(signal.SIGTERM, None)

    # Assert that flow was called with the expected arguments
    mock_app_objects.mock_stop_event.set.assert_called_once_with()
    expected_logger_info_calls = [
        mocker.call("Received termination signal. Shutting down application..."),
        mocker.call("Successfully exited"),
    ]
    assert mock_app_objects.mock_logger.info.call_args_list == expected_logger_info_calls
    mock_exit.assert_called_once_with(0)

    assert app.stop_event.is_set()


def test_run(
    mocker: pytest_mock.plugin.MockerFixture,
    mock_env_vars: EnvVarValues,
    mock_app_objects_factory: Callable[[], MockAppObjects],
) -> None:
    """
    Test run flow.

    Args:
      - mocker (pytest_mock.plugin.MockerFixture): Provides mocking utilities for patching and mocking.
      - mock_env_vars (EnvVarValues): Environment variable values that were set.
      - mock_app_objects_factory (Callable[[], MockAppObjects]):
        Function to create and patch mock objects for creation of App object.

    """
    # Setup mocks
    mock_app_objects = mock_app_objects_factory()
    mock_app_objects.mock_stop_event.is_set.side_effect = [False, True]  # Loop main loop once

    mock_signal = mocker.patch("app.app.signal.signal")
    mock_set_webhook = mocker.patch("app.app.App.set_webhook")
    mock_schedule_run_pending = mocker.patch("app.app.schedule.run_pending")
    mock_time_sleep = mocker.patch("app.app.time.sleep")

    # Create App object
    app = App()

    # Call the function to test
    app.run()

    # Assert that flow was called with the expected arguments
    expected_signal_calls = [
        mocker.call(signalnum=signal.SIGTERM, handler=app.shutdown),
        mocker.call(signalnum=signal.SIGINT, handler=app.shutdown),
    ]
    assert mock_signal.call_args_list == expected_signal_calls
    mock_app_objects.mock_history_manager.start.assert_called_once_with()
    mock_app_objects.mock_studios_manager.start.assert_called_once_with()
    mock_set_webhook.assert_called_once_with()

    expected_logger_info_calls = [
        mocker.call("Starting threads..."),
        mocker.call("Bot started!"),
    ]
    assert mock_app_objects.mock_logger.info.call_args_list == expected_logger_info_calls

    expected_stop_event_is_set_calls = [mocker.call(), mocker.call()]
    assert mock_app_objects.mock_stop_event.is_set.call_args_list == expected_stop_event_is_set_calls
    mock_schedule_run_pending.assert_called_once_with()
    mock_time_sleep.assert_called_once_with(1)
