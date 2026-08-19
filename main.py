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
from kivy.properties import NumericProperty, BooleanProperty


BUSINESS_TEMPLATES = [
    {"name": "Kiosque a The", "cost": 10, "income": 2, "cycle": 1.0, "manager": 50, "icon": "☕"},
    {"name": "Lavage Auto", "cost": 100, "income": 25, "cycle": 2.5, "manager": 500, "icon": "🚗"},
    {"name": "Pizzeria", "cost": 500, "income": 120, "cycle": 4.0, "manager": 2500, "icon": "🍕"},
    {"name": "Hotel Moderne", "cost": 2000, "income": 500, "cycle": 7.0, "manager": 10000, "icon": "🏨"},
    {"name": "Station Spatiale", "cost": 8000, "income": 2000, "cycle": 12.0, "manager": 50000, "icon": "🚀"},
]

CHALLENGES = [
    {"name": "Debutant", "target": 100, "reward": 50, "desc": "Atteindre 100$"},
    {"name": "Investisseur", "target": 1000, "reward": 200, "desc": "Atteindre 1000$"},
    {"name": "Magnat", "target": 10000, "reward": 1000, "desc": "Atteindre 10000$"},
]


class BusinessRow(BoxLayout):
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
            font_size="18sp", bold=True, size_hint_y=0.2
        )
        self.add_widget(self.info_label)

        self.pbar = ProgressBar(max=100, value=0, size_hint_y=0.15)
        self.add_widget(self.pbar)

        btn_layout = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=0.3)
        self.buy_btn = Button(text=f"Ameliorer\n({int(self.cost)}$)", font_size="13sp", halign="center")
        self.buy_btn.bind(on_press=self.upgrade)

        self.produce_btn = Button(text=f"Produire (+{int(self.income)}$)", font_size="13sp")
        self.produce_btn.bind(on_press=self.start_production)

        btn_layout.add_widget(self.buy_btn)
        btn_layout.add_widget(self.produce_btn)
        self.add_widget(btn_layout)

        self.manager_btn = Button(text=f"Manager Auto ({self.manager_cost}$)", font_size="12sp", size_hint_y=0.2)
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

    def update_ui(self):
        self.info_label.text = f"{self.icon} {self.business_name} (Lvl {self.level})"
        self.buy_btn.text = f"Ameliorer\n({self.cost}$)"
        
        app = App.get_running_app()
        effective_income = self.income * (2 if app.is_vip else 1) * (5 if app.is_premium else 1)
        self.produce_btn.text = f"Produire (+{effective_income}$)"
        
        if self.has_manager:
            self.manager_btn.text = "Manager: ACTIF"
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
            # تطبيق مضاعف VIP و Premium
            multiplier = 1
            if app.check_vip_status():
                multiplier *= 2
            if app.check_premium_status():
                multiplier *= 5

            app.money += self.income * multiplier

            if self.has_manager:
                self.start_production(None)
            return False


class IdleTycoonGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(8)

        # ====== الرأس (الرصيد + المتجر) ======
        header_layout = BoxLayout(orientation="horizontal", size_hint_y=0.12, spacing=dp(10))
        
        self.header = Label(text="💰 10 $", font_size="24sp", bold=True, size_hint_x=0.6)
        header_layout.add_widget(self.header)
        
        self.shop_btn = Button(text="🛒 Boutique", font_size="16sp", size_hint_x=0.4, background_color=(0.9, 0.2, 0.4, 1))
        self.shop_btn.bind(on_press=self.open_shop)
        header_layout.add_widget(self.shop_btn)
        
        self.add_widget(header_layout)

        # ====== قائمة المشاريع ======
        scroll = ScrollView(size_hint_y=0.88, do_scroll_x=False)
        self.businesses_grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
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

    def open_shop(self, instance):
        """نافذة المتجر للشراء"""
        app = App.get_running_app()
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))

        status_txt = f"VIP: {'OUI (x2)' if app.is_vip else 'NON'} | Premium: {'OUI (x5)' if app.is_premium else 'NON'}"
        content.add_widget(Label(text=status_txt, font_size="16sp", bold=True, size_hint_y=0.2))

        # زر شراء VIP
        btn_vip = Button(
            text="Acheter VIP Pass (x2 Profit) - 4.99$",
            size_hint_y=0.25,
            background_color=(0.2, 0.7, 0.9, 1),
            disabled=app.is_vip
        )
        btn_vip.bind(on_press=lambda x: app.process_vip_purchase())

        # زر شراء Premium
        btn_premium = Button(
            text="Acheter Premium Pass (x5 Profit) - 9.99$",
            size_hint_y=0.25,
            background_color=(0.9, 0.7, 0.1, 1),
            disabled=app.is_premium
        )
        btn_premium.bind(on_press=lambda x: app.process_premium_purchase())

        content.add_widget(btn_vip)
        content.add_widget(btn_premium)

        close_btn = Button(text="Fermer", size_hint_y=0.2, background_color=(0.4, 0.4, 0.4, 1))
        popup = Popup(title="Boutique In-App", content=content, size_hint=(0.85, 0.5))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)

        popup.open()


class IdleTycoonApp(App):
    money = NumericProperty(10)
    is_vip = BooleanProperty(False)
    is_premium = BooleanProperty(False)

    def build(self):
        self.title = "Idle Tycoon VIP Edition"
        self.store = JsonStore("game_save.json")
        self.root_game = IdleTycoonGame()
        
        self.bind(money=self.update_money_display)
        self.load_game_data()
        return self.root_game

    # ====== دوال التحقق المفصلية (Target Check Methods) ======
    def check_vip_status(self):
        """دالة فحص رتبة VIP"""
        return self.is_vip

    def check_premium_status(self):
        """دالة فحص رتبة Premium"""
        return self.is_premium

    # ====== دوال معالجة الشراء (Target Purchase Handlers) ======
    def process_vip_purchase(self):
        """محاكاة نجاح عملية شراء VIP"""
        self.is_vip = True
        self.save_game_data()
        self.refresh_all_ui()

    def process_premium_purchase(self):
        """محاكاة نجاح عملية شراء Premium"""
        self.is_premium = True
        self.save_game_data()
        self.refresh_all_ui()

    def refresh_all_ui(self):
        for biz in self.root_game.businesses:
            biz.update_ui()

    def update_money_display(self, instance, value):
        vip_tag = " [VIP]" if self.is_vip else ""
        prem_tag = " [PREMIUM]" if self.is_premium else ""
        self.root_game.header.text = f"💰 {value:,} ${vip_tag}{prem_tag}"

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
            is_vip=self.is_vip,
            is_premium=self.is_premium,
            businesses=businesses_data,
        )

    def load_game_data(self):
        if self.store.exists("game_data"):
            data = self.store.get("game_data")
            self.money = data.get("money", 10)
            self.is_vip = data.get("is_vip", False)
            self.is_premium = data.get("is_premium", False)
            
            businesses_data = data.get("businesses", {})
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


if __name__ == "__main__":
    IdleTycoonApp().run()
