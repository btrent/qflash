import datetime
import glob
import os
import random
import sys
import traceback

if (sys.platform == 'darwin'):
    sys.platform = 'linux2'
    
import kivy
from kivy.config import Config, ConfigParser

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import Settings, SettingItem, SettingsPanel
from kivy.uix.screenmanager import SlideTransition, FadeTransition, NoTransition

from kivy.core.window import Window
from kivy.clock import Clock

from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView

from kivy.app import App
from kivy.uix.label import Label
#from kivy.graphics import Color, Line, Rectangle
from kivy.uix.button import Button

class CardList():
    name = ""
    location = ""

class SettingsScreen(Screen):
    pass

class Card:
    front = ""
    back = ""
    valid_date = None

    def __init__(self, f, b, **kwargs):
        self.front = f
        self.back = b
        self.valid_date = datetime.datetime.now()

class QFlash(App):
    cards = []
    card_label = None
    card_list = []
    current_card = None
    valid_cards = []

    def generate_settings(self):
        config = ConfigParser()
        if not config.has_section("root"):
            self.build_config(config)

        settings_panel = Settings() #create instance of Settings
        settings_panel.add_json_panel('QFlash Settings', config, 'settings.json')

        return settings_panel # show the settings interface

    def generate_start_screen(self):
        start_layout = BoxLayout(size_hint=(1,1), align="vertical")

        self.load_card_lists()
        if not self.card_list:
            no_cards_label = Label(markup=True, pos=(0,0), font_name='img/TakaoPMincho.ttf', size_hint=(1,1),
                                   font_size=16, halign="center", text="No tsv files found in " + self.user_data_dir)
            start_layout.add_widget(no_cards_label)
        else:
            list_adapter = ListAdapter(data=self.card_list, cls=ListItemButton, sorted_keys=[])
            list_adapter.bind(on_selection_change=self.select_cards)
            card_list = ListView(item_strings=self.card_list, adapter=list_adapter)
            start_layout.add_widget(card_list)

        return start_layout

    # Getting a list of all card lists on the filesystem
    def load_card_lists(self):
        for file in glob.glob(self.user_data_dir+"/*.tsv"):
            filename = file.replace(self.user_data_dir+"/","")
            self.card_list.append(str(filename))

    # Loading a card list from the filesystem
    def load_cards(self, filename):
        f = open(os.path.join(self.user_data_dir, filename))
        for line in f:
            if "\t" in line:
                tmp = line.split("\t")
                for i in range(len(tmp)):
                    tmp[i] = tmp[i].replace("<br>", "\n")
                self.cards.append(Card(tmp[0], tmp[1]))

    # User has selected a card list
    def select_cards(self, adapter):
        for i in range(0, len(self.card_list)):
            if adapter.get_view(i).is_selected:
                self.load_cards(self.card_list[i])

        self.root.current = 'main'
        self.card_refresh()

        return True

    def card_refresh(self):
        card = self.select_new_card()
        if card is None:
            self.go_to_finished_screen()
        else:
            self.card_label.text = card.front
            self.card_label.text_size = self.card_label.size
            #TODO P1: why does label size only work after first refresh?
            #         and why doesn't valign=top work when label is first drawn?
            #         Try to fix, or just force refresh initially?
            print self.card_label.top

    # Valid cards are cards that are ready to be shown
    def update_valid_cards(self):
        now = datetime.datetime.now()
        self.valid_cards = []
        for card in self.cards:
            delta = now - card.valid_date
            if delta.total_seconds() > 0:
                self.valid_cards.append(card)

    def select_new_card(self):
        self.update_valid_cards()

        if not self.valid_cards:
            self.current_card = None
        else:
            self.current_card = random.choice(self.valid_cards)

        return self.current_card            

    def on_load(self, i):
        if (len(sys.argv) > 1):
            if sys.argv[1] == "test":
                from test import Test
                Test(self).run_all()

                return True

        return True

    def build_config(self, config):
        config.setdefaults('root', {
            'sound': '0',
            'vibrate': '0',
            'keep_screen_on': '1'
        })

    def build(self):
        if (not self.is_desktop()):
            Config.set('postproc', 'retain_time', '10')
            Config.set('postproc', 'double_tap_time', '1')
            Config.set('postproc', 'triple_tap_time', '2')
            Config.set('graphics', 'fullscreen', 'auto')
            Config.write()

        ##################################
        card_layout = BoxLayout(orientation='vertical',size_hint=(1,.85))
        card_widget = BoxLayout(size_hint=(1,.85))
        card_buttons_widget = BoxLayout(size_hint=(1,.15))

        self.card_label = Label(markup=True, pos=(0,0), font_name='img/TakaoPMincho.ttf',
                                font_size=64, halign="center", valign="top")
        self.card_label.bind(on_touch_down=self.on_card_press)
        card_widget.add_widget(self.card_label)

        again_btn = Button(markeup=True)
        again_btn.text = "again"
        again_btn.bind(on_press=self.process_card_btn)
        card_buttons_widget.add_widget(again_btn)

        soon_btn = Button(markeup=True)
        soon_btn.text = "soon"
        soon_btn.bind(on_press=self.process_card_btn)
        card_buttons_widget.add_widget(soon_btn)

        later_btn = Button(markeup=True)
        later_btn.text = "later"
        later_btn.bind(on_press=self.process_card_btn)
        card_buttons_widget.add_widget(later_btn)

        never_btn = Button(markeup=True)
        never_btn.text = "never"
        never_btn.bind(on_press=self.process_card_btn)
        card_buttons_widget.add_widget(never_btn)

        card_layout.add_widget(card_widget)
        card_layout.add_widget(card_buttons_widget)

        platform = kivy.utils.platform()
        card_screen = Screen(name='main')
        card_screen.add_widget(card_layout)

        ##################################
        # Start screen
        ##################################
        start_screen = Screen(name='start')
        start_screen.add_widget(self.generate_start_screen())
        
        ##################################
        # Settings screen
        ##################################
        settings_screen = SettingsScreen(name='settings')
        settings_screen.add_widget(self.generate_settings())

        ##################################
        # No more cards screen
        ##################################
        no_more_layout = BoxLayout(size_hint=(1,1))
        no_more_label = Label(markup=True, pos=(0,0), font_name='img/TakaoPMincho.ttf',
                              font_size=64, halign="center", text="No more cards to review.")
        no_more_layout.add_widget(no_more_label)
        no_more_screen = Screen(name='finished')
        no_more_screen.add_widget(no_more_layout)
        #TODO P1: add buttons to get back to home or to exit

        # Add screens
        # sm = ScreenManager(transition=SlideTransition())
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(start_screen)
        sm.add_widget(card_screen)
        sm.add_widget(settings_screen)
        sm.add_widget(no_more_screen)

        self.on_load(1)

        return sm

    def go_to_main_screen(self):
        self.root.current = 'main'

    def go_to_finished_screen(self):
        self.root.current = 'finished'

    def go_to_settings_screen(self):
        self.root.current='settings'

    def on_card_press(self, label, touch):
        if (label.text == self.current_card.front):
            label.text = self.current_card.back
        else:
            label.text = self.current_card.front

        label.text_size = label.size

    def process_card_btn(self, btn):
        # switch
        {
            'again': (lambda : self.delay_card(0)),
            'soon':  (lambda : self.delay_card(1)),
            'later': (lambda : self.delay_card(4)),
            'never': (lambda : self.delay_card(-1))
        }[btn.text]()

        self.save_data()
        self.card_refresh()

    def save_data(self):
        #TODO P0: implement this
        print "Saving data not implemented!"

    def delay_card(self, num_days):
        if (num_days == -1):
            # Potential Y10K problem
            self.current_card.valid_date = datetime.datetime.strptime("9999", "%Y")
        else:
            self.current_card.valid_date = self.current_card.valid_date + datetime.timedelta(days=num_days)

    def is_desktop(self):
        platform = kivy.utils.platform()

        return True if platform.startswith('win') or platform.startswith('linux') or platform.startswith('mac') else False

    def is_mac(self):
        platform = kivy.utils.platform()
        return True if platform.startswith('mac') else False

if __name__ == '__main__':
    QFlash().run()
