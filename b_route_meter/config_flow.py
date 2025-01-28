"""
Config Flow for B-Route Meter
Bルートメーターのコンフィグフロー

This implements the UI wizard to let user input B-route ID, password, 
and serial port in Home Assistant's "Integrations" page.

Home Assistant の「統合」ページでユーザーが BルートID、パスワード、
シリアルポートなどを入力できるウィザードを実装します。
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_RETRY_COUNT,
    CONF_ROUTE_B_ID,
    CONF_ROUTE_B_PWD,
    CONF_SERIAL_PORT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_SERIAL_PORT,
    DEVICE_NAME,
    DOMAIN,
)

# We define the user step schema
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_ROUTE_B_ID,
            description="Get from https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html",
        ): str,
        vol.Required(CONF_ROUTE_B_PWD): str,
        vol.Optional(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): str,
        vol.Optional(CONF_RETRY_COUNT, default=DEFAULT_RETRY_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=10)
        ),
    }
)


class BRouteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    B-Route config flow
    Bルートコンフィグフロー


    This class defines how the UI flow is structured (the steps),
    and how we create an entry once user completes them.


    このクラスはUIフロー(ステップ)の構造を定義し、
    ユーザーが入力を完了した際にエントリを作成する方法を決めます。
    """

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """
        The first (and only) step of our config flow
        コンフィグフローの最初(かつ唯一)のステップ
        """
        errors = {}

        if user_input is not None:
            # Validate or attempt connection here if needed
            # 必要があればここで接続テストやバリデーションを行う

            # For example, we can check if an entry with same B ID already exists
            unique_id = user_input[CONF_ROUTE_B_ID]
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # If everything is OK, create the entry
            return self.async_create_entry(
                title=f"{DEVICE_NAME} ({unique_id})",
                data=user_input,
            )

        # Show the form
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """
        Return the options flow if needed
        オプションフローが必要な場合に返す
        """
        return BRouteOptionsFlow(config_entry)


class BRouteOptionsFlow(config_entries.OptionsFlow):
    """
    Options flow if you want to allow changing config after setup
    設定後に変更を許可したい場合のオプションフロー
    """

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        # If you want to allow user to update route_b_pwd etc, do so here
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)
