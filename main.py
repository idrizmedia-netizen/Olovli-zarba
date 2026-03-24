import kivy
kivy.require('2.3.0')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.progressbar import ProgressBar
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Ellipse, Rectangle, Line, RoundedRectangle, InstructionGroup
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
import random
import os
import sqlite3
import time
import kivy

# --- BAZA TIZIMI ---
def init_db():
    conn = sqlite3.connect("football_pro_v12.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS records 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, score INTEGER, ai_score INTEGER, 
                       team TEXT, duration TEXT, date TEXT)''')
    try:
        cursor.execute("SELECT opp_team FROM records LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE records ADD COLUMN opp_team TEXT DEFAULT 'Unknown'")
    conn.commit()
    conn.close()

# --- REKORD ELEMENTI ---
class RecordItem(BoxLayout):
    def __init__(self, name, score, ai_score, team, opp_team, duration, date, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 110
        self.padding = 10
        self.spacing = 15
        is_win = score > ai_score
        bg_col = (0.1, 0.4, 0.2, 0.7) if is_win else (0.4, 0.1, 0.1, 0.7)
        with self.canvas.before:
            Color(*bg_col)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15,])
        self.bind(pos=self._update_rect, size=self._update_rect)
        l_box = BoxLayout(orientation='vertical', size_hint_x=0.35)
        l_box.add_widget(Label(text=name, bold=True, font_size='16sp'))
        l_box.add_widget(Label(text=team, font_size='12sp', color=(0.7,0.9,1,1)))
        c_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        c_box.add_widget(Label(text=f"{score} : {ai_score}", font_size='24sp', bold=True))
        c_box.add_widget(Label(text="VS", font_size='10sp', color=(1,1,1,0.5)))
        r_box = BoxLayout(orientation='vertical', size_hint_x=0.35)
        r_box.add_widget(Label(text=str(opp_team), bold=True, font_size='14sp', color=(1,0.7,0.7,1)))
        r_box.add_widget(Label(text=date.split()[1] + " " + date.split()[2] if len(date.split())>2 else date, font_size='10sp'))
        self.add_widget(l_box); self.add_widget(c_box); self.add_widget(r_box)
    def _update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size

# --- DIZAYNLI TUGMA ---
class StyledButton(Button):
    def __init__(self, bg_color=(0.12, 0.58, 0.95, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''; self.background_color = (0, 0, 0, 0)
        self.main_color = bg_color; self.bold = True
        self.bind(pos=self.update_canvas, size=self.update_canvas)
    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.main_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12,])

# --- TURNIR VIZUAL SETKASI ---
class TournamentBracketUI(Widget):
    def __init__(self, teams, current_round, winners, **kwargs):
        super().__init__(**kwargs)
        self.teams = teams 
        self.round = current_round 
        self.winners = winners 
        self.bind(pos=self.draw_bracket, size=self.draw_bracket)

    def draw_bracket(self, *args):
        self.canvas.clear()
        w, h = self.width, self.height
        cx, cy = self.pos
        with self.canvas:
            Color(1, 1, 1, 0.3)
            # Chorak final chiziqlari
            for i in range(4):
                y_start = cy + h * (0.15 + i * 0.22)
                y_mid = cy + h * (0.26 + (i//2) * 0.44)
                # Chap tomon
                Line(points=[cx + w*0.05, y_start, cx + w*0.15, y_start, cx + w*0.15, y_mid, cx + w*0.22, y_mid], width=1.5)
                # O'ng tomon
                Line(points=[cx + w*0.95, y_start, cx + w*0.85, y_start, cx + w*0.85, y_mid, cx + w*0.78, y_mid], width=1.5)
            
            Color(1, 0.8, 0, 0.6)
            # Yarim final -> Final
            Line(points=[cx + w*0.22, cy + h*0.26, cx + w*0.35, cy + h*0.26, cx + w*0.35, cy + h*0.48, cx + w*0.42, cy + h*0.48], width=2.5)
            Line(points=[cx + w*0.22, cy + h*0.70, cx + w*0.35, cy + h*0.70, cx + w*0.35, cy + h*0.48, cx + w*0.42, cy + h*0.48], width=2.5)
            Line(points=[cx + w*0.78, cy + h*0.26, cx + w*0.65, cy + h*0.26, cx + w*0.65, cy + h*0.48, cx + w*0.58, cy + h*0.48], width=2.5)
            Line(points=[cx + w*0.78, cy + h*0.70, cx + w*0.65, cy + h*0.70, cx + w*0.65, cy + h*0.48, cx + w*0.58, cy + h*0.48], width=2.5)

# --- O'YIN MAYDONI ---
class FootballGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.my_score = 0; self.ai_score = 0; self.turn = "HUJUM"; self.active = False
        self.user_history = {"CHAP": 0, "MARKAZ": 0, "O'NG": 0}
        self.difficulty = "O'RTA"; self.ai_speed_mod = 1.0
        self.weather_instructions = InstructionGroup()
        self.fans_instructions = InstructionGroup()
        with self.canvas.before:
            for i in range(15):
                Color(0.1, 0.32 + (i%2)*0.06, 0.1, 1)
                Rectangle(pos=(0, i*100), size=(3000, 100))
            self.canvas.before.add(self.fans_instructions)
            Color(1, 1, 1, 0.2); Line(rectangle=(25, 25, 2400, 2400), width=1.5)
        with self.canvas:
            self.traj_color = Color(1, 1, 0, 0); self.traj_line = Line(points=[], width=2, dash_length=8, dash_offset=2)
            Color(1, 1, 1, 1); self.goal_frame = Line(points=[], width=7)
            self.goal_net_h = Line(points=[], width=1); self.goal_net_v = Line(points=[], width=1)
            self.keeper_color = Color(1, 0.2, 0.2, 1); self.k_body = Rectangle(size=(52, 82)); self.k_head = Ellipse(size=(36, 36))
            self.k_l_arm = Line(points=[], width=5); self.k_r_arm = Line(points=[], width=5)
            self.trail_color = Color(1, 1, 1, 0); self.trail = Line(points=[], width=8, joint='round', cap='round')
            self.ball_color = Color(1, 1, 1, 1); self.ball = Ellipse(size=(54, 54))
            self.shoe_color = Color(0, 0.7, 1, 1); self.p_body = Rectangle(size=(50, 78)); self.p_head = Ellipse(size=(34, 34))
            self.p_l_arm = Line(points=[], width=4); self.p_r_arm = Line(points=[], width=4); self.p_leg = Line(points=[], width=6)
        self.canvas.after.add(self.weather_instructions)
        self.bind(size=self._redraw)
        Clock.schedule_interval(self._animate_fans, 0.5)
    def _animate_fans(self, dt):
        if not self.active: return
        self.fans_instructions.clear(); w = self.width
        for i in range(25):
            self.fans_instructions.add(Color(random.random(), 0.1, 0.1, 0.7))
            self.fans_instructions.add(Ellipse(pos=(i*(w/25), self.height-140 + random.randint(0,12)), size=(22, 22)))
    def _redraw(self, *args):
        w, h = self.width, self.height
        gw, gh = 520, 260; gx, gy = w/2 - gw/2, h - 450
        self.goal_frame.points = [gx, gy, gx, gy+gh, gx+gw, gy+gh, gx+gw, gy]
        self.ball.pos = (w/2 - 27, 400); self.p_body.pos = (w/2 - 25, 290); self.k_body.pos = (w/2 - 26, h - 400)
        self.update_graphics()
    def update_graphics(self, *args):
        kx, ky = self.k_body.pos; self.k_head.pos = (kx + 8, ky + 77)
        self.k_l_arm.points = [kx, ky+65, kx-35, ky+45]; self.k_r_arm.points = [kx+52, ky+65, kx+87, ky+45]
        px, py = self.p_body.pos; self.p_head.pos = (px + 8, py + 73)
        self.p_l_arm.points = [px, py+62, px-28, py+42]; self.p_r_arm.points = [px+50, py+62, px+78, py+42]; self.p_leg.points = [px+25, py+5, px+35, py-28]
    def show_traj(self, direction):
        if not self.active: return
        w, h = self.width, self.height
        tx = {"CHAP": w/2-210, "MARKAZ": w/2-27, "O'NG": w/2+160}[direction]
        self.traj_line.points = [w/2, 427, tx + 27, h - 350]; self.traj_color.a = 0.5
    def play(self, user_dir):
        if not self.active: return ""
        self.traj_color.a = 0; app = App.get_running_app(); w, h = self.width, self.height
        prob_map = {"OSON": 0.25, "O'RTA": 0.5, "QIYIN": 0.8}; ai_prob = prob_map.get(self.difficulty, 0.5)
        if self.turn == "HUJUM":
            self.user_history[user_dir] += 1
            most = max(self.user_history, key=self.user_history.get)
            ai_dir = most if random.random() < ai_prob else random.choice(["CHAP", "MARKAZ", "O'NG"])
        else: ai_dir = random.choice(["CHAP", "MARKAZ", "O'NG"])
        self.ball.pos = (w/2 - 27, 400); self.trail.points = []
        speed = 0.21 / self.ai_speed_mod
        t_k_dir = ai_dir if self.turn == "HUJUM" else user_dir
        tkx = {"CHAP": w/2-220, "MARKAZ": w/2-26, "O'NG": w/2+180}.get(t_k_dir, w/2-26)
        anim_k = Animation(pos=(tkx, h-400), duration=speed, t='out_quad')
        anim_k.bind(on_progress=self.update_graphics); anim_k.start(self.k_body)
        kick_dir = user_dir if self.turn == "HUJUM" else ai_dir
        tbx = {"CHAP": w/2-200, "MARKAZ": w/2-27, "O'NG": w/2+160}.get(kick_dir, w/2-27)
        self.trail_color.a = 0.8; b_anim = Animation(pos=(tbx, h-370), duration=speed, t='out_quad')
        def _trail(a, w, p): self.trail.points += [self.ball.pos[0]+27, self.ball.pos[1]+27]
        b_anim.bind(on_progress=_trail); b_anim.start(self.ball)
        msg = ""
        if self.turn == "HUJUM":
            if user_dir != ai_dir:
                self.my_score += 1; reward = int(25 * self.ai_speed_mod); app.coins += reward; msg = f"GOL! +{reward}💰"; app.start_confetti()
            else: msg = "SEYV!"
            self.turn = "HIMOYA"
        else:
            if ai_dir != user_dir: self.ai_score += 1; msg = "URDI!"
            else: app.coins += 15; msg = "QAYTARDINGIZ! +15💰"; app.start_confetti()
            self.turn = "HUJUM"
        app.lbl_turn_status.text = f"NAVBAT: {self.turn}"; app.update_coin_label()
        return msg

# --- ASOSIY ILOVA ---
class FootballApp(App):
    def build(self):
        Window.clearcolor = (0.02, 0.02, 0.02, 1); init_db()
        self.data_file = "football_ultra_v12.txt"; self.coins = 1000
        self.current_team = "Paxtakor"; self.opp_team = "Real Madrid"
        self.unlocked_items = ["TEAM_Paxtakor", "BALL_Classic Orb", "TRAIL_Neon Wind", "FORM_Cyber Blue"]
        self.elapsed_time = 0; self.load_data()
        self.in_tournament = False; self.tournament_round = 0; self.tournament_teams = []
        self.tournament_winners = {} 
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=5)
        header = BoxLayout(size_hint_y=0.08, spacing=10)
        self.lbl_coins = Label(text=f"💰 {self.coins} UZS", color=(1, 0.8, 0, 1), bold=True, font_size='20sp')
        header.add_widget(StyledButton(text="REKORDLAR", on_press=self.show_records, bg_color=(0.4, 0, 0.4, 1)))
        header.add_widget(self.lbl_coins)
        header.add_widget(StyledButton(text="DO'KON", on_press=self.show_shop, bg_color=(0.9, 0.5, 0, 1)))
        match_panel = BoxLayout(size_hint_y=0.15, spacing=10, padding=[5, 10])
        self.my_team_box = BoxLayout(orientation='vertical')
        with self.my_team_box.canvas.before:
            Color(0.1, 0.3, 0.6, 0.8); self.rt1 = RoundedRectangle(pos=self.my_team_box.pos, size=self.my_team_box.size, radius=[10])
        self.my_team_box.bind(pos=self._upd_rt, size=self._upd_rt)
        self.lbl_my_team_name = Label(text=self.current_team.upper(), bold=True, font_size='18sp')
        self.my_team_box.add_widget(self.lbl_my_team_name)
        score_box = BoxLayout(orientation='vertical', size_hint_x=0.4)
        self.lbl_score_main = Label(text="0 : 0", font_size='48sp', bold=True)
        self.lbl_timer = Label(text="⏱ 0.0s", font_size='14sp', color=(1,1,1,0.8))
        score_box.add_widget(self.lbl_score_main); score_box.add_widget(self.lbl_timer)
        self.opp_team_box = BoxLayout(orientation='vertical')
        with self.opp_team_box.canvas.before:
            Color(0.6, 0.1, 0.1, 0.8); self.rt2 = RoundedRectangle(pos=self.opp_team_box.pos, size=self.opp_team_box.size, radius=[10])
        self.opp_team_box.bind(pos=self._upd_rt, size=self._upd_rt)
        self.lbl_opp_team_name = Label(text=self.opp_team.upper(), bold=True, font_size='18sp')
        self.opp_team_box.add_widget(self.lbl_opp_team_name)
        match_panel.add_widget(self.my_team_box); match_panel.add_widget(score_box); match_panel.add_widget(self.opp_team_box)
        self.lbl_turn_status = Label(text="TAYYORMI?", color=(0, 1, 0.5, 1), bold=True, size_hint_y=0.05)
        self.lbl_shout = Label(text="", font_size='1sp', bold=True, size_hint_y=0.1)
        self.game_widget = FootballGame(); self.power_bar = ProgressBar(max=100, value=0, size_hint_y=0.02)
        self.setup_ui = BoxLayout(size_hint_y=0.22, orientation='vertical', spacing=8)
        self.input_name = TextInput(text="PRO_PLAYER", multiline=False, size_hint_y=0.3, halign='center')
        btn_row = BoxLayout(spacing=10)
        btn_row.add_widget(StyledButton(text="ODDIY O'YIN", on_press=self.open_prep, bg_color=(0.1, 0.6, 0.2, 1)))
        btn_row.add_widget(StyledButton(text="TURNIR 🏆", on_press=self.start_tournament_flow, bg_color=(0.8, 0.5, 0, 1)))
        self.setup_ui.add_widget(self.input_name); self.setup_ui.add_widget(btn_row)
        self.play_ui = BoxLayout(size_hint_y=0.12, spacing=15, padding=10)
        for d in ["CHAP", "MARKAZ", "O'NG"]: 
            btn = StyledButton(text=d, bg_color=(0.1, 0.4, 0.8, 1))
            btn.bind(on_press=lambda x, d=d: self.start_power(d)); btn.bind(on_release=lambda x, d=d: self.on_action(d))
            self.play_ui.add_widget(btn)
        self.container.add_widget(header); self.container.add_widget(match_panel); self.container.add_widget(self.lbl_turn_status)
        self.container.add_widget(self.lbl_shout); self.container.add_widget(self.game_widget); self.container.add_widget(self.power_bar); self.container.add_widget(self.setup_ui)
        return self.container

    def _upd_rt(self, instance, value):
        if instance == self.my_team_box: self.rt1.pos = instance.pos; self.rt1.size = instance.size
        else: self.rt2.pos = instance.pos; self.rt2.size = instance.size

    def start_tournament_flow(self, instance):
        self.in_tournament = True; self.tournament_round = 0
        self.current_team = self.input_name.text; self.lbl_my_team_name.text = self.current_team.upper()
        all_j = self.get_full_team_list()
        # 8 ta jamoa: foydalanuvchi + 7 ta tasodifiy
        self.tournament_teams = [self.current_team] + random.sample(all_j, 7)
        self.tournament_winners = {0: self.tournament_teams[:], 1: ["?", "?", "?", "?"], 2: ["?", "?"]}
        self.show_bracket_popup()

    def show_bracket_popup(self):
        titles = ["CHORAK FINAL", "YARIM FINAL", "FINAL"]
        p = Popup(title=f"🏆 {titles[self.tournament_round]}", size_hint=(0.95, 0.9))
        root = RelativeLayout()
        root.add_widget(TournamentBracketUI(self.tournament_teams, self.tournament_round, self.tournament_winners))
        
        # Jamoalarni setka bo'yicha joylashtirish (Faqat raqiblar qarama-qarshi tushishi uchun)
        # Chap tomondagi 4 ta (0, 1, 2, 3) va o'ng tomondagi 4 ta (4, 5, 6, 7)
        for i in range(4):
            t_l = StyledButton(text=self.tournament_winners[0][i], font_size='10sp', size_hint=(0.18, 0.07))
            t_l.pos_hint = {'x': 0.01, 'center_y': 0.15 + i * 0.22}
            if self.tournament_round == 0 and i == 0: t_l.main_color = (0, 0.8, 0.3, 1)
            root.add_widget(t_l)
            
            t_r = StyledButton(text=self.tournament_winners[0][i+4], font_size='10sp', size_hint=(0.18, 0.07))
            t_r.pos_hint = {'right': 0.99, 'center_y': 0.15 + i * 0.22}
            root.add_widget(t_r)

        # Yarim finalchilar
        for i in range(2):
            t_l = StyledButton(text=self.tournament_winners[1][i], font_size='10sp', size_hint=(0.18, 0.07))
            t_l.pos_hint = {'x': 0.20, 'center_y': 0.26 + i * 0.44}
            if self.tournament_round == 1 and i == 0: t_l.main_color = (0, 0.8, 0.3, 1)
            root.add_widget(t_l)

            t_r = StyledButton(text=self.tournament_winners[1][i+2], font_size='10sp', size_hint=(0.18, 0.07))
            t_r.pos_hint = {'right': 0.80, 'center_y': 0.26 + i * 0.44}
            root.add_widget(t_r)

        # Finalchilar
        t_f1 = StyledButton(text=self.tournament_winners[2][0], font_size='10sp', size_hint=(0.18, 0.07))
        t_f1.pos_hint = {'x': 0.38, 'center_y': 0.48}
        if self.tournament_round == 2: t_f1.main_color = (0, 0.8, 0.3, 1)
        root.add_widget(t_f1)

                # To'g'ri ko'rinishi:
        t_f2 = StyledButton(text=self.tournament_winners[2][1], font_size='10sp', size_hint=(0.18, 0.07))
        t_f2.pos_hint = {'right': 0.62, 'center_y': 0.48} # Tekislandi
        root.add_widget(t_f2)


        # Turnirda raqibni aniqlash (Foydalanuvchi har doim 0-indexda yoki g'olib bo'lib boradi)
        if self.tournament_round == 0: 
            self.opp_team = self.tournament_winners[0][4] # Chorakda o'ngdagi birinchi jamoa
        elif self.tournament_round == 1: 
            self.opp_team = self.tournament_winners[1][2] # Yarim finalda o'ngdagi birinchi
        else: 
            self.opp_team = self.tournament_winners[2][1] # Finalda o'ngdagi finalchi

        bottom = BoxLayout(orientation='vertical', size_hint=(1, 0.2), pos_hint={'y':0}, padding=5)
        bottom.add_widget(Label(text=f"RAQIB: {self.opp_team}", color=(1, 1, 0, 1), bold=True))
        btn = StyledButton(text="O'YINNI BOSHLASH", bg_color=(0, 0.7, 0.3, 1))
        btn.bind(on_press=lambda x: [self.init_game(None), p.dismiss()]); bottom.add_widget(btn)
        root.add_widget(bottom); p.content = root; p.open()

    def handle_tournament_win(self):
        if self.tournament_round == 0:
            self.tournament_winners[1] = [self.current_team, self.tournament_winners[0][1], self.tournament_winners[0][5], self.tournament_winners[0][2]]
        elif self.tournament_round == 1:
            self.tournament_winners[2] = [self.current_team, self.tournament_winners[1][3]]
        
        if self.tournament_round < 2:
            self.tournament_round += 1
            self.show_visual_shout(f"G'ALABA! {['', 'YARIM FINAL', 'FINAL'][self.tournament_round]}")
            Clock.schedule_once(lambda dt: self.show_bracket_popup(), 2.0)
        else:
            self.coins += 3000; self.update_coin_label(); self.show_visual_shout("🏆 TURNIR CHEMPIONI! +3000💰"); self.in_tournament = False
            self.start_confetti(); Clock.schedule_once(self.restart, 4)

    def init_game(self, instance):
        self.game_widget.my_score = 0; self.game_widget.ai_score = 0; self.lbl_score_main.text = "0 : 0"
        self.game_widget.active = True; self.elapsed_time = 0; self.lbl_opp_team_name.text = self.opp_team.upper()
        Clock.schedule_interval(self._update_stopwatch, 0.1)
        if self.setup_ui.parent: self.container.remove_widget(self.setup_ui)
        if not self.play_ui.parent: self.container.add_widget(self.play_ui)

    def open_prep(self, instance):
        self.in_tournament = False; self.current_team = self.input_name.text; self.lbl_my_team_name.text = self.current_team.upper()
        p = Popup(title="TAYYORGARLIK", size_hint=(0.95, 0.85)); main = BoxLayout(orientation='vertical', padding=15, spacing=10)
        d_box = BoxLayout(size_hint_y=0.2, spacing=5)
        for d in ["OSON", "O'RTA", "QIYIN"]:
            btn = StyledButton(text=d, bg_color=(0.2,0.2,0.2,1)); btn.bind(on_press=lambda x, d=d: self.set_d(x, d)); d_box.add_widget(btn)
        main.add_widget(d_box); main.add_widget(Label(text="RAQIBNI TANLANG", bold=True, size_hint_y=0.1))
        sc = ScrollView(size_hint_y=0.5); box = BoxLayout(orientation='vertical', size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        owned = [x.split("_")[1] for x in self.unlocked_items if "TEAM_" in x]
        for t in owned:
            b = Button(text=t, size_hint_y=None, height=60, background_color=(0.6, 0.1, 0.1, 1))
            b.bind(on_press=lambda x, n=t: self.set_opp_team(n)); box.add_widget(b)
        sc.add_widget(box); main.add_widget(sc)
        go = StyledButton(text="BOSHLASH", bg_color=(0.1, 0.7, 0.3, 1), size_hint_y=0.2)
        go.bind(on_press=lambda x: [self.init_game(None), p.dismiss()]); main.add_widget(go); p.content = main; p.open()

    def set_opp_team(self, name):
        self.opp_team = name; self.lbl_opp_team_name.text = name.upper()
        idx = self.get_team_index(name); self.game_widget.ai_speed_mod = 1.0 + (idx * 0.05)

    def get_team_index(self, name):
        teams = self.get_full_team_list()
        try: return teams.index(name)
        except: return 0

    def set_d(self, b, d):
        self.game_widget.difficulty = d
        for c in b.parent.children: c.main_color = (0.2,0.2,0.2,1); c.update_canvas()
        b.main_color = (0.8, 0.1, 0.1, 1); b.update_canvas()

    def _update_stopwatch(self, dt):
        if self.game_widget.active: self.elapsed_time += dt; self.lbl_timer.text = f"⏱ {self.elapsed_time:.1f}s"

    def start_power(self, d):
        self.game_widget.show_traj(d); self.power_bar.value = 0
        self.p_anim = Animation(value=100, duration=0.8); self.p_anim.start(self.power_bar)

    def on_action(self, direction):
        if not self.game_widget.active: return
        if hasattr(self, 'p_anim'): self.p_anim.stop(self.power_bar)
        res = self.game_widget.play(direction); self.lbl_score_main.text = f"{self.game_widget.my_score} : {self.game_widget.ai_score}"; self.show_visual_shout(res)
        if self.game_widget.my_score >= 11 or self.game_widget.ai_score >= 11:
            self.game_widget.active = False; self.save_score_db()
            if self.in_tournament:
                if self.game_widget.my_score > self.game_widget.ai_score: Clock.schedule_once(lambda dt: self.handle_tournament_win(), 2)
                else: self.show_visual_shout("YUTQAZDINGIZ!"); self.in_tournament = False; Clock.schedule_once(self.restart, 3)
            else: Clock.schedule_once(self.restart, 3)

    def restart(self, dt):
        self.game_widget.my_score = 0; self.game_widget.ai_score = 0; self.lbl_score_main.text = "0 : 0"
        self.elapsed_time = 0; Clock.unschedule(self._update_stopwatch)
        if self.play_ui.parent: self.container.remove_widget(self.play_ui)
        if not self.setup_ui.parent: self.container.add_widget(self.setup_ui)

    def show_records(self, instance):
        conn = sqlite3.connect("football_pro_v12.db"); cur = conn.cursor()
        cur.execute("SELECT name, score, ai_score, team, opp_team, duration, date FROM records ORDER BY id DESC LIMIT 15")
        rows = cur.fetchall(); conn.close(); p = Popup(title="HALL OF FAME", size_hint=(0.95, 0.85))
        sc = ScrollView(); box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10); box.bind(minimum_height=box.setter('height'))
        for r in rows: box.add_widget(RecordItem(r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
        sc.add_widget(box); p.content = sc; p.open()

    def get_full_team_list(self):
        l1 = ["Paxtakor", "Nasaf", "Navbahor", "Neftchi", "Bunyodkor", "AGMK", "Andijon", "Sog'diyona", "Surxon", "Qizilqum"]
        l2 = ["Real Madrid", "Barcelona", "Atletico", "Girona", "Sociedad", "Sevilla", "Valencia", "Betis", "Bilbao", "Villarreal"]
        l3 = ["Man City", "Liverpool", "Arsenal", "Man Utd", "Tottenham", "Chelsea", "Aston Villa", "Newcastle", "West Ham", "Everton"]
        l4 = ["Bayern", "Dortmund", "Leverkusen", "Leipzig", "Stuttgart", "Frankfurt", "Wolfsburg", "Union Berlin", "Mainz", "Freiburg"]
        l5 = ["Inter", "Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta", "Fiorentina", "Bologna", "Torino"]
        l6 = ["PSG", "Monaco", "Marseille", "Lyon", "Lille", "Nice", "Lens", "Rennes", "Reims", "Strasbourg"]
        l7 = ["Benfica", "Porto", "Sporting", "Ajax", "PSV", "Feyenoord", "Galatasaray", "Fenerbahce", "Besiktas", "Celtic"]
        l8 = ["Argentina", "Braziliya", "Fransiya", "Angliya", "Ispaniya", "Portugaliya", "Germaniya", "Italiya", "Urugvay", "Belgiya"]
        l9 = ["O'zbekiston", "Yaponiya", "Koreya", "Eron", "Saudiya", "Qatar", "Marokash", "Senegal", "AQSH", "Meksika"]
        l10 = ["Al-Nassr", "Al-Hilal", "Al-Ittihad", "Inter Miami", "Boca Juniors", "River Plate", "Flamengo", "Palmeiras", "Zenit", "CSKA"]
        return l1+l2+l3+l4+l5+l6+l7+l8+l9+l10

    def show_shop(self, instance):
        shop_p = Popup(title="ULTIMATE SHOP", size_hint=(0.95, 0.95)); tp = TabbedPanel(do_default_tab=False)
        all_j = self.get_full_team_list()
        
        # TO'PLAR UCHUN 40 TA NOM
        balls = ["Yulduz", "Komet", "Vulkan", "Okean", "Plazma", "Kristall", "Neon", "Titan", "Magma", "Zulmat",
                 "Oltin", "Kumush", "Bronza", "Smaragd", "Yoqut", "Olmos", "Marmar", "Granit", "Kiborg", "Atom",
                 "Orbita", "Galaktika", "Foton", "Kvark", "Efir", "Aura", "Tuman", "Bo'ron", "Chaqmoq", "Zarba",
                 "Pulat", "Lazer", "Raqamli", "Gologramma", "Soya", "Nur", "Alov", "Muz", "Shabada", "Yer"]
                 
        # TRAIL UCHUN 40 TA NOM
        trails = ["Moviy Nur", "Qizil Dunyo", "Yashil Iz", "Sariq Olov", "Oq Tuman", "Binafsha Soya", "Pushti Sehr", "To'q Rang", "Kumush To'lqin", "Oltin Chang",
                  "Lazer Chiziq", "Neon Yo'l", "Plazma Oqimi", "Suv Tomchisi", "Olovli Iz", "Elektr Razryad", "Qora tuynuk", "Yulduzli Chang", "Raqamli Iz", "Kiber Oqim",
                  "Muzli Yo'l", "Vulkanik Bug'", "Quyosh Nuri", "Oy Soyasi", "Komet dumi", "Efirli Iz", "Atomik Nur", "Gravitatsiya", "Foton Oqimi", "Kvark Izi",
                  "Dinamik", "Tezlik", "Yashin", "Golografik", "Spektr", "Vektor", "Matritsa", "Portal", "Zarba", "G'alaba"]
                  
        # FORMA UCHUN 40 TA NOM
        forms = ["Qirol", "Sardor", "Lider", "Afsona", "Qahramon", "Gladiator", "Spartak", "Viking", "Samuray", "Ninja",
                 "Kiborg", "Astronavt", "Agent", "Sohibjamol", "Yirtqich", "Burgut", "Sher", "Yo'lbars", "Ajdaho", "Feniks",
                 "Oltin Vektor", "Kumush Shovqin", "Neon Blok", "Retro", "Futuristik", "Minimalizm", "Abstrakt", "Geometriya", "Harbiy", "Klassika",
                 "Oq Tuman", "Qora Tun", "Moviy Osmon", "Yashil Maydon", "Qonli Qizil", "Sariq Quyosh", "Binafsha Rang", "To'q Sariq", "Tilla", "Platina"]

        sections = [("JAMOA", all_j, "TEAM", (0.1, 0.4, 0.2, 1)), ("TO'P", balls, "BALL", (0.1, 0.2, 0.4, 1)), ("TRAIL", trails, "TRAIL", (0.4, 0.1, 0.3, 1)), ("FORMA", forms, "FORM", (0.5, 0.3, 0.1, 1))]
        for title, items, cat, tab_col in sections:
            tab = TabbedPanelItem(text=title); tab.background_color = tab_col; sc = ScrollView()
            box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=15); box.bind(minimum_height=box.setter('height'))
            for i, name in enumerate(items):
                code = f"{cat}_{name}"; is_owned = code in self.unlocked_items; price = 1000 + (i * 800) if cat == "TEAM" else 500 + (i * 300)
                row = BoxLayout(size_hint_y=None, height=90, spacing=10)
                with row.canvas.before: Color(0.15, 0.15, 0.15, 0.9); RoundedRectangle(pos=row.pos, size=row.size, radius=[12])
                info = BoxLayout(orientation='vertical', padding=10); info.add_widget(Label(text=str(name), bold=True, font_size='16sp'))
                if cat == "TEAM": info.add_widget(Label(text=f"Power: {1.0+(i*0.05):.2f}x", font_size='11sp', color=(0,1,0,1)))
                btn = StyledButton(text="EGA" if is_owned else f"{price} UZS", size_hint_x=0.4, bg_color=(0.1, 0.6, 0.3, 1) if is_owned else (0.3, 0.3, 0.3, 1))
                btn.bind(on_press=lambda x, c=cat, cd=code, p=price, n=name: self.buy(c, cd, p, n, shop_p))
                row.add_widget(info); row.add_widget(btn); box.add_widget(row)
            sc.add_widget(box); tab.add_widget(sc); tp.add_widget(tab)
        shop_p.content = tp; shop_p.open()

    def buy(self, cat, code, price, name, pop):
        if code in self.unlocked_items: return
        if self.coins >= price: self.coins -= price; self.unlocked_items.append(code); self.update_coin_label(); pop.dismiss()
        else: self.show_visual_shout("MABLAG' YETARLI EMAS!")

    def update_coin_label(self): self.lbl_coins.text = f"💰 {self.coins} UZS"; self.save_data()
    
    def save_score_db(self):
        conn = sqlite3.connect("football_pro_v12.db"); cur = conn.cursor()
        cur.execute("INSERT INTO records (name, score, ai_score, team, opp_team, duration, date) VALUES (?,?,?,?,?,?,?)", 
                    (self.input_name.text, self.game_widget.my_score, self.game_widget.ai_score, self.current_team, self.opp_team, f"{self.elapsed_time:.1f}s", time.ctime()))
        conn.commit(); conn.close()

    def show_visual_shout(self, text):
        self.lbl_shout.text = text; self.lbl_shout.font_size = 1
        Animation(font_size=40, duration=0.4, t='out_back').start(self.lbl_shout)
        Clock.schedule_once(lambda dt: setattr(self.lbl_shout, 'font_size', 1), 2.0)

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                lns = f.readlines()
                if len(lns)>=2: self.coins = int(lns[0].strip()); self.unlocked_items = lns[1].strip().split(",")

    def save_data(self):
        with open(self.data_file, "w") as f: f.write(f"{self.coins}\n{','.join(self.unlocked_items)}")

    def start_confetti(self):
        for _ in range(25):
            with self.game_widget.canvas:
                Color(random.random(), random.random(), random.random(), 1); r = Rectangle(pos=(random.randint(0,2000), 1800), size=(15,15))
            Animation(pos=(random.randint(0,2000), -100), duration=2.5).start(r)

if __name__ == "__main__":
    init_db(); FootballApp().run()
