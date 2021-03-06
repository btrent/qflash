import datetime
import glob
import logging
import os
import pickle
import random
import shutil
import sys
import traceback
from sets import Set

# Unfortunately, this stuff has to go here
if (sys.platform == 'darwin'):
    sys.platform = 'linux2'

formatter = logging.Formatter("[%(asctime)s.%(msecs)03d][%(levelname)s][%(message)s]", "%H:%M:%S")
console = logging.StreamHandler() 
console.setFormatter(formatter)
sys._kivy_logging_handler = console
    
# Back to your regularly scheduled imports
import kivy
from kivy.base import EventLoop
from kivy.config import Config, ConfigParser

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import Settings, SettingItem, SettingsPanel
from kivy.uix.screenmanager import SlideTransition, FadeTransition, NoTransition

from kivy.core.window import Window
from kivy.clock import Clock

from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView

from kivy.app import App
from kivy.logger import Logger as Log
from kivy.uix.label import Label
#from kivy.graphics import Color, Line, Rectangle
from kivy.uix.button import Button

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

    def get_key(self):
        return self.front + "_" + self.back

class QFlash(App):
    card_filename = None
    cards = []
    card_label = None
    card_list = []
    current_card = None
    import_msg_label = None
    valid_cards = []

    def generate_settings(self):
        config = ConfigParser()
        if not config.has_section("root"):
            self.build_config(config)

        settings_panel = Settings() #create instance of Settings
        settings_panel.add_json_panel('QFlash Settings', config, 'settings.json')

        return settings_panel # show the settings interface

    def generate_start_screen(self, screen=None):
        # If we're going back to home after a session
        # TODO P2: make this more efficient (state last saved flag, for example)
        if self.cards:
            self.save_state()

        self.card_filename = None
        self.cards = []
        self.card_list = []
        self.current_card = None
        self.valid_cards = []

        screen.clear_widgets()

        start_layout = GridLayout(size_hint=(1,1), cols=1, rows=2)

        self.load_card_lists()

        empty_cards_list = False

        if not self.card_list:
            empty_cards_list = True

            # No decks on device, so let's try copying over our samples
            # 
            # This code is hideous because Android returns errors even when things succeed
            # So we can't trust thrown exceptions!

            sample_list = glob.glob("samples/*.tsv")
            if sample_list:
                for file in sample_list:
                    try:
                        shutil.copy2(file, self.user_data_dir)
                    except:
                        pass

                    self.card_list.append(file[8:])

                empty_cards_list = False
            else:
                empty_cards_list = True
                no_cards_label = Label(markup=True, pos=(0,0), font_name='img/ipag.ttf', size_hint=(1,.85),
                                       font_size=16, halign="center", text="No tsv files found in " + self.user_data_dir)
                start_layout.add_widget(no_cards_label)

        if not empty_cards_list:
            list_adapter = ListAdapter(data=self.card_list, cls=ListItemButton, 
                                       args_converter=(lambda row_index, rec: 
                                                       {'text': rec,'height':75}), 
                                       sorted_keys=[])
            list_adapter.bind(on_selection_change=self.select_cards)
            card_list = ListView(item_strings=self.card_list, adapter=list_adapter, size_hint=(1,.85))
            start_layout.add_widget(card_list)

        file_chooser_btn = Button(text='Import List', size_hint=(1,.15))
        file_chooser_btn.bind(on_release=self.go_to_import_screen)
        start_layout.add_widget(file_chooser_btn)

        screen.add_widget(start_layout)

    def import_list(self, file_chooser_instance, selection, event=None):
        if (len(selection) > 1):
            self.import_msg_label.text = "Please select one file at a time."
            return

        filename = selection[0]

        if (filename[-4:] != ".tsv"):
            self.import_msg_label.text = "Please select a .tsv file (tab separated values)."
            return

        try:
            shutil.copy2(filename, self.user_data_dir)
        except:
            pass

        self.go_to_start_screen()

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

        self.card_filename = filename
        self.load_state()

    # User has selected a card list
    def select_cards(self, adapter):
        for i in range(0, len(self.card_list)):
            if adapter.get_view(i).is_selected:
                self.load_cards(self.card_list[i])

        self.root.current = 'main'

        return True

    def card_refresh(self, event=None):
        Log.debug("refreshing card")
        card = self.select_new_card()
        if card is None:
            # Hack!
            # I have no idea why this works
            # card_refresh should only be called on_enter (onload) for main screen
            # But it is being called just barely before load is complete
            # So if we navigate away before the screen is ready, the app crashes
            # 
            # This stops that
            Clock.schedule_once(self.go_to_finished_screen)
        else:
            self.card_label.text = card.front
            self.card_label.text_size = self.card_label.size

        Log.debug("card refreshed")

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

        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

        return True

    def on_pause(self):
        self.save_state()
        return True

    def on_resume(self):
        return True

    def hook_keyboard(self, window, key, *largs):
        if (key == 27):
            self.go_to_start_screen()
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

        platform = kivy.utils.platform()

        ##################################
        # Start screen
        ##################################
        start_screen = Screen(name='start')
        start_screen.bind(on_pre_enter=self.generate_start_screen)
        
        ##################################
        # Card screen
        ##################################
        card_layout = BoxLayout(orientation='vertical',size_hint=(1,.95))
        card_widget = BoxLayout(size_hint=(1,.85))
        card_buttons_widget = BoxLayout(size_hint=(1,.15))

        self.card_label = Label(markup=True, pos=(0,0), font_name='img/ipag.ttf',
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

        card_screen = Screen(name='main')
        card_screen.add_widget(card_layout)
        card_screen.bind(on_enter=self.card_refresh)

        ##################################
        # Settings screen
        ##################################
        settings_screen = SettingsScreen(name='settings')
        settings_screen.add_widget(self.generate_settings())

        ##################################
        # No more cards screen
        ##################################

        no_more_layout = BoxLayout(size_hint=(1,1), orientation='vertical')
        no_more_label = Label(markup=True, pos=(0,0), font_name='img/ipag.ttf', size_hint=(1,.85),
                              font_size=64, halign="center", text="No more cards to review.")
        no_more_layout.add_widget(no_more_label)
        no_more_btn_layout = BoxLayout(size_hint=(1,.15))

        no_more_home_btn = Button(markup=True)
        no_more_home_btn.text = "Home"
        no_more_home_btn.bind(on_press=self.go_to_start_screen)
        no_more_btn_layout.add_widget(no_more_home_btn)

        no_more_exit_btn = Button(markup=True)
        no_more_exit_btn.text = "Done"
        no_more_exit_btn.bind(on_press=sys.exit)
        no_more_btn_layout.add_widget(no_more_exit_btn)

        no_more_layout.add_widget(no_more_btn_layout)

        no_more_screen = Screen(name='finished')
        no_more_screen.add_widget(no_more_layout)

        import_layout = BoxLayout(size_hint=(1,1), orientation='vertical')
        self.import_msg_label = Label(markup=True, pos=(0,0), font_name = 'img/ipag.ttf', size_hint=(1,.1),
                                      font_size=24, halign='left', text='Please select a .tsv file.')
        import_layout.add_widget(self.import_msg_label)        

        #TODO P3: Can we increase text size?
        import_file_chooser = FileChooserListView(on_submit=self.import_list, path='/')
        import_file_chooser.bind(selection=self.import_list)
        import_layout.add_widget(import_file_chooser)

        import_cancel_button = Button(text="Cancel", on_press=self.go_to_start_screen, size_hint=(1,.15))
        import_layout.add_widget(import_cancel_button)

        import_screen = Screen(name='import')
        import_screen.add_widget(import_layout)

        # Add screens
        # sm = ScreenManager(transition=SlideTransition())
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(start_screen)
        sm.add_widget(card_screen)
        sm.add_widget(settings_screen)
        sm.add_widget(no_more_screen)
        sm.add_widget(import_screen)

        self.on_load(1)

        return sm

    def go_to_main_screen(self, screen=None):
        self.root.current = 'main'

    def go_to_finished_screen(self, screen=None):
        self.root.current = 'finished'

    def go_to_settings_screen(self, screen=None):
        self.root.current='settings'

    def go_to_start_screen(self, screen=None):
        self.root.current='start'

    def go_to_import_screen(self, screen=None):
        self.root.current = 'import'

    # This override replaces the kivy settings screen with the qflash one
    #def open_settings(self):
    #    self.go_to_settings_screen()

    def on_card_press(self, label, touch):
        if (label.text == self.current_card.front):
            label.text = self.current_card.back
        else:
            label.text = self.current_card.front

        label.text_size = label.size

    def process_card_btn(self, btn):
        Log.debug("processing card")
        # switch
        {
            'again': (lambda : self.delay_card(0)),
            'soon':  (lambda : self.delay_card(1)),
            'later': (lambda : self.delay_card(4)),
            'never': (lambda : self.delay_card(-1))
        }[btn.text]()

        Log.debug("card processed")
        if (self.is_desktop()):
            self.save_state()
        self.card_refresh()

    def save_state(self):
        Log.debug("saving state")
        if not self.cards:
            return True

        save_filename = os.path.join(self.user_data_dir, self.card_filename + "_state.dat")
        f = open(save_filename, 'w')
        pickle.dump(self.cards, f)
        Log.debug("state saved")

    def load_state(self):
        load_filename = os.path.join(self.user_data_dir, self.card_filename + "_state.dat")
        try:
            f = open(load_filename)
            unpickler = pickle.Unpickler(f)
            saved_cards = unpickler.load()

            # We can't just load the saved state into self.cards in case 
            # new cards were added or cards were removed (list was updated)
            # TODO P3: optimize this if necessary (test with big lists)
            saved_card_keys = []
            for card in saved_cards:
                saved_card_keys.append(card.get_key())
            fresh_card_keys = []
            for card in self.cards:
                fresh_card_keys.append(card.get_key())

            fresh_card_keys_set = Set(fresh_card_keys)
            saved_card_keys_set = Set(saved_card_keys)
            new_keys = fresh_card_keys_set - saved_card_keys_set
            removed_keys = saved_card_keys_set - fresh_card_keys_set

            tmp_cards = []
            for card in saved_cards:
                if (card.get_key() not in removed_keys):
                    tmp_cards.append(card)
            for card in self.cards:
                if (card.get_key() in new_keys):
                    tmp_cards.append(card)

            self.cards = tmp_cards

        except:
            # TODO P3: if the exception is not "file not found", log it
            pass

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
