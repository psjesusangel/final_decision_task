"""
gui.py
Graphical user interface using tkinter and ttk (standard GUI python libraries)
Contains all window/frames and navigation logic
"""

import tkinter as tk
from tkinter import ttk
import random
import time
from datetime import datetime

from config import (
    MIN_PRESS_INTERVAL, ITI_RANGE, EASY_CLICKS_REQUIRED, CALIBRATION_DURATION,
    PRACTICE_TRIALS
)
from utils import save_data, logger


class ExperimentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        logger.info("Initializing ExperimentApp")
        self.title("Effort-Based Decision Task")
        self.state("zoomed")  # start maximized
        self.minsize(800, 600)
        self.configure(bg="#2e2e2e")

        # Initialize ttk style
        style = ttk.Style(self)
        try:
            style.theme_use('aqua')  # Mac OS X only; native Mac OS X
        except tk.TclError:
            style.theme_use('clam')

        # Experiment state
        self.subject = None
        self.handedness = None
        self.domain = "Money"  # default for now, implement food later
        self.valence = "Loss"
        self.chose_practice_trials = False
        self.calibration_presses_right = 0
        self.calibration_presses_left = 0
        self.hard_clicks_required = 0
        self.data = []  # collected trial rows

        # Setup container for frames
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        
        # Configure the container for centering
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        # Initialize all frames
        self.frames = {}
        for F in (InfoEntryFrame, InstructionsFrame, RightCalibrationFrame, LeftCalibrationFrame, PracticeTrialsFrame, EndFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(InfoEntryFrame)

    def show_frame(self, frame_class):
        """Switch to given frame"""
        frame = self.frames[frame_class]
        frame.tkraise()
        logger.info("Switched to frame: %s", frame_class.__name__)

    def save_data(self):
        """Delegate to utility to save CSV"""
        save_data(self.subject, self.domain, self.valence, self.data)


class InfoEntryFrame(ttk.Frame):
    """Frame for entering subject info"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure the frame for centering
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create a centered content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0)

        # Subject Number
        ttk.Label(content_frame, text="Subject Number:").pack(pady=10)
        self.subject_entry = ttk.Entry(content_frame)
        self.subject_entry.pack()

        # Domain selection: F=Food, M=Monetary
        ttk.Label(content_frame, text="Domain (F/M):").pack(pady=10)
        self.domain_combo = ttk.Combobox(
            content_frame, values=['F', 'M'], state='readonly'
        )
        self.domain_combo.pack()

        # Valence selection: G=Gain, L=Loss
        ttk.Label(content_frame, text="Valence (G/L):").pack(pady=10)
        self.valence_combo = ttk.Combobox(
            content_frame, values=['G', 'L'], state='readonly'
        )
        self.valence_combo.pack()

        # Handedness
        ttk.Label(content_frame, text="Handedness (Left/Right):").pack(pady=10)
        self.handedness_combo = ttk.Combobox(
            content_frame, values=['Left', 'Right'], state='readonly'
        )
        self.handedness_combo.pack()

        # Practice trials? Y/N
        ttk.Label(content_frame, text="Practice trials? (Y/N):").pack(pady=10)
        self.practice_trials_combo = ttk.Combobox(
            content_frame, values=['Y', 'N'], state='readonly'
        )
        self.practice_trials_combo.pack()

        ttk.Button(content_frame, text="Next", command=self.on_next).pack(pady=20)

    def on_next(self):
        subj = self.subject_entry.get().strip()
        domain = self.domain_combo.get().strip()
        valence = self.valence_combo.get().strip()
        hand = self.handedness_combo.get().strip()
        practice = self.practice_trials_combo.get().strip()

        # ERROR HANDLING: Only proceed if all entries provided
        if subj and domain and valence and hand and practice:
            self.controller.subject = subj
            # Map shorthand to full domain
            self.controller.domain = 'Food' if domain == 'F' else 'Money'
            # Map shorthand to full valence
            self.controller.valence = 'Gain' if valence == 'G' else 'Loss'
            self.controller.handedness = hand
            self.controller.chose_practice_trials = (practice == 'Y')

            logger.info(
                "Subject info: %s, Domain=%s, Valence=%s, Handedness=%s, Practice=%s",
                subj,
                self.controller.domain,
                self.controller.valence,
                hand,
                practice
            )
            # Go to instructions for Calibration task
            self.controller.show_frame(InstructionsFrame)
        else:
            # TODO: show UI error feedback if any field is missing
            logger.warning("Incomplete info fields: %s, %s, %s, %s, %s",
                           subj, domain, valence, hand, practice)
            

class InstructionsFrame(ttk.Frame):
    """Frame for displaying general calibration instructions"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure the frame for centering
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create a centered content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0)
        
        self.instruction_text = ttk.Label(
            content_frame,
            text=(
                "Calibration Instructions\n\n"
                "The next screen will ask you to press the RIGHT arrow key with your non-\n"
                "dominant pinky as fast as possible for " + str(CALIBRATION_DURATION) + " seconds.\n\n" 
                "The screen following that will ask you to press the LEFT arrow key with your non-\n"
                "dominant pinky as fast as possible for " + str(CALIBRATION_DURATION) + " seconds.\n\n"
                "Your responses will be recorded and used during the following experiment.\n\n"
                "Press each key individually. Holding down a key will only count as one press."
            ),
            wraplength=600,
            justify="center"
        )
        self.instruction_text.pack(pady=30)
        
        self.start_btn = ttk.Button(
            content_frame,
            text="I understand, start calibration",
            command=self.proceed_to_calibration
        )
        self.start_btn.pack(pady=20)
    
    def proceed_to_calibration(self):
        """Go to the right calibration frame"""
        self.controller.show_frame(RightCalibrationFrame)

# Base class for calibration 
class CalibrationBaseFrame(ttk.Frame):
    """Base frame for calibration tests - contains common functionality"""
    def __init__(self, parent, controller, side, next_frame_class):
        super().__init__(parent)
        self.controller = controller
        self.side = side  # 'Right' or 'Left'
        self.next_frame_class = next_frame_class
        self.count = 0
        self.key_pressed = False  # Track if key is currently pressed
        self._last_count_time = 0.0
        
        # Configure the frame for centering
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create a centered content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0)
        
        self.label = ttk.Label(
            content_frame,
            text=f"You will now perform the {self.side.upper()} arrow calibration test.\nWhen you're ready, click the button below to start.",
            wraplength=600
        )
        self.label.pack(pady=20)
        
        self.countdown_label = ttk.Label(
            content_frame,
            text="",
            font=("Arial", 24, "bold")
        )
        
        self.count_label = ttk.Label(content_frame, text="")
        self.timer_label = ttk.Label(content_frame, text="")
        
        # Container for button
        self.button_container = ttk.Frame(content_frame)
        self.button_container.pack(pady=20)
        
        # Add start button for calibration test
        ttk.Button(
            self.button_container,
            text=f"Start {self.side.upper()} Arrow Test",
            command=self.start_test
        ).pack()
    
    def start_test(self):
        """Start the calibration test"""
        # Clear the button container
        for widget in self.button_container.winfo_children():
            widget.destroy()
        self.button_container.pack_forget()
        
        # Show countdown
        self.countdown_label.pack(pady=20)
        self.start_countdown()
    
    def start_countdown(self):
        """Begin the 3-second countdown"""
        logger.info(f"Starting countdown for {self.side} key test")
        self.label.config(text=f"Get ready to press the {self.side.upper()} arrow key...")
        self._do_countdown(3)
    
    def _do_countdown(self, count):
        """Recursive countdown function"""
        if count > 0:
            self.countdown_label.config(text=str(count))
            self.after(1000, lambda: self._do_countdown(count - 1))
        else:
            self.countdown_label.config(text="GO!")
            self.after(500, self.start_calibration)
    
    def start_calibration(self):
        """Begin the actual calibration test"""
        self.count = 0
        self.countdown_label.pack_forget()
        self.count_label.pack()
        self.timer_label.pack()
        
        logger.info(f"{self.side} calibration test started")
        
        prompt = (
            f"Press {self.side.upper()} arrow key as fast as possible for "
            f"{CALIBRATION_DURATION}s."
        )
        self.label.config(text=prompt)
        
        # Bind both key press and key release events
        self.bind_all('<KeyPress>', self.on_key_press)
        self.bind_all('<KeyRelease>', self.on_key_release)
        
        # Start the timer
        self._run_timer(time.time(), time.time() + CALIBRATION_DURATION)
    
    def _run_timer(self, start, end):
        now = time.time()
        if now >= end:
            # Unbind key events when timer ends
            self.unbind_all('<KeyPress>')
            self.unbind_all('<KeyRelease>')
            
            # Save the result and finish
            self.finish_calibration()
        else:
            remaining = end - now
            self.count_label.config(text=f"Count: {self.count}")
            self.timer_label.config(text=f"Time: {remaining:.1f}s")
            self.after(50, lambda: self._run_timer(start, end))
            
    def finish_calibration(self):
        """Must be implemented by subclasses to handle completion"""
        raise NotImplementedError("Subclasses must implement finish_calibration")
    
    def on_key_press(self, event):
        """Handle key press, but only count if key wasn't already pressed"""
        if event.keysym == self.side and not self.key_pressed:
            # Mark that the key is down; we'll count on the release
            logger.info(f"Key pressed down")
            self.key_pressed = True
    
    def on_key_release(self, event):
        """Handle key release to reset the key state"""
        if event.keysym == self.side and self.key_pressed:
            now = time.time()
            if now - self._last_count_time > MIN_PRESS_INTERVAL:
                self.count += 1
                self._last_count_time = now
                logger.info(f"Count incremented to: {self.count}")
            self.key_pressed = False

class RightCalibrationFrame(CalibrationBaseFrame):
    """Frame for RIGHT arrow calibration"""
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Right", LeftCalibrationFrame)
    
    def finish_calibration(self):
        """Handle completion of the RIGHT calibration"""
        self.controller.calibration_presses_right = self.count
        logger.info(f"Right presses: {self.count}")
        
        # Show results and continue button
        self.count_label.pack_forget()
        self.timer_label.pack_forget()
        
        result_text = (
            f"RIGHT arrow test complete!\n\n"
            f"You made {self.count} key presses.\n\n"
            f"Next, you will perform the same test with the LEFT arrow key.\n"
            f"When you're ready, click the button below to start the LEFT arrow test."
        )
        self.label.config(text=result_text)
        
        # Add a continue button
        self.button_container.pack(pady=20)
        ttk.Button(
            self.button_container,
            text="Continue to LEFT Arrow Test",
            command=lambda: self.controller.show_frame(LeftCalibrationFrame)
        ).pack()


class LeftCalibrationFrame(CalibrationBaseFrame):
    """Frame for LEFT arrow calibration"""
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Left", PracticeTrialsFrame)
    
    def finish_calibration(self):
        """Handle completion of the LEFT calibration"""
        self.controller.calibration_presses_left = self.count
        total = (
            self.controller.calibration_presses_right + self.count
        ) * 0.8
        self.controller.hard_clicks_required = int(total)
        
        logger.info(f"Left presses: {self.count}")
        logger.info(
            "Hard clicks requirement set to: %d",
            self.controller.hard_clicks_required
        )
        
        # Show results and continue button
        self.count_label.pack_forget()
        self.timer_label.pack_forget()
        
        result_text = (
            f"Calibration complete!\n\n"
            f"RIGHT arrow: {self.controller.calibration_presses_right} presses\n"
            f"LEFT arrow: {self.controller.calibration_presses_left} presses\n\n"
            f"Hard task will require {self.controller.hard_clicks_required} presses."
        )
        self.label.config(text=result_text)
        
        # Add continue button
        self.button_container.pack(pady=20)
        ttk.Button(
            self.button_container,
            text="Proceed to Practice Trials",
            command=lambda: self.controller.show_frame(PracticeTrialsFrame)
        ).pack()


class PracticeTrialsFrame(ttk.Frame):
    """Frame to run practice trials with combo‐box choice and continue button"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.trial_index = 0
        self.stage = None
        self.choice_time = None
        self.choice = None
        self.choice_rt = None
        self.clicks = 0
        self.clicks_req = 0
        self.duration = 0.0
        self.key_pressed = {}  # for counting task clicks
        self._last_click_time = 0.0

        # layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        content = ttk.Frame(self)
        content.grid(row=0, column=0)

        # static instruction about the endowment
        ttk.Label(
            content,
            text="You will start this task with an $8 endowment.\n"
                 "On each trial, choose to complete an easy task or a hard task.",
            wraplength=600,
            justify="center"
        ).pack(pady=(20, 10))

        # dynamic trial prompt
        self.instr = ttk.Label(content, text="", wraplength=600, justify="center")
        self.instr.pack(pady=10)

        # choice combo and button
        self.choice_var = tk.StringVar()
        self.choice_combo = ttk.Combobox(
            content, textvariable=self.choice_var, state="readonly", width=30
        )
        self.choice_btn = ttk.Button(content, text="Continue", command=self.on_choice)

        # progress bar for the task
        self.progress = ttk.Progressbar(
            content, orient="horizontal", length=400, mode="determinate"
        )

        # keep key bindings for the task phase
        self.bind_all('<KeyPress>', self.on_key_press)
        self.bind_all('<KeyRelease>', self.on_key_release)

        logger.info("PracticeTrialsFrame initialized")
        self.load_trial()

    def load_trial(self):
        if self.trial_index >= len(PRACTICE_TRIALS):
            logger.info("All practice trials complete")
            self.controller.save_data()
            self.controller.show_frame(EndFrame)
            return

        self.current = PRACTICE_TRIALS[self.trial_index]
        self.stage = 'choice'
        self.choice_time = time.time()

        hard_amt = self.current['magnitude_hard']
        loss_prob = int(self.current['prob'] * 100)
        prompt = (
            f"Practice Trial {self.trial_index + 1}\n\n"
            f"Easy: pay $4 (100% success)\n"
            f"Hard: pay ${hard_amt:.2f} (loss {loss_prob}% chance)\n\n"
            "Select your option below and click Continue."
        )
        self.instr.config(text=prompt)

        # configure and show the combo + button
        easy_label = "Easy: -$4"
        hard_label = f"Hard: ${hard_amt:.2f}"
        self.choice_combo.config(values=[easy_label, hard_label])
        self.choice_var.set("")  # clear selection
        self.choice_combo.pack(pady=5)
        self.choice_btn.pack(pady=(5, 20))

        # hide progress bar until task starts
        self.progress.pack_forget()

    def on_choice(self):
        selection = self.choice_var.get()
        if not selection:
            return  # no choice made

        # record response time and set up task parameters
        rt = time.time() - self.choice_time
        self.choice = 'Easy' if selection.startswith("Easy") else 'Hard'
        self.choice_rt = rt
        self.clicks = 0
        if self.choice == 'Easy':
            self.clicks_req = EASY_CLICKS_REQUIRED
            self.duration = 7.0
        else:
            self.clicks_req = self.controller.hard_clicks_required
            self.duration = 21.0

        logger.info(
            "Trial %d choice: %s (RT=%.3f)",
            self.trial_index + 1, self.choice, rt
        )

        # hide choice widgets
        self.choice_combo.pack_forget()
        self.choice_btn.pack_forget()

        # show and reset progress bar
        self.progress['value'] = 0
        self.progress.pack(pady=10)

        # begin the task
        self.stage = 'task'
        self.task_start = time.time()
        self.task_end = self.task_start + self.duration
        self.after(50, self.run_task)

    def on_key_press(self, event):
        if self.stage == 'task':
            key = event.keysym.lower()
            valid = ['space'] if self.choice == 'Easy' else ['left', 'right']
            if key in valid and not self.key_pressed.get(key, False):
                self.key_pressed[key] = True

    def on_key_release(self, event):
        if self.stage == 'task':
            key = event.keysym.lower()
            if self.key_pressed.get(key, False):
                now = time.time()
                if now - self._last_click_time > MIN_PRESS_INTERVAL:
                    self.clicks += 1
                    self._last_click_time = now
                self.key_pressed[key] = False

    def run_task(self):
        now = time.time()
        if now >= self.task_end or self.clicks >= self.clicks_req:
            complete = int(self.clicks >= self.clicks_req)
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%H:%M:%S"),
                self.controller.subject,
                self.controller.handedness,
                self.trial_index + 1,
                self.controller.domain,
                self.controller.valence,
                self.current['magnitude_hard'],
                self.current['prob'],
                round(self.current['magnitude_hard'] * self.current['prob'], 3),
                self.choice,
                round(self.choice_rt, 3),
                self.clicks_req,
                self.clicks,
                complete
            ]
            self.controller.data.append(row)
            logger.info(
                "Trial %d complete: clicks %d/%d, success=%d",
                self.trial_index + 1, self.clicks, self.clicks_req, complete
            )

            iti = random.uniform(*ITI_RANGE)
            self.instr.config(text=f"ITI... please wait {iti:.1f}s")
            self.progress['value'] = 0
            self.after(int(iti * 1000), self.next_trial)
        else:
            pct = (self.clicks / self.clicks_req) * 100
            self.progress['value'] = pct
            self.instr.config(text=f"{self.choice} task in progress: {int(pct)}%")
            self.after(50, self.run_task)

    def next_trial(self):
        self.trial_index += 1
        self.key_pressed.clear()
        self.load_trial()

class EndFrame(ttk.Frame):
    """Frame to show completion and exit."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        logger.info("EndFrame displayed")
        
        # Configure the frame for centering
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create a centered content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0)
        
        ttk.Label(
            content_frame, text="Practice complete!\nData saved.\nThank you!"
        ).pack(pady=20)
        ttk.Button(content_frame, text="Exit", command=controller.destroy).pack(pady=10)

        # TODO: Add option to restart or review data