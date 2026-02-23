"""
studios_manager.py
Author: https://github.com/lendrixxx
Description:
  This file defines the StudiosManager class which is the main handler for retrieving and storing of studio data.
"""

import logging
import os
import threading
import tracemalloc
from copy import deepcopy
from datetime import date
from typing import Optional, Tuple

import psutil
import schedule
import telebot
from readerwriterlock.rwlock import RWLockFair

from chat.chat_manager import ChatManager
from common.class_availability import ClassAvailability
from common.result_data import ResultData
from common.studio_type import StudioType
from studios.ally.ally import check_access_token as check_ally_access_token
from studios.ally.ally import get_ally_schedule_and_instructorid_map
from studios.anarchy.anarchy import get_anarchy_schedule_and_instructorid_map
from studios.barrys.barrys import get_barrys_schedule_and_instructorid_map
from studios.hapana.data.rev import LOCATION_TO_SITE_ID_MAP as REV_LOCATION_TO_SITE_ID_MAP
from studios.hapana.data.rev import ROOM_NAME_TO_STUDIO_LOCATION_MAP as REV_ROOM_NAME_TO_STUDIO_LOCATION_MAP
from studios.hapana.data.rev import ROOM_NAME_TO_STUDIO_TYPE_MAP as REV_ROOM_NAME_TO_STUDIO_TYPE_MAP
from studios.hapana.hapana import get_hapana_schedule_and_instructorid_map, get_hapana_security_token
from studios.studio_manager import StudioManager
from studios.zingfit.data.absolute import LOCATION_TO_SITE_ID_MAP as ABSOLUTE_LOCATION_TO_SITE_ID_MAP
from studios.zingfit.data.absolute import MAX_SCHEDULE_WEEKS as ABSOLUTE_MAX_SCHEDULE_WEEKS
from studios.zingfit.data.absolute import ROOM_ID_TO_STUDIO_LOCATION_MAP as ABSOLUTE_ROOM_ID_TO_STUDIO_LOCATION_MAP
from studios.zingfit.data.absolute import ROOM_ID_TO_STUDIO_TYPE_MAP as ABSOLUTE_ROOM_ID_TO_STUDIO_TYPE_MAP
from studios.zingfit.data.absolute import TABLE_HEADING_DATE_FORMAT as ABSOLUTE_TABLE_HEADING_DATE_FORMAT
from studios.zingfit.data.absolute import URL_SUBDOMAIN as ABSOLUTE_URL_SUBDOMAIN
from studios.zingfit.zingfit import get_zingfit_schedule_and_instructorid_map


class StudiosManager:
    """
    Manages studios data.

    Attributes:
      - logger (logging.Logger): Logger for logging messages.
      - bot (telebot.TeleBot): Telegram bot instance.
      - chat_manager (ChatManager): The manager handling chat data.
      - cached_result_data_lock (RWLockFair): Read-write lock for cached_result_data.
      - cached_result_data (ResultData): Cached result data containing schedules of all the studios.
      - chat_class_to_notify_waitlist (dict[int, list[Tuple[str, date]]):
        Dictionary of chat id and list of classes to notify when waitlist is available.
      - studios (dict[StudioType, StudioManager]): Dictionary of studio types and studio managers.

    """

    logger: logging.Logger
    bot: telebot.TeleBot
    chat_manager: ChatManager
    cached_result_data_lock: RWLockFair
    cached_result_data: ResultData
    chat_class_to_notify_waitlist: dict[int, list[Tuple[str, date]]]
    ally_admin_telegram_chat_id: Optional[str]
    studios: dict[StudioType, StudioManager]

    def __init__(
        self,
        logger: logging.Logger,
        bot: telebot.TeleBot,
        chat_manager: ChatManager,
        ally_admin_telegram_chat_id: Optional[str],
    ) -> None:
        """
        Initializes the StudiosManager instance.

        Args:
          - logger (logging.Logger): The logger for logging messages.
          - bot (telebot.TeleBot): The instance of the Telegram bot.
          - chat_manager (ChatManager): The manager handling chat data.
          - ally_admin_telegram_chat_id (str): The chat id to use to retrieve ally OTP.
            Should be id of chat of username provided.

        """
        self.logger = logger
        self.bot = bot
        self.chat_manager = chat_manager
        self.cached_result_data_lock = RWLockFair()
        self.cached_result_data = ResultData()
        self.chat_class_to_notify_waitlist: dict[int, list[Tuple[str, date]]] = {}
        self.ally_admin_telegram_chat_id = ally_admin_telegram_chat_id
        self.studios = {
            "Absolute": StudioManager(
                get_schedule_and_instructorid_map_func=get_zingfit_schedule_and_instructorid_map,
                logger=logger,
                studio_name="Absolute",
                studio_url_subdomain=ABSOLUTE_URL_SUBDOMAIN,
                table_heading_date_format=ABSOLUTE_TABLE_HEADING_DATE_FORMAT,
                max_weeks=ABSOLUTE_MAX_SCHEDULE_WEEKS,
                location_to_site_id_map=ABSOLUTE_LOCATION_TO_SITE_ID_MAP,
                room_id_to_studio_type_map=ABSOLUTE_ROOM_ID_TO_STUDIO_TYPE_MAP,
                room_id_to_studio_location_map=ABSOLUTE_ROOM_ID_TO_STUDIO_LOCATION_MAP,
                clean_class_name_func=None,
            ),
            "Ally": StudioManager(
                get_schedule_and_instructorid_map_func=get_ally_schedule_and_instructorid_map,
                logger=logger,
            ),
            "Anarchy": StudioManager(
                get_schedule_and_instructorid_map_func=get_anarchy_schedule_and_instructorid_map,
                logger=logger,
            ),
            "Barrys": StudioManager(
                get_schedule_and_instructorid_map_func=get_barrys_schedule_and_instructorid_map,
                logger=logger,
            ),
            "Rev": StudioManager(
                get_schedule_and_instructorid_map_func=get_hapana_schedule_and_instructorid_map,
                logger=logger,
                studio_name="Rev",
                security_token=get_hapana_security_token(
                    logger=logger,
                    studio_name="Rev",
                    site_id=next(iter(REV_LOCATION_TO_SITE_ID_MAP.values())),  # Get the first value from the map
                ),
                location_to_site_id_map=REV_LOCATION_TO_SITE_ID_MAP,
                room_id_to_studio_type_map=REV_ROOM_NAME_TO_STUDIO_TYPE_MAP,
                room_name_to_studio_location_map=REV_ROOM_NAME_TO_STUDIO_LOCATION_MAP,
            ),
        }
        tracemalloc.start()

    def update_cached_result_data(self) -> None:
        """
        Updates the cached schedule data from all studios.
        """

        def _get_absolute_schedule(
            self: StudiosManager, mutex: threading.Lock, updated_cached_result_data: ResultData
        ) -> None:
            absolute_schedule = self.studios["Absolute"].get_schedule()
            with mutex:
                updated_cached_result_data += absolute_schedule

        def _get_ally_schedule(
            self: StudiosManager, mutex: threading.Lock, updated_cached_result_data: ResultData
        ) -> None:
            ally_schedule = self.studios["Ally"].get_schedule()
            with mutex:
                updated_cached_result_data += ally_schedule

        def _get_anarchy_schedule(
            self: StudiosManager, mutex: threading.Lock, updated_cached_result_data: ResultData
        ) -> None:
            anarchy_schedule = self.studios["Anarchy"].get_schedule()
            with mutex:
                updated_cached_result_data += anarchy_schedule

        def _get_barrys_schedule(
            self: StudiosManager, mutex: threading.Lock, updated_cached_result_data: ResultData
        ) -> None:
            barrys_schedule = self.studios["Barrys"].get_schedule()
            with mutex:
                updated_cached_result_data += barrys_schedule

        def _get_rev_schedule(
            self: StudiosManager, mutex: threading.Lock, updated_cached_result_data: ResultData
        ) -> None:
            rev_schedule = self.studios["Rev"].get_schedule()
            with mutex:
                updated_cached_result_data += rev_schedule

        self.logger.info("Updating cached result data...")
        updated_cached_result_data = ResultData()
        mutex = threading.Lock()

        threads = []
        for func, name in [
            (_get_absolute_schedule, "absolute_thread"),
            (_get_ally_schedule, "ally_thread"),
            (_get_anarchy_schedule, "anarchy_thread"),
            (_get_barrys_schedule, "barrys_thread"),
            (_get_rev_schedule, "rev_thread"),
        ]:
            thread = threading.Thread(
                target=func, name=name, args=[self, mutex, updated_cached_result_data], daemon=True
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        with self.cached_result_data_lock.gen_wlock():
            self.cached_result_data = updated_cached_result_data
        self.logger.info("Successfully updated cached result data!")
        current, peak = tracemalloc.get_traced_memory()
        self.logger.info(f"[debug] tracemalloc Current: {current/1024**2:.2f} MB; Peak: {peak/1024**2:.2f} MB")
        process = psutil.Process(os.getpid())
        info = process.memory_full_info()
        self.logger.info(
            f"[debug] RSS: {info.rss/1024**2:.2f} MB, VMS: {info.vms/1024**2:.2f} MB, USS: {info.uss/1024**2:.2f} MB"
        )

    def add_class_to_notify_waitlist(self, chat_id: int, class_id: str, class_date: date) -> None:
        """
        Adds a list of class IDs to the list of class IDs to notify when waitlist is
        available.

        Args:
          - chat_id (int): The ID of the chat to add a message to be deleted.
          - class_id (str): The ID of the class to add to the list.

        """
        if chat_id in self.chat_class_to_notify_waitlist:
            if (class_id, class_date) not in self.chat_class_to_notify_waitlist[chat_id]:
                self.chat_class_to_notify_waitlist[chat_id].append((class_id, class_date))
        else:
            self.chat_class_to_notify_waitlist[chat_id] = [(class_id, class_date)]

    def set_class_ids_to_notify_waitlist(self, chat_id: int, classes: list[Tuple[str, date]]) -> None:
        """
        Overwrites the list of class IDs to notify when waitlist is available.

        Args:
          - chat_id (int): The ID of the chat to add a message to be deleted.
          - class_ids (list[str]): The IDs of the classes to set.

        """
        self.chat_class_to_notify_waitlist[chat_id] = classes

    def check_and_notify_waitlist_available(self) -> None:
        """
        Checks and sends notifications for available waitlists.
        """
        for chat_id, classes in self.chat_class_to_notify_waitlist.items():
            new_classes_list = []
            for class_id, class_date in classes:
                class_date, class_data = self.cached_result_data.get_class_data(
                    class_id=class_id, class_date=class_date
                )
                if class_data is not None:
                    if class_data.availability != ClassAvailability.Full:
                        class_info_str = class_data.get_string(include_availability=False, include_capacity_info=False)
                        text = f"Waitlist available for {class_info_str}"
                        self.chat_manager.send_prompt(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=None,
                            delete_sent_msg_in_future=False,
                        )
                    else:
                        new_classes_list.append((class_id, class_date))
            self.set_class_ids_to_notify_waitlist(chat_id, new_classes_list)

    def update_cached_result_data_and_notify_waitlist_available(self) -> None:
        self.update_cached_result_data()
        self.check_and_notify_waitlist_available()

    def schedule_update_cached_result_data_and_notify_waitlist_available(self) -> None:
        """
        Periodically updates cached schedule data.

        Scheduled runs is triggered in main thread.

        """
        schedule.every(10).minutes.do(job_func=self.update_cached_result_data_and_notify_waitlist_available)

    def schedule_check_ally_access_token(self) -> None:
        """
        Periodically checks ally access token.

        Scheduled runs is triggered in main thread.

        """
        if self.ally_admin_telegram_chat_id is None:
            return

        # 9 AM SGT
        schedule.every().day.at("01:00").do(
            job_func=check_ally_access_token,
            logger=self.logger,
            ally_admin_telegram_chat_id=self.ally_admin_telegram_chat_id,
            chat_manager=self.chat_manager,
        )

        # 9 PM SGT
        schedule.every().day.at("13:00").do(
            job_func=check_ally_access_token,
            logger=self.logger,
            ally_admin_telegram_chat_id=self.ally_admin_telegram_chat_id,
            chat_manager=self.chat_manager,
        )

    def start(self) -> None:
        """
        Starts the scheduling manager by updating the cached result data.
        """
        check_ally_access_token(
            logger=self.logger,
            ally_admin_telegram_chat_id=self.ally_admin_telegram_chat_id,
            chat_manager=self.chat_manager,
        )
        self.update_cached_result_data()

    def get_cached_result_data(self) -> ResultData:
        """
        Retrieves the cached result data.

        Returns:
          ResultData: The stored cached result data.

        """
        with self.cached_result_data_lock.gen_rlock():
            return deepcopy(self.cached_result_data)
