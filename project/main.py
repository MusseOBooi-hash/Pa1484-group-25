import sys
import time

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log

from secrets import WIFI_SSID, WIFI_PASSWORD
from trafiklab import STOPS, get_departures
from settings_store import load_settings, save_settings

# Transport types shown in the dropdown, in the same order
TRANSPORT_OPTIONS = ["All", "Bus", "Train", "Ferry"]

# Names of the stops, shown in the stop dropdown
STOP_NAMES = [stop["name"] for stop in STOPS]

# The most departures shown in the table at the same time
MAX_ROWS = 8


# The class runs the app
class Application:
    # The function starts the board, builds UI and connects to WIFI
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.tile2_dark = False
        self.selected_stop = STOP_NAMES[0]
        self.data_ok = None
        self.create_ui()
        self.connect_wifi()
        self.show_departures(self.get_selected_transport())
        log("student application ready")

    # The function sets the background and text color of a tile
    @staticmethod
    def apply_tile_colors(tile, label, dark):
        tile.set_style_bg_opa(lv.OPA.COVER, 0)
        tile.set_style_bg_color(
            lv.color_hex(0x000000 if dark else 0xFFFFFF), 0
        )
        label.set_style_text_color(
            lv.color_hex(0xFFFFFF if dark else 0x000000), 0
        )

    # The function switches tile 2 between light and dark mode
    def on_tile2_clicked(self, _event):
        self.tile2_dark = not self.tile2_dark
        self.apply_tile_colors(self.tile2, self.tile2_label, self.tile2_dark)

    # The function shows a message in the table instead of departures
    def show_table_message(self, message):
        self.departure_table.set_row_count(2)
        self.departure_table.set_cell_value(1, 0, "")
        self.departure_table.set_cell_value(1, 1, "")
        self.departure_table.set_cell_value(1, 2, message)
        self.departure_table.set_cell_value(1, 3, "")

    # The function fills the departure table with live data (US1.2B),
    # filtered by transport type. Returns True if the data was loaded.
    def show_departures(self, transport_type):
        if not network.WLAN(network.STA_IF).isconnected():
            self.show_table_message("Waiting for Wi-Fi...")
            self.data_ok = False
            return False

        stop_id = STOPS[STOP_NAMES.index(self.selected_stop)]["id"]
        departures = get_departures(stop_id)
        if departures is None:
            self.show_table_message("Could not load departures")
            self.data_ok = False
            return False

        self.departure_table.set_row_count(1)
        row = 1
        for departure in departures:
            if row > MAX_ROWS:
                break
            if transport_type == "All" or departure["Type"] == transport_type:
                self.departure_table.set_cell_value(row, 0, departure["Time"])
                self.departure_table.set_cell_value(row, 1, departure["Line"])
                self.departure_table.set_cell_value(row, 2, departure["Destination"])
                self.departure_table.set_cell_value(row, 3, departure["Status"])
                row = row + 1

        if row == 1:
            self.show_table_message("No departures right now")
        self.data_ok = True
        return True

    # The function returns the transport type selected in the dropdown
    def get_selected_transport(self):
        return TRANSPORT_OPTIONS[self.transport_dropdown.get_selected()]

    # The function updates the table when a transport type is selected
    def on_transport_changed(self, _event):
        self.show_departures(self.get_selected_transport())
        self.tile2_label.set_text(self.selected_stop)

    # The function updates the table when a stop is selected
    def on_stop_changed(self, _event):
        self.selected_stop = STOP_NAMES[self.stop_dropdown.get_selected()]
        self.show_departures(self.get_selected_transport())
        self.tile2_label.set_text(self.selected_stop)

    # The function saves the current settings as default settings
    def on_save_clicked(self, _event):
        save_settings({
            "transport_type": self.get_selected_transport(),
            "stop": self.selected_stop,
        })

    # The function loads the saved settings and updates the dropdowns and the table
    def apply_saved_settings(self):
        settings = load_settings()
        saved_type = settings.get("transport_type", "All")
        self.transport_dropdown.set_selected(TRANSPORT_OPTIONS.index(saved_type))
        saved_stop = settings.get("stop", STOP_NAMES[0])
        if saved_stop in STOP_NAMES:
            self.selected_stop = saved_stop
            self.stop_dropdown.set_selected(STOP_NAMES.index(saved_stop))
            self.tile2_label.set_text(saved_stop)
        self.show_departures(saved_type)

    # The function resets the current settings to the saved default settings
    def on_reset_clicked(self, _event):
        self.apply_saved_settings()

    # The function creates the UI
    def create_ui(self):
        'Function: Creates UI'
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile2 = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile3 = self.tileview.add_tile(2, 0, lv.DIR.LEFT)

        # Start screen (US1.1)
        self.tile1_label = lv.label(self.tile1)
        self.tile1_label.set_text(
            "Karlskrona Departures\nGroup 25\nVersion 1.0.0\n\n"
            "Members:\nMushtaba\nHamse\nZirak\nWalid\nMohammed\nMajid"
        )
        self.tile1_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile1_label.center()
        self.apply_tile_colors(self.tile1, self.tile1_label, False)

        # Departure screen (US1.2)
        self.tile2_label = lv.label(self.tile2)
        self.tile2_label.set_text("Departures")
        self.tile2_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile2_label.align(lv.ALIGN.TOP_MID, 0, 10)
        self.apply_tile_colors(self.tile2, self.tile2_label, False)

        self.departure_table = lv.table(self.tile2)
        self.departure_table.set_column_count(4)
        self.departure_table.set_column_width(0, 90)
        self.departure_table.set_column_width(1, 80)
        self.departure_table.set_column_width(2, 250)
        self.departure_table.set_column_width(3, 150)
        self.departure_table.set_cell_value(0, 0, "Time")
        self.departure_table.set_cell_value(0, 1, "Line")
        self.departure_table.set_cell_value(0, 2, "Destination")
        self.departure_table.set_cell_value(0, 3, "Status")
        self.departure_table.align(lv.ALIGN.TOP_MID, 0, 60)

        # Attribution required by Trafiklab's terms (NF3)
        self.attribution_label = lv.label(self.tile2)
        self.attribution_label.set_text("Data: Trafiklab.se")
        self.attribution_label.set_style_text_color(lv.color_hex(0x555555), 0)
        self.attribution_label.align(lv.ALIGN.TOP_RIGHT, -10, 20)

        # Manual refresh button (US4.2)
        self.refresh_button = lv.button(self.tile2)
        self.refresh_button.align(lv.ALIGN.TOP_LEFT, 10, 10)
        self.refresh_label = lv.label(self.refresh_button)
        self.refresh_label.set_text("Refresh")
        self.refresh_label.center()
        self.refresh_button.add_event_cb(
            self.on_refresh_clicked, lv.EVENT.CLICKED, None
        )

        # Settings screen (US3)
        self.tile3_label = lv.label(self.tile3)
        self.tile3_label.set_text("Settings")
        self.tile3_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile3_label.align(lv.ALIGN.TOP_MID, 0, 10)
        self.apply_tile_colors(self.tile3, self.tile3_label, False)

        self.transport_label = lv.label(self.tile3)
        self.transport_label.set_text("Transport type")
        self.transport_label.set_style_text_color(lv.color_hex(0x000000), 0)
        self.transport_label.align(lv.ALIGN.TOP_LEFT, 20, 70)

        self.transport_dropdown = lv.dropdown(self.tile3)
        self.transport_dropdown.set_options("\n".join(TRANSPORT_OPTIONS))
        self.transport_dropdown.set_width(200)
        self.transport_dropdown.align(lv.ALIGN.TOP_LEFT, 20, 100)
        self.transport_dropdown.add_event_cb(
            self.on_transport_changed, lv.EVENT.VALUE_CHANGED, None
        )

        self.stop_label = lv.label(self.tile3)
        self.stop_label.set_text("Stop")
        self.stop_label.set_style_text_color(lv.color_hex(0x000000), 0)
        self.stop_label.align(lv.ALIGN.TOP_LEFT, 20, 160)

        self.stop_dropdown = lv.dropdown(self.tile3)
        self.stop_dropdown.set_options("\n".join(STOP_NAMES))
        self.stop_dropdown.set_width(250)
        self.stop_dropdown.align(lv.ALIGN.TOP_LEFT, 20, 190)
        self.stop_dropdown.add_event_cb(
            self.on_stop_changed, lv.EVENT.VALUE_CHANGED, None
        )

        self.save_button = lv.button(self.tile3)
        self.save_button.align(lv.ALIGN.BOTTOM_LEFT, 20, -20)
        self.save_label = lv.label(self.save_button)
        self.save_label.set_text("Save as default")
        self.save_label.center()
        self.save_button.add_event_cb(
            self.on_save_clicked, lv.EVENT.CLICKED, None
        )

        self.reset_button = lv.button(self.tile3)
        self.reset_button.align(lv.ALIGN.BOTTOM_RIGHT, -20, -20)
        self.reset_label = lv.label(self.reset_button)
        self.reset_label.set_text("Reset")
        self.reset_label.center()
        self.reset_button.add_event_cb(
            self.on_reset_clicked, lv.EVENT.CLICKED, None
        )

        # Load saved settings and fill the departure table (US3.4)
        self.apply_saved_settings()

    # The function reloads the departures with the current settings (US4.2)
    def refresh_departures(self):
        return self.show_departures(self.get_selected_transport())

    # The function refreshes the departures when the button is pressed
    def on_refresh_clicked(self, _event):
        self.refresh_departures()

    # The function connects to WIFI
    @staticmethod
    def connect_wifi():
        'Function: Connects to WiFi'
        log("connecting to Wi-Fi SSID: " + WIFI_SSID)
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(WIFI_SSID, WIFI_PASSWORD)
        started = time.ticks_ms()
        while (not station.isconnected() and
               time.ticks_diff(time.ticks_ms(), started) < 15_000):
            time.sleep_ms(250)
        log("Wi-Fi connected" if station.isconnected()
            else "Wi-Fi could not connect (timeout)")


try:
    app = Application()
except Exception as error:
    log("FATAL: %r" % (error,))
    sys.print_exception(error)
    raise