"""
B-Route Smart Meter Integration
Bルートスマートメーターの統合

This file is typically used to set up the integration at runtime:
 - async_setup_entry: Called when user adds the integration
 - async_unload_entry: Called to remove it

このファイルでは、統合を実行時にセットアップする処理を記述します:
 - async_setup_entry: ユーザーが統合を追加した時に呼ばれる
 - async_unload_entry: 統合が削除されるときに呼ばれる
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up B-Route meter from a config entry
    コンフィグエントリからBルートメーターをセットアップ
    """
    hass.data.setdefault(DOMAIN, {})

    # Store the config entry data for later usage
    hass.data[DOMAIN][entry.entry_id] = {}

    # Forward the setup to sensor platform
    # センサープラットフォームへのセットアップを転送
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload the config entry
    コンフィグエントリをアンロード
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
