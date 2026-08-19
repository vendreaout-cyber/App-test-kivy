# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.properties import NumericProperty


# ============== قوالب المشاريع ==============
BUSINESS_TEMPLATES = [
    {"name": "Kiosque a The", "cost": 10, "income": 2, "cycle": 1.0, "manager": 50, "icon": "[THE]"},
    {"name": "Lavage Auto", "cost": 100, "income": 25, "cycle": 2.5, "manager": 500, "icon": "[AUTO]"},
    {"name": "Pizzeria", "cost": 500, "income": 120, "cycle": 4.0, "manager": 2500, "icon": "[PIZZA]"},
    {"name": "Hotel Moderne", "cost": 2000, "income": 500, "cycle": 7.0, "manager": 10000, "icon": "[HOTEL]"},
    {"name": "Station Spatiale", "cost": 8000, "income": 2000, "cycle": 12.0, "manager": 50000, "icon": "[SPACE]"},
]

# ============== التحديات ==============
CHALLENGES = [
    {"name": "Debutant", "target": 100, "reward": 50, "desc": "Atteindre 100$"},
    {"name": "Investisseur", "target": 1000, "reward": 200, "desc": "Atteindre 1000$"},
    {"name": "Magnat", "target": 10000, "reward": 1000, "desc": "Atteindre 10000$"},
    {"name": "Tycoon", "target": 100000, "reward": 5000, "desc": "Atteindre 100000$"},
    {"name": "Legende", "target": 1000000, "reward": 50000, "desc": "Atteindre 1,000,000$"},
]


class ChallengeManager:
    """مدير التحديات"""
    
    def __init__(self):
        self.active_challenges = []
        self.completed_challenges = []
        self.load_challenges()
    
    def load_challenges(self):
        self.active_challenges = CHALLENGES.copy()
        self.completed_challenges = []
    
    def check_challenges(self, money):
        completed = []
        for challenge in self.active_challenges:
            if money >= challenge["target"]:
                completed.append(challenge)
        
        for challenge in completed:
            self.active_challenges.remove(challenge)
            self.completed_challenges.append(challenge)
            
            app = App.get_running_app()
            app.money += challenge["reward"]
            app.show_challenge_popup(challenge)
            app.save_game_data()
        
        return len(completed) > 0


class BusinessRow(BoxLayout):
    """Composant representant un investissement / entreprise"""

    def __init__(self, name, base_cost, base_income, cycle_time, manager_cost, icon, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(5)
        self.padding = [dp(10), dp(6)]
        self.size_hint_y = None
        self.height = dp(180)

        self.business_name = name
        self.icon = icon
        self.cost = base_cost
        self.income = base_income
        self.cycle_time = cycle_time
        self.manager_cost = manager_cost
        self.has_manager = False
        self.level = 0
        self.progress_val = 0
        self.is_producing = False

        self.info_label = Label(
            text=f"{self.icon} {self.business_name} (Lvl {self.level})",
            font_size="18sp",
            bold=True,
            size_hint_y=0.2,
            color=(0.9, 0.9, 0.9, 1),
        )
        self.add_widget(self.info_label)

        self.pbar = ProgressBar(
            max=100, 
            value=0, 
            size_hint_y=0.15,
        )
        self.add_widget(self.pbar)

        btn_layout = BoxLayout(
            orientation="horizontal", 
            spacing=dp(8), 
            size_hint_y=0.3
        )

        self.buy_btn = Button(
            text=f"Ameliorer\n({int(self.cost)}$)",
            font_size="13sp",
            halign="center",
        )
        self.buy_btn.bind(on_press=self.upgrade)

        self.produce_btn = Button(
            text=f"Produire (+{int(self.income)}$)", 
            font_size="13sp",
        )
        self.produce_btn.bind(on_press=self.start_production)

        btn_layout.add_widget(self.buy_btn)
        btn_layout.add_widget(self.produce_btn)
        self.add_widget(btn_layout)

        self.manager_btn = Button(
            text=f"Manager Auto ({self.manager_cost}$)",
            font_size="12sp",
            size_hint_y=0.2,
        )
        self.manager_btn.bind(on_press=self.buy_manager)
        self.add_widget(self.manager_btn)

    def upgrade(self, instance):
        app = App.get_running_app()
        if app.money >= self.cost:
            app.money -= self.cost
            self.level += 1
            self.income = max(self.income + 1, int(self.income * 1.35))
            self.cost = int(self.cost * 1.5)
            self.update_ui()
            app.save_game_data()
            app.challenge_manager.check_challenges(app.money)

    def update_ui(self):
        self.info_label.text = f"{self.icon} {self.business_name} (Lvl {self.level})"
        self.buy_btn.text = f"Ameliorer\n({self.cost}$)"
        self.produce_btn.text = f"Produire (+{self.income}$)"
        
        if self.has_manager:
            self.manager_btn.text = "[OK] Manager: ACTIF"
            self.manager_btn.disabled = True
            self.manager_btn.background_color = (0.2, 0.8, 0.3, 1)

    def buy_manager(self, instance):
        app = App.get_running_app()
        if not self.has_manager and app.money >= self.manager_cost:
            app.money -= self.manager_cost
            self.has_manager = True
            self.update_ui()
            app.save_game_data()
            
            if self.level > 0 and not self.is_producing:
                self.start_production(None)

    def start_production(self, instance):
        if self.level > 0 and not self.is_producing:
            self.is_producing = True
            self.progress_val = 0
            Clock.schedule_interval(self._animate_progress, 0.05)

    def _animate_progress(self, dt):
        step = (0.05 / self.cycle_time) * 100
        self.progress_val += step
        self.pbar.value = self.progress_val

        if self.progress_val >= 100:
            self.pbar.value = 0
            self.is_producing = False
            
            app = App.get_running_app()
            app.money += self.income
            app.challenge_manager.check_challenges(app.money)

            if self.has_manager:
                self.start_production(None)

            return False


class IdleTycoonGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(8)

        header_layout = BoxLayout(orientation="horizontal", size_hint_y=0.12, spacing=dp(10))
        
        self.header = Label(
            text="10 $",
            font_size="28sp",
            bold=True,
            color=(0.2, 0.9, 0.2, 1),
            size_hint_x=0.7,
        )
        header_layout.add_widget(self.header)
        
        self.challenge_btn = Button(
            text="Defis",
            font_size="18sp",
            size_hint_x=0.3,
            background_color=(0.8, 0.6, 0.2, 1),
        )
        self.challenge_btn.bind(on_press=self.show_challenges)
        header_layout.add_widget(self.challenge_btn)
        
        self.add_widget(header_layout)

        scroll = ScrollView(size_hint_y=0.88, do_scroll_x=False)
        
        self.businesses_grid = GridLayout(
            cols=1, 
            spacing=dp(10),
            size_hint_y=None,
        )
        self.businesses_grid.bind(minimum_height=self.businesses_grid.setter('height'))

        self.businesses = []
        for template in BUSINESS_TEMPLATES:
            biz = BusinessRow(
                name=template["name"],
                base_cost=template["cost"],
                base_income=template["income"],
                cycle_time=template["cycle"],
                manager_cost=template["manager"],
                icon=template["icon"],
            )
            self.businesses.append(biz)
            self.businesses_grid.add_widget(biz)

        scroll.add_widget(self.businesses_grid)
        self.add_widget(scroll)

    def show_challenges(self, instance):
        app = App.get_running_app()
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))
        
        title = Label(
            text="Defis", 
            font_size="24sp", 
            bold=True,
            size_hint_y=None,
            height=dp(40),
            color=(1, 0.8, 0.2, 1),
        )
        content.add_widget(title)
        
        scroll_challenges = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        challenges_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        challenges_layout.bind(minimum_height=challenges_layout.setter('height'))
        
        if app.challenge_manager.completed_challenges:
            for ch in app.challenge_manager.completed_challenges:
                lbl = Label(
                    text=f"[OK] {ch['name']}  +{ch['reward']}$",
                    font_size="15sp",
                    color=(0.2, 0.8, 0.2, 1),
                    size_hint_y=None,
                    height=dp(30),
                    halign='left',
                    valign='middle',
                )
                lbl.bind(size=lbl.setter('text_size'))
                challenges_layout.add_widget(lbl)
        
        if app.challenge_manager.active_challenges:
            for ch in app.challenge_manager.active_challenges:
                lbl = Label(
                    text=f"[..] {ch['name']}: {ch['desc']}",
                    font_size="14sp",
                    color=(0.9, 0.9, 0.9, 1),
                    size_hint_y=None,
                    height=dp(30),
                    halign='left',
                    valign='middle',
                )
                lbl.bind(size=lbl.setter('text_size'))
                challenges_layout.add_widget(lbl)
        
        if not app.challenge_manager.completed_challenges and not app.challenge_manager.active_challenges:
            lbl = Label(
                text="Tous les defis sont termines!",
                font_size="18sp",
                color=(1, 0.8, 0.2, 1),
                size_hint_y=None,
                height=dp(40),
                halign='center',
            )
            lbl.bind(size=lbl.setter('text_size'))
            challenges_layout.add_widget(lbl)
        
        scroll_challenges.add_widget(challenges_layout)
        content.add_widget(scroll_challenges)
        
        close_btn = Button(
            text="Fermer", 
            size_hint_y=None,
            height=dp(45),
            background_color=(0.3, 0.3, 0.3, 1),
            font_size="16sp",
        )
        
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.9, 0.75),
            auto_dismiss=True,
        )
        
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()


class IdleTycoonApp(App):
    money = NumericProperty(10)

    def build(self):
        self.title = "Idle Tycoon - Beta 1.0"
        self.store = JsonStore("game_save.json")
        self.challenge_manager = ChallengeManager()
        self.root_game = IdleTycoonGame()
        
        self.bind(money=self.update_money_display)
        self.load_game_data()
        self.challenge_manager.check_challenges(self.money)
        return self.root_game

    def update_money_display(self, instance, value):
        self.root_game.header.text = f"{value:,} $"

    def show_challenge_popup(self, challenge):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))
        
        content.add_widget(Label(
            text=f"{challenge['name']} termine!",
            font_size="22sp",
            bold=True,
            color=(1, 0.8, 0.2, 1),
            size_hint_y=0.3,
        ))
        
        content.add_widget(Label(
            text=f"Recompense: +{challenge['reward']}$",
            font_size="20sp",
            color=(0.2, 0.9, 0.2, 1),
            size_hint_y=0.2,
        ))
        
        close_btn = Button(
            text="Super!", 
            size_hint_y=0.2, 
            background_color=(0.2, 0.6, 0.9, 1),
            font_size="18sp",
        )
        
        popup = Popup(
            title="Defi accompli",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=True,
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def save_game_data(self):
        businesses_data = {}
        for biz in self.root_game.businesses:
            businesses_data[biz.business_name] = {
                "level": biz.level,
                "cost": biz.cost,
                "income": biz.income,
                "has_manager": biz.has_manager,
            }
        
        self.store.put("game_data", 
            money=self.money,
            businesses=businesses_data,
            completed_challenges=[ch["name"] for ch in self.challenge_manager.completed_challenges],
        )

    def load_game_data(self):
        if self.store.exists("game_data"):
            data = self.store.get("game_data")
            self.money = data["money"]
            
            if "completed_challenges" in data:
                completed_names = data["completed_challenges"]
                for ch in self.challenge_manager.active_challenges[:]:
                    if ch["name"] in completed_names:
                        self.challenge_manager.active_challenges.remove(ch)
                        self.challenge_manager.completed_challenges.append(ch)
            
            businesses_data = data["businesses"]
            for biz in self.root_game.businesses:
                if biz.business_name in businesses_data:
                    b_data = businesses_data[biz.business_name]
                    biz.level = b_data["level"]
                    biz.cost = b_data["cost"]
                    biz.income = b_data["income"]
                    biz.has_manager = b_data["has_manager"]
                    biz.update_ui()

                    if biz.has_manager and biz.level > 0:
                        biz.start_production(None)

    def on_pause(self):
        self.save_game_data()
        return True

    def on_stop(self):
        self.save_game_data()


if __name__ == "__main__":
    IdleTycoonApp().run()
