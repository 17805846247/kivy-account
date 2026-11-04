from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle, RoundedRectangle
from datetime import datetime, timedelta
import json
import os
import shutil

# ========== 字体自检 ==========
FONT_NAME = 'Roboto'
for fp in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']:
    if os.path.exists(fp):
        try:
            LabelBase.register(name='YaHei', fn_regular=fp)
            FONT_NAME = 'YaHei'
            break
        except:
            pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'records.json')
BACKUP_FILE = os.path.join(BASE_DIR, 'records_backup.json')

CATEGORIES = ['🍜吃饭', '🚌交通', '🎮娱乐', '🛒购物', '🎁红包', '📦其他']

BG = (0.08, 0.09, 0.15, 1)
CARD = (0.12, 0.14, 0.24, 1)
GREEN = (0.1, 0.85, 0.55, 1)
RED = (0.95, 0.35, 0.35, 1)
GOLD = (0.98, 0.78, 0.2, 1)
GRAY = (0.55, 0.58, 0.65, 1)
WHITE = (0.95, 0.96, 0.98, 1)


def card_bg(widget, color=CARD, radius=15):
    widget.canvas.before.clear()
    with widget.canvas.before:
        Color(*color)
        RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    def _redraw(*_):
        widget.canvas.before.clear()
        with widget.canvas.before:
            Color(*color)
            RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=_redraw, size=_redraw)


class 记账App(App):
    def build(self):
        self.records = self.load_data()
        self.selected_cat = '📦其他'

        root = BoxLayout(orientation='vertical', padding=12, spacing=8)
        root.canvas.before.add(Color(*BG))
        root.canvas.before.add(Rectangle(pos=root.pos, size=root.size))
        def _bg(*_):
            root.canvas.before.clear()
            with root.canvas.before:
                Color(*BG)
                Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=_bg, size=_bg)

        # 1. 大余额
        self.balance_label = Label(
            text='¥0.00', font_name=FONT_NAME, font_size=38, bold=True,
            color=WHITE, size_hint_y=0.16
        )
        root.add_widget(self.balance_label)

        # 2. 周统计
        week_row = BoxLayout(orientation='horizontal', spacing=6, size_hint_y=0.1)
        self.lbl_week_in = self._stat('本周收', '¥0', GREEN)
        self.lbl_week_out = self._stat('本周支', '¥0', RED)
        self.lbl_week_net = self._stat('本周结余', '¥0', GOLD)
        week_row.add_widget(self.lbl_week_in)
        week_row.add_widget(self.lbl_week_out)
        week_row.add_widget(self.lbl_week_net)
        root.add_widget(week_row)

        # 3. 分类按钮
        cat_row = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.07)
        self.cat_buttons = []
        for cat in CATEGORIES:
            b = Button(text=cat, font_name=FONT_NAME, font_size=14,
                       background_normal='', background_color=(0.2,0.22,0.35,1), color=WHITE)
            b.bind(on_press=lambda x, c=cat: self.select_cat(c, x))
            self.cat_buttons.append(b)
            cat_row.add_widget(b)
        root.add_widget(cat_row)

        # 4. 金额输入
        self.amount_input = TextInput(
            hint_text='金额', font_name=FONT_NAME, font_size=24,
            multiline=False, input_filter='float',
            size_hint_y=0.09, padding=[10, 8, 10, 8],
            background_color=(0.15,0.17,0.28,1),
            foreground_color=WHITE, hint_text_color=GRAY
        )
        root.add_widget(self.amount_input)

        # 5. 收入/支出大按钮（等高，不挤压）
        btn_row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.1)
        btn_in = Button(text='＋ 收入', font_name=FONT_NAME, font_size=22, bold=True,
                        background_normal='', background_color=GREEN, color=(0,0,0,1))
        btn_in.bind(on_press=lambda x: self.add_record('income'))
        btn_out = Button(text='－ 支出', font_name=FONT_NAME, font_size=22, bold=True,
                         background_normal='', background_color=RED, color=WHITE)
        btn_out.bind(on_press=lambda x: self.add_record('expense'))
        btn_row.add_widget(btn_in)
        btn_row.add_widget(btn_out)
        root.add_widget(btn_row)

        # 6. 提示行
        self.tip_label = Label(text='选分类 → 输金额 → 点按钮', font_name=FONT_NAME,
                               font_size=12, color=GRAY, size_hint_y=0.04)
        root.add_widget(self.tip_label)

        # 7. 记录列表（固定高度，内部滚动，不再撑动整体）
        self.history = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=[0,4,0,4])
        self.history.bind(minimum_height=self.history.setter('height'))
        scroll = ScrollView(size_hint_y=0.34)
        scroll.add_widget(self.history)
        root.add_widget(scroll)

        # 8. 清空
        btn_clear = Button(text='🗑 清空全部', font_name=FONT_NAME, font_size=13,
                           size_hint_y=0.05, background_color=(0.25,0.25,0.3,1), color=GRAY)
        btn_clear.bind(on_press=self.clear_all)
        root.add_widget(btn_clear)

        self.select_cat(self.selected_cat, self.cat_buttons[-1])
        self.update_display()
        return root

    def _stat(self, title, value, color):
        box = BoxLayout(orientation='vertical', padding=5)
        card_bg(box, CARD, 10)
        l1 = Label(text=title, font_name=FONT_NAME, font_size=12, color=GRAY, size_hint_y=0.35)
        l2 = Label(text=value, font_name=FONT_NAME, font_size=18, bold=True, color=color, size_hint_y=0.65)
        box.add_widget(l1)
        box.add_widget(l2)
        box.value_label = l2
        return box

    def select_cat(self, cat, btn):
        self.selected_cat = cat
        for b in self.cat_buttons:
            b.background_color = (0.2,0.22,0.35,1)
        btn.background_color = (0.35,0.55,0.9,1)

    # ========== 数据 ==========
    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            clean = []
            for r in data:
                if isinstance(r, dict) and 'type' in r and 'amount' in r:
                    r.setdefault('note', '')
                    r.setdefault('cat', '📦其他')
                    r.setdefault('time', datetime.now().strftime('%m-%d %H:%M'))
                    clean.append(r)
            return clean
        except Exception as e:
            print(f"[自检] 数据损坏: {e}")
            try: shutil.copy2(DATA_FILE, BACKUP_FILE)
            except: pass
            return []

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[自检] 保存失败: {e}")

    def add_record(self, type):
        text = self.amount_input.text.strip()
        if not text:
            self.tip_label.text = '⚠ 先输金额'
            return
        try:
            amount = float(text)
        except:
            self.tip_label.text = '⚠ 金额要是数字'
            return
        if amount <= 0:
            self.tip_label.text = '⚠ 金额要大于 0'
            return
        self.records.append({
            'type': type, 'amount': amount,
            'note': '', 'cat': self.selected_cat,
            'time': datetime.now().strftime('%m-%d %H:%M')
        })
        self.save_data()
        self.amount_input.text = ''
        self.tip_label.text = '✅ 记上啦' if type == 'income' else '💸 花掉了'
        self.update_display()

    def delete_record(self, rec):
        if rec in self.records:
            self.records.remove(rec)
            self.save_data()
            self.update_display()

    def clear_all(self, instance):
        self.records = []
        self.save_data()
        self.update_display()

    # ========== 显示 ==========
    def get_week_stats(self):
        now = datetime.now()
        monday = now.replace(hour=0, minute=0, second=0, microsecond=0)
        monday -= timedelta(days=monday.weekday())
        win = wout = 0
        for r in self.records:
            try:
                t = datetime.strptime(r['time'], '%m-%d %H:%M')
                t = t.replace(year=now.year)
                if t >= monday:
                    if r['type'] == 'income': win += r['amount']
                    else: wout += r['amount']
            except: pass
        return win, wout

    def update_display(self):
        balance = sum(r['amount'] if r['type'] == 'income' else -r['amount'] for r in self.records)
        self.balance_label.text = f'¥{balance:.2f}'
        self.balance_label.color = GREEN if balance >= 0 else RED

        win, wout = self.get_week_stats()
        self.lbl_week_in.value_label.text = f'¥{win:.0f}'
        self.lbl_week_out.value_label.text = f'¥{wout:.0f}'
        self.lbl_week_net.value_label.text = f'¥{win-wout:.0f}'

        self.history.clear_widgets()
        for r in reversed(self.records[-40:]):
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=6, padding=[6,3,6,3])
            card_bg(row, CARD, 8)
            color = GREEN if r['type'] == 'income' else RED
            sign = '+' if r['type'] == 'income' else '-'
            row.add_widget(Label(text=r.get('cat','📦'), font_name=FONT_NAME, font_size=18, size_hint_x=0.2))
            row.add_widget(Label(text=r['time'], font_name=FONT_NAME, font_size=12, color=GRAY, size_hint_x=0.45))
            row.add_widget(Label(text=f'{sign}¥{r["amount"]:.0f}', font_name=FONT_NAME,
                                 font_size=15, bold=True, color=color, size_hint_x=0.2))
            db = Button(text='✕', font_name=FONT_NAME, font_size=13, size_hint_x=0.15,
                        background_normal='', background_color=(0.4,0.2,0.2,1), color=RED)
            db.bind(on_press=lambda x, rec=r: self.delete_record(rec))
            row.add_widget(db)
            self.history.add_widget(row)


if __name__ == '__main__':
    记账App().run()
