import sys
import time

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log

from secrets import WIFI_SSID, WIFI_PASSWORD
from demo_data import demo_departure, Stops
from settings_store import load_settings, save_settings

# The class runs the app
class Application:
    # The function starts the board, builds UI and connects to WIFI
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.tile2_dark = False
        self.selected_stop = Stops[0]
        self.create_ui()
        self.connect_wifi()
        log("student application ready")

    @staticmethod
    # The function sets the background and text color of a tile
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

    # The function fills the departure table and is filtered by transport type
    def show_departures(self, transport_type):
        self.departure_table.set_row_count(1)
        row = 1
        for departure in demo_departure:
            if departure["Stop"] == self.selected_stop:
                if transport_type == "All" or departure["Type"] == transport_type:
                    self.departure_table.set_cell_value(row, 0, departure["Time"])
                    self.departure_table.set_cell_value(row, 1, departure["Line"])
                    self.departure_table.set_cell_value(row, 2, departure["Destination"])
                    self.departure_table.set_cell_value(row, 3, departure["Status"])
                    row = row + 1

    # The function updates the table when a transport type is selected
    def on_transport_changed(self, _event):
        options = ["All", "Bus", "Train", "Ferry"]
        selected = self.transport_dropdown.get_selected()
        self.show_departures(options[selected])
        self.tile2_label.set_text(self.selected_stop)

    # The function updates the table when a stop is selected
    def on_stop_changed(self, _event):
        self.selected_stop = Stops[self.stop_dropdown.get_selected()]
        options = ["All", "Bus", "Train", "Ferry"]
        selected = self.transport_dropdown.get_selected()
        self.show_departures(options[selected])
        self.tile2_label.set_text(self.selected_stop)

    # The funktion saves the currents settings as default setting
    def on_save_clicked(self, _event):
        options = ["All", "Bus", "Train", "Ferry"]
        selected = self.transport_dropdown.get_selected()
        save_settings({"transport_type": options[selected], "stop": self.selected_stop})

    # The function loades the saved settings and updates the dropdowns and the table
    def apply_saved_settings(self):
        settings = load_settings()
        options = ["All", "Bus", "Train", "Ferry"]
        saved_type = settings.get("transport_type", "All")
        self.transport_dropdown.set_selected(options.index(saved_type))
        saved_stop = settings.get("stop", Stops[0])
        if saved_stop in Stops:
            self.selected_stop = saved_stop
            self.stop_dropdown.set_selected(Stops.index(saved_stop))
            self.tile2_label.set_text(saved_stop)
        self.show_departures(saved_type)

    # The function resets the currents settings to the saved default setting
    def on_reset_clicked(self, _event):
        self.apply_saved_settings()

    # The funktions creates UI
    def create_ui(self):
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile2 = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile3 = self.tileview.add_tile(2, 0, lv.DIR.LEFT)

        self.tile1_label = lv.label(self.tile1)
        self.tile1_label.set_text("PA1484\nGroup 25\nVersion 1.0.0\n\nMembers:\nMushtaba\nHamse\nZirak\nWalid\nMohammed\nMajid")
        self.tile1_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile1_label.center()
        self.apply_tile_colors(self.tile1, self.tile1_label, False)

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

        self.show_departures("All")

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
        self.transport_dropdown.set_options("All\nBus\nTrain\nFerry")
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
        self.stop_dropdown.set_options("\n".join(Stops))
        self.stop_dropdown.set_width(200)
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

        self.apply_saved_settings()

    @staticmethod
    # The function connects to WIFI
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