import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import json
import os
from datetime import datetime, timedelta

# Unified database file for absolute sync
DATA_FILE = "planner_data.json"

class HighContrastDashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Dashboard Pro: OS Edition")
        self.root.geometry("1300x780")  # Rescaled cleanly to host the new layout panels
        self.root.configure(bg="#0a0c10")  # Deep black background
        
        # Color Palette
        self.bg_main = "#0a0c10"
        self.bg_card = "#141822"
        self.text_main = "#ffffff"
        self.text_muted = "#6272a4"
        
        # High-Contrast Action & Status Colors
        self.color_select = "#ff5722"       # Vibrant Orange for manual selection
        self.color_today_bg = "#004d26"     # Deep Emerald Green background block for Today
        self.color_today_fg = "#00e676"     # Bright Neon Green font text for Today
        self.color_event = "#ffd700"        # Striking Amber Gold solid block for Reminders
        self.color_habit_accent = "#29b6f6"  # Electric Cyan for Habit tracking accents
        self.color_streak = "#ffb300"       # Warm Gold/Orange for Streaks
        self.color_graph_bar = "#059669"    # Clean emerald green for progress graph fills
        self.color_xp = "#a855f7"           # Royal Purple for Level & Gamification elements

        # Load unified data structure
        self.data = self.load_data()
        
        # Pomodoro Operational Engine States
        self.timer_running = False
        self.timer_seconds_left = 25 * 60  # Initial 25 mins focus block
        self.timer_mode = "Focus"          # Toggle states: "Focus" or "Break"
        
        # Layout Configurations: 3 Columns
        self.root.columnconfigure(0, weight=10, uniform="dashboard")
        self.root.columnconfigure(1, weight=11, uniform="dashboard")
        self.root.columnconfigure(2, weight=11, uniform="dashboard")
        self.root.rowconfigure(0, weight=1)
        
        # --- COLUMN 1: LEFT PANEL (Calendar & Pomodoro & XP Display) ---
        self.left_panel = tk.Frame(root, bg=self.bg_main, padx=16, pady=20)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        
        # GAMIFICATION STATS HEADER
        self.xp_card = tk.Frame(self.left_panel, bg=self.bg_card, bd=1, relief="flat", padx=12, pady=10)
        self.xp_card.pack(fill="x", pady=(0, 14))
        
        self.lvl_lbl = tk.Label(self.xp_card, text=f"LEVEL {self.data['gamification']['level']}", font=("Segoe UI", 12, "bold"), bg=self.bg_card, fg=self.color_xp)
        self.lvl_lbl.pack(anchor="w")
        
        self.xp_progress = ttk.Progressbar(self.xp_card, orient="horizontal", mode="determinate")
        self.xp_progress.pack(fill="x", pady=6)
        self.update_xp_bar_display()
        
        # CALENDAR SUB-CARD
        self.cal = Calendar(
            self.left_panel, selectmode='day', date_pattern='yyyy-mm-dd', font=("Segoe UI", 10),
            background=self.bg_card, foreground=self.text_main, headersbackground=self.bg_main,
            headersforeground=self.text_muted, selectbackground=self.color_select, selectforeground="#0a0c10",
            normalbackground=self.bg_card, normalforeground=self.text_main, weekendbackground=self.bg_card,
            weekendforeground="#ff5555", othermonthbackground="#0d1117", othermonthforeground="#3c444d",
            othermonthwebackground="#0d1117", othermonthweforeground="#6e3c41", bd=0
        )
        self.cal.pack(fill="both", expand=True, pady=(0, 14))
        self.cal.bind("<<CalendarSelected>>", self.on_date_select)
        self.cal.bind("<<CalendarMonthChanged>>", self.apply_dynamic_highlights)
        
        # POMODORO TIMER WORKSPACE CARD
        self.pomo_card = tk.Frame(self.left_panel, bg=self.bg_card, bd=1, relief="flat", padx=14, pady=14)
        self.pomo_card.pack(fill="x", side="bottom")
        
        self.pomo_title = tk.Label(self.pomo_card, text="POMODORO WORKSPACE", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.text_muted)
        self.pomo_title.pack(anchor="w")
        
        self.pomo_clock = tk.Label(self.pomo_card, text="25:00", font=("Segoe UI", 24, "bold"), bg=self.bg_card, fg=self.color_select)
        self.pomo_clock.pack(pady=4)
        
        self.pomo_btn_frame = tk.Frame(self.pomo_card, bg=self.bg_card)
        self.pomo_btn_frame.pack(fill="x", pady=(2, 0))
        self.pomo_btn_frame.columnconfigure(0, weight=1)
        self.pomo_btn_frame.columnconfigure(1, weight=1)
        
        self.pomo_start_btn = tk.Button(self.pomo_btn_frame, text="Start Focus", command=self.toggle_timer, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2")
        self.pomo_start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=4)
        
        self.pomo_reset_btn = tk.Button(self.pomo_btn_frame, text="Reset", command=self.reset_timer, bg="#1e293b", fg="#ff5555", font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2")
        self.pomo_reset_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), ipady=4)

        # --- COLUMN 2: MIDDLE PANEL (Matrix Reminders & 7-Day Agenda) ---
        self.middle_panel = tk.Frame(root, bg=self.bg_card, padx=18, pady=20)
        self.middle_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=25)
        
        self.middle_panel.columnconfigure(0, weight=1)
        self.middle_panel.rowconfigure(5, weight=3, uniform="mid_stack")
        self.middle_panel.rowconfigure(7, weight=3, uniform="mid_stack")
        
        self.date_label = tk.Label(self.middle_panel, text="", font=("Segoe UI", 15, "bold"), bg=self.bg_card, fg=self.color_select, anchor="w")
        self.date_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.input_label = tk.Label(self.middle_panel, text="CREATE REMINDER EVENT & PRIORITY", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.text_muted, anchor="w")
        self.input_label.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        
        self.reminder_entry = tk.Entry(self.middle_panel, font=("Segoe UI", 11), bg="#1f2430", fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground="#2f3647", highlightthickness=1)
        self.reminder_entry.grid(row=2, column=0, sticky="ew", ipady=6, pady=(0, 8))
        self.reminder_entry.bind("<Return>", lambda event: self.add_reminder())
        
        # Priority Picker Matrix Segment
        self.priority_var = tk.StringVar(value="Normal")
        self.priority_frame = tk.Frame(self.middle_panel, bg=self.bg_card)
        self.priority_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        for idx, p_opt in enumerate(["Urgent & Important", "Important (Q2)", "Normal"]):
            rb = tk.Radiobutton(self.priority_frame, text=p_opt, variable=self.priority_var, value=p_opt, bg=self.bg_card, fg=self.text_main, selectcolor="#11141a", font=("Segoe UI", 8), activebackground=self.bg_card, activeforeground=self.color_select)
            rb.pack(side="left", padx=(0, 12))
            
        self.btn_grid = tk.Frame(self.middle_panel, bg=self.bg_card)
        self.btn_grid.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self.btn_grid.columnconfigure(0, weight=1)
        self.btn_grid.columnconfigure(1, weight=1)
        
        self.add_btn = tk.Button(self.btn_grid, text="Save Event", command=self.add_reminder, bg=self.color_select, fg="#0a0c10", font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2")
        self.add_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=5)
        
        self.del_btn = tk.Button(self.btn_grid, text="Delete Item", command=self.delete_reminder, bg="#212634", fg="#ff5555", font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2")
        self.del_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), ipady=5)
        
        self.reminder_listbox = tk.Listbox(self.middle_panel, font=("Segoe UI", 11), bg="#11141a", fg=self.text_main, bd=1, highlightthickness=1, highlightbackground="#1f2430", highlightcolor="#1f2430", selectbackground="#1f2430", selectforeground=self.color_select, activestyle="none")
        self.reminder_listbox.grid(row=5, column=0, sticky="nsew", pady=(0, 12))
        
        self.weekly_label = tk.Label(self.middle_panel, text="UPCOMING 7-DAY AGENDA (INTERACTIVE)", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.text_muted, anchor="w")
        self.weekly_label.grid(row=6, column=0, sticky="ew", pady=(0, 4))
        
        self.scroll_canvas = tk.Canvas(self.middle_panel, bg="#0d1117", bd=1, highlightthickness=1, highlightbackground="#1f2430")
        self.weekly_frame = tk.Frame(self.scroll_canvas, bg="#0d1117")
        self.weekly_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
        self.scroll_canvas.create_window((0, 0), window=self.weekly_frame, anchor="nw", width=360)
        self.scroll_canvas.grid(row=7, column=0, sticky="nsew")

        # --- COLUMN 3: RIGHT PANEL (Habits & Graphics & Report Generator) ---
        self.right_panel = tk.Frame(root, bg=self.bg_card, padx=18, pady=20)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(10, 16), pady=25)
        
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(4, weight=5, uniform="right_panel_stack") 
        self.right_panel.rowconfigure(6, weight=4, uniform="right_panel_stack") 
        
        # Top Title Layout incorporating the new global Analysis Exporter Button
        self.habit_header_frame = tk.Frame(self.right_panel, bg=self.bg_card)
        self.habit_header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.habit_header_frame.columnconfigure(0, weight=1)
        
        self.habit_title = tk.Label(self.habit_header_frame, text="HABIT TRACKER", font=("Segoe UI", 15, "bold"), bg=self.bg_card, fg=self.color_habit_accent, anchor="w")
        self.habit_title.grid(row=0, column=0, sticky="w")
        
        self.report_btn = tk.Button(self.habit_header_frame, text="📊 Export Analysis", command=self.generate_monthly_report, bg="#1e1b4b", fg=self.color_habit_accent, font=("Segoe UI", 8, "bold"), bd=0, relief="flat", cursor="hand2", padx=8)
        self.report_btn.grid(row=0, column=1, sticky="e")
        
        self.habit_input_lbl = tk.Label(self.right_panel, text="DEFINE NEW DAILY ROUTINE", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.text_muted, anchor="w")
        self.habit_input_lbl.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        
        self.habit_entry = tk.Entry(self.right_panel, font=("Segoe UI", 11), bg="#1f2430", fg=self.text_main, bd=0, insertbackground=self.text_main, highlightbackground="#2f3647", highlightthickness=1)
        self.habit_entry.grid(row=2, column=0, sticky="ew", ipady=6, pady=(0, 8))
        self.habit_entry.bind("<Return>", lambda event: self.add_habit())
        
        self.habit_btn_grid = tk.Frame(self.right_panel, bg=self.bg_card)
        self.habit_btn_grid.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.habit_btn_grid.columnconfigure(0, weight=1)
        self.habit_btn_grid.columnconfigure(1, weight=1)
        
        self.add_habit_btn = tk.Button(self.habit_btn_grid, text="Add Habit", command=self.add_habit, bg=self.color_habit_accent, fg="#0a0c10", font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2")
        self.add_habit_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=5)
        
        self.del_habit_btn = tk.Button(self.habit_btn_grid, text="Delete Habit", command=self.delete_habit, bg="#212634", fg="#ff5555", font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2")
        self.del_habit_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), ipady=5)

        self.habit_canvas = tk.Canvas(self.right_panel, bg="#0d1117", bd=1, highlightthickness=1, highlightbackground="#1f2430")
        self.habit_frame = tk.Frame(self.habit_canvas, bg="#0d1117")
        self.habit_canvas.bind("<Configure>", lambda e: self.habit_canvas.configure(scrollregion=self.habit_canvas.bbox("all")))
        self.habit_canvas.create_window((0, 0), window=self.habit_frame, anchor="nw", width=360)
        self.habit_canvas.grid(row=4, column=0, sticky="nsew", pady=(0, 12))
        
        self.analysis_lbl = tk.Label(self.right_panel, text="7-DAY COMPLETION ANALYSIS GRAPH", font=("Segoe UI", 8, "bold"), bg=self.bg_card, fg=self.text_muted, anchor="w")
        self.analysis_lbl.grid(row=5, column=0, sticky="ew", pady=(0, 4))
        
        self.graph_canvas = tk.Canvas(self.right_panel, bg="#0d1117", bd=1, highlightthickness=1, highlightbackground="#1f2430")
        self.graph_canvas.grid(row=6, column=0, sticky="nsew")
        
        # Startup App Configurations
        self.setup_calendar_tags()
        self.update_date_header()
        self.refresh_reminder_list()
        self.refresh_weekly_agenda()
        self.refresh_habit_matrix()

    # --- Gamification Engine Framework ---

    def add_xp(self, amount):
        """Appends experience units and displays smooth rank calculations."""
        self.data["gamification"]["xp"] += amount
        xp_needed = self.data["gamification"]["level"] * 100
        
        if self.data["gamification"]["xp"] >= xp_needed:
            self.data["gamification"]["xp"] -= xp_needed
            self.data["gamification"]["level"] += 1
            messagebox.showinfo("LEVEL UP!", f"🎉 Incredible work! You've reached Level {self.data['gamification']['level']}!")
            
        self.save_data()
        self.update_xp_bar_display()

    def update_xp_bar_display(self):
        current_lvl = self.data["gamification"]["level"]
        current_xp = self.data["gamification"]["xp"]
        xp_target = current_lvl * 100
        
        self.lvl_lbl.config(text=f"LEVEL {current_lvl}  ({current_xp}/{xp_target} XP)")
        self.xp_progress["value"] = (current_xp / xp_target) * 100

    # --- Pomodoro Focus Workspace Logic ---

    def toggle_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.pomo_start_btn.config(text="Resume Focus", bg="#1e293b")
        else:
            self.timer_running = True
            self.pomo_start_btn.config(text="Pause Timer", bg="#ef4444")
            self.run_timer_tick()

    def run_timer_tick(self):
        if not self.timer_running:
            return
            
        if self.timer_seconds_left > 0:
            self.timer_seconds_left -= 1
            mins, secs = divmod(self.timer_seconds_left, 60)
            self.pomo_clock.config(text=f"{mins:02d}:{secs:02d}")
            self.root.after(1000, self.run_timer_tick)
        else:
            # Current time block is completed
            self.timer_running = False
            if self.timer_mode == "Focus":
                messagebox.showinfo("Focus Complete!", "Excellent session block. Grab a short 5-minute break!")
                self.add_xp(35)  # Award large XP payload for focused sessions
                self.timer_mode = "Break"
                self.timer_seconds_left = 5 * 60
                self.pomo_clock.config(text="05:00", fg=self.color_today_fg)
            else:
                messagebox.showinfo("Break Over", "Time to jump back into action. Let's start focusing!")
                self.timer_mode = "Focus"
                self.timer_seconds_left = 25 * 60
                self.pomo_clock.config(text="25:00", fg=self.color_select)
            self.pomo_start_btn.config(text="Start Focus", bg="#1e293b")

    def reset_timer(self):
        self.timer_running = False
        self.timer_mode = "Focus"
        self.timer_seconds_left = 25 * 60
        self.pomo_clock.config(text="25:00", fg=self.color_select)
        self.pomo_start_btn.config(text="Start Focus", bg="#1e293b")

    # --- Visual Style Tags Core Setup ---

    def setup_calendar_tags(self):
        self.cal.calevent_remove("all")
        self.cal.tag_config("today_style", background=self.color_today_bg, foreground=self.color_today_fg, font=("Segoe UI", 10, "bold"))
        self.cal.tag_config("scheduled_style", background=self.color_event, foreground="#0a0c10", font=("Segoe UI", 10, "bold"))
        self.apply_dynamic_highlights()

    def apply_dynamic_highlights(self, event=None):
        self.cal.calevent_remove("all")
        today_date = datetime.today().date()
        self.cal.calevent_create(today_date, "Today", "today_style")
        
        for date_str in self.data["reminders"].keys():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj != today_date:
                    self.cal.calevent_create(date_obj, "Reminder", "scheduled_style")
            except ValueError:
                continue

    # --- Storage Pipelines Engine ---

    def load_data(self):
        default_structure = {"reminders": {}, "habits": {}, "gamification": {"level": 1, "xp": 0}}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    content = json.load(f)
                    if "gamification" not in content:
                        content["gamification"] = {"level": 1, "xp": 0}
                    return content
            except json.JSONDecodeError:
                return default_structure
        return default_structure

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def on_date_select(self, event=None):
        self.update_date_header()
        self.refresh_reminder_list()
        self.refresh_weekly_agenda()
        self.refresh_habit_matrix()

    def update_date_header(self):
        raw_date = self.cal.get_date()
        date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
        self.date_label.config(text=date_obj.strftime("%A, %b %d"))

    # --- Reminders & Priority Matrix Controller Logic ---

    def refresh_reminder_list(self):
        self.reminder_listbox.delete(0, tk.END)
        selected_date = self.cal.get_date()
        
        if selected_date in self.data["reminders"]:
            for item in self.data["reminders"][selected_date]:
                # Dynamic visual text checks based on priority states
                if isinstance(item, dict):
                    text = item["text"]
                    priority = item.get("priority", "Normal")
                else:
                    text = item
                    priority = "Normal"
                    
                prefix = "🚨 [Q1]" if priority == "Urgent & Important" else "🔶 [Q2]" if priority == "Important (Q2)" else "⚡"
                self.reminder_listbox.insert(tk.END, f"  {prefix} {text}")

    def refresh_weekly_agenda(self):
        for widget in self.weekly_frame.winfo_children():
            widget.destroy()
            
        raw_selected_date = self.cal.get_date()
        start_date = datetime.strptime(raw_selected_date, "%Y-%m-%d").date()
        items_found = False
        row_idx = 0
        
        for i in range(7):
            current_loop_date = start_date + timedelta(days=i)
            date_str_key = current_loop_date.strftime("%Y-%m-%d")
            
            if date_str_key in self.data["reminders"]:
                items_found = True
                day_heading = current_loop_date.strftime("%A (%b %d)")
                
                lbl = tk.Label(self.weekly_frame, text=f"■ {day_heading}", font=("Segoe UI", 9, "bold"), bg="#0d1117", fg="#ffd700", anchor="w")
                lbl.grid(row=row_idx, column=0, sticky="ew", padx=8, pady=(6, 2))
                row_idx += 1
                
                for item in self.data["reminders"][date_str_key]:
                    text = item["text"] if isinstance(item, dict) else item
                    var = tk.BooleanVar(value=False)
                    
                    cb = tk.Checkbutton(
                        self.weekly_frame, text=text, variable=var,
                        command=lambda v=var: self.add_xp(15) if v.get() else None,
                        bg="#0d1117", fg="#cbd5e1", selectcolor="#141822", activebackground="#0d1117",
                        activeforeground="#ffffff", font=("Segoe UI", 10), anchor="w", justify="left", wraplength=310
                    )
                    cb.grid(row=row_idx, column=0, sticky="ew", padx=(24, 8), pady=1)
                    row_idx += 1
                    
        if not items_found:
            no_task_lbl = tk.Label(self.weekly_frame, text="  No tasks found for this 7-day bracket.", font=("Segoe UI", 10), bg="#0d1117", fg="#6272a4", anchor="w")
            no_task_lbl.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

    def add_reminder(self):
        selected_date = self.cal.get_date()
        reminder_text = self.reminder_entry.get().strip()
        priority_setting = self.priority_var.get()
        
        if not reminder_text:
            messagebox.showwarning("Entry Error", "Task text entry field cannot be empty.")
            return
            
        if selected_date not in self.data["reminders"]:
            self.data["reminders"][selected_date] = []
            
        self.data["reminders"][selected_date].append({
            "text": reminder_text,
            "priority": priority_setting
        })
        
        self.save_data()
        self.refresh_reminder_list()
        self.refresh_weekly_agenda()
        self.apply_dynamic_highlights()
        self.reminder_entry.delete(0, tk.END)

    def delete_reminder(self):
        selected_date = self.cal.get_date()
        selected_indices = self.reminder_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("Selection Error", "Please select an item line to delete.")
            return
            
        index = selected_indices[0]
        del self.data["reminders"][selected_date][index]
        
        if not self.data["reminders"][selected_date]:
            del self.data["reminders"][selected_date]
            
        self.save_data()
        self.refresh_reminder_list()
        self.refresh_weekly_agenda()
        self.apply_dynamic_highlights()

    # --- Habit Tracker Matrix & Analytics Output System ---

    def refresh_habit_matrix(self):
        for widget in self.habit_frame.winfo_children():
            widget.destroy()
            
        selected_date = self.cal.get_date()
        habits_dict = self.data["habits"]
        
        if not habits_dict:
            empty_lbl = tk.Label(self.habit_frame, text=" No routine habits defined yet.\n Create your first habit above!", font=("Segoe UI", 10), bg="#0d1117", fg="#6272a4", justify="left", anchor="w")
            empty_lbl.grid(row=0, column=0, padx=12, pady=15)
            self.draw_performance_graph()
            return

        row_idx = 0
        for habit_name, logs in habits_dict.items():
            is_done = logs.get(selected_date, False)
            var = tk.BooleanVar(value=is_done)
            
            current_streak = self.calculate_streak(habit_name, selected_date)
            streak_text = f"🔥 {current_streak} days" if current_streak > 0 else "—"

            row_frame = tk.Frame(self.habit_frame, bg="#0d1117")
            row_frame.grid(row=row_idx, column=0, sticky="ew", padx=10, pady=4)
            row_frame.columnconfigure(0, weight=1)
            
            cb = tk.Checkbutton(
                row_frame, text=habit_name, variable=var,
                command=lambda h=habit_name, v=var: self.toggle_habit_log(h, v),
                bg="#0d1117", fg="#ffffff" if is_done else "#a0aec0", selectcolor="#141822",
                activebackground="#0d1117", activeforeground=self.color_habit_accent,
                font=("Segoe UI", 11, "bold" if is_done else "normal"), anchor="w", justify="left", wraplength=210
            )
            cb.grid(row=0, column=0, sticky="w")
            
            streak_lbl = tk.Label(row_frame, text=streak_text, font=("Segoe UI", 9, "bold"), bg="#1a202c" if current_streak > 0 else "#0d1117", fg=self.color_streak if current_streak > 0 else self.text_muted, padx=6, pady=2)
            streak_lbl.grid(row=0, column=1, sticky="e", padx=(10, 5))
            
            row_idx += 1
            
        self.draw_performance_graph()

    def draw_performance_graph(self):
        self.graph_canvas.delete("all")
        habits_dict = self.data["habits"]
        if not habits_dict:
            self.graph_canvas.create_text(175, 50, text="No trackable metrics log present.", fill="#6272a4", font=("Segoe UI", 10))
            return

        raw_selected_date = self.cal.get_date()
        center_date = datetime.strptime(raw_selected_date, "%Y-%m-%d").date()
        
        start_y, row_spacing, bar_max_width, graph_start_x = 18, 26, 150, 115
        
        for idx, (habit_name, logs) in enumerate(habits_dict.items()):
            current_y = start_y + (idx * row_spacing)
            if current_y > 110:
                break
                
            completed_days = sum(1 for i in range(7) if logs.get((center_date - timedelta(days=i)).strftime("%Y-%m-%d"), False))
            ratio = completed_days / 7.0
            percentage = int(ratio * 100)
            
            display_name = habit_name if len(habit_name) <= 12 else habit_name[:10] + ".."
            self.graph_canvas.create_text(12, current_y, text=display_name, fill="#ffffff", font=("Segoe UI", 9, "bold"), anchor="w")
            self.graph_canvas.create_rectangle(graph_start_x, current_y - 5, graph_start_x + bar_max_width, current_y + 5, fill="#1f2430", outline="")
            
            fill_w = int(bar_max_width * ratio)
            if fill_w > 0:
                self.graph_canvas.create_rectangle(graph_start_x, current_y - 5, graph_start_x + fill_w, current_y + 5, fill=self.color_graph_bar, outline="")
                
            self.graph_canvas.create_text(graph_start_x + bar_max_width + 8, current_y, text=f"{percentage}%", fill=self.color_habit_accent if percentage > 0 else "#6272a4", font=("Segoe UI", 8, "bold"), anchor="w")

    def toggle_habit_log(self, habit_name, var_ref):
        selected_date = self.cal.get_date()
        checked_status = var_ref.get()
        
        self.data["habits"][habit_name][selected_date] = checked_status
        if checked_status:
            self.add_xp(15)  # Reward XP status for discipline goals met
        else:
            self.save_data()
            
        self.refresh_habit_matrix()

    def calculate_streak(self, habit_name, base_date_str):
        logs = self.data["habits"].get(habit_name, {})
        current_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
        streak = 0
        while logs.get(current_date.strftime("%Y-%m-%d"), False):
            streak += 1
            current_date -= timedelta(days=1)
        return streak

    def add_habit(self):
        habit_text = self.habit_entry.get().strip()
        if not habit_text or habit_text in self.data["habits"]:
            return
        self.data["habits"][habit_text] = {}
        self.save_data()
        self.refresh_habit_matrix()
        self.habit_entry.delete(0, tk.END)

    def delete_habit(self):
        habits_list = list(self.data["habits"].keys())
        if not habits_list: return
            
        pop = tk.Toplevel(self.root)
        pop.title("Delete Routine")
        pop.geometry("300x130")
        pop.configure(bg=self.bg_card)
        
        chosen_habit = tk.StringVar()
        dropdown = ttk.Combobox(pop, textvariable=chosen_habit, values=habits_list, state="readonly")
        dropdown.pack(pady=15, padx=20, fill="x")
        dropdown.current(0)
        
        def run_del():
            if chosen_habit.get() in self.data["habits"]:
                del self.data["habits"][chosen_habit.get()]
                self.save_data()
                self.refresh_habit_matrix()
            pop.destroy()
            
        tk.Button(pop, text="Confirm Delete", command=run_del, bg="#ff5555", fg="#ffffff", bd=0).pack(pady=5, fill="x", padx=20)

    # --- Monthly Report Generation & Markdown File Exporter Engine ---

    def generate_monthly_report(self):
        """Compiles calendar statistics, priorities, routines, and XP progress metrics into a local text report."""
        today_str = datetime.today().strftime("%Y-%m-%d")
        report_path = "Monthly_Productivity_Report.txt"
        
        total_tasks = sum(len(v) for v in self.data["reminders"].values())
        total_habits_tracked = len(self.data["habits"])
        
        report_content = f"""# PERFORMANCE SYSTEM ANALYSIS REPORT
Generated on: {today_str}
===========================================

## LEVEL INDEX PROFILE STATUS
* Current Profile Ranking Level: {self.data['gamification']['level']}
* Banked Core Experience Points: {self.data['gamification']['xp']} XP

## REMINDERS LOG DATABASE STATISTICS
* Total Unique Task Events Logged: {total_tasks} item entities mapped

## DAFULY ROUTINE HABIT MATRICES ANALYSIS
* Total Tracked Routines Monitored: {total_habits_tracked} items currently defined
"""
        for habit, logs in self.data["habits"].items():
            completed_ticks = sum(1 for v in logs.values() if v)
            report_content += f"  ↳ Habit: '{habit}' -> {completed_ticks} absolute operational days checked off.\n"

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            messagebox.showinfo("Report Exported", f"Successfully compiled global statistics dashboard into standard file location:\n➡ {report_path}")
        except Exception as e:
            messagebox.showerror("Export Failure", f"Could not create storage logs: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HighContrastDashboardApp(root)
    root.mainloop()