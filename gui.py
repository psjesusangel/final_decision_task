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
    ITI_RANGE, EASY_CLICKS_REQUIRED, CALIBRATION_DURATION,
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
        self.skip_calibration_countdown = False  # Flag to skip second countdown

        # Setup container for frames
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        
        # Configure the container for centering
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        self.frames = {}

        for F in (InfoEntryFrame, InstructionsFrame, CalibrationFrame, PracticeTrialsFrame, EndFrame):
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
    """Frame for displaying calibration instructions and countdown"""
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
        
        self.countdown_label = ttk.Label(
            content_frame,
            text="",
            font=("Arial", 24, "bold")
        )
        
        self.start_btn = ttk.Button(
            content_frame,
            text="Start RIGHT Arrow Test",
            command=self.start_countdown
        )
        self.start_btn.pack(pady=20)
    
    def start_countdown(self):
        """Begin the 3-second countdown"""
        self.start_btn.pack_forget()
        self.countdown_label.pack(pady=30)
        self._do_countdown(3)
    
    def _do_countdown(self, count):
        """Recursive countdown function"""
        if count > 0:
            self.countdown_label.config(text=str(count))
            self.after(1000, lambda: self._do_countdown(count - 1))
        else:
            self.countdown_label.config(text="GO!")
            self.controller.skip_calibration_countdown = True
            self.after(500, lambda: self.controller.show_frame(CalibrationFrame))

class CalibrationFrame(ttk.Frame):
    """Frame to calibrate effort for hard task"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.step = 0
        self.count = 0
        self.key_pressed = False  # Track if key is currently pressed
        self.test_started = False  # Flag to track if test has started
        
        # Configure the frame for centering
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create a centered content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0)
        
        self.label = ttk.Label(
            content_frame,
            text="Get ready for the RIGHT arrow calibration...",
            wraplength=600
        )
        self.label.pack(pady=20)
        
        self.countdown_label = ttk.Label(
            content_frame,
            text="",
            font=("Arial", 24, "bold")
        )
        self.countdown_label.pack(pady=20)
        
        self.count_label = ttk.Label(content_frame, text="")
        self.timer_label = ttk.Label(content_frame, text="")
        
        # Container for continue button between tests
        self.button_container = ttk.Frame(content_frame)
    
    def tkraise(self):
        """Override tkraise to initialize the calibration when frame becomes visible"""
        super().tkraise()
        # Only start the test if this is the first time being shown
        if not self.test_started:
            self.test_started = True
            
            # Check if we should skip countdown (coming from instructions)
            if self.controller.skip_calibration_countdown:
                logger.info("Skipping secondary countdown, starting test directly")
                self.controller.skip_calibration_countdown = False  # Reset flag
                # Go straight to the test
                self.after(500, self.start_step)
            else:
                # Otherwise do the normal countdown
                self.after(500, self.start_countdown_for_step)

    def start_countdown_for_step(self):
        """Begin the 3-second countdown before each step"""
        side = 'RIGHT' if self.step == 0 else 'LEFT'  # step is still 0 at first
        logger.info("Starting countdown for calibration step %d (%s key)", 
                    self.step + 1, side)
        
        self.label.config(text=f"Get ready to press the {side} arrow key...")
        self._do_countdown(3)
    
    def _do_countdown(self, count):
        """Recursive countdown function"""
        if count > 0:
            self.countdown_label.config(text=str(count))
            self.after(1000, lambda: self._do_countdown(count - 1))
        else:
            self.countdown_label.config(text="GO!")
            self.after(500, self.start_step)

    def start_step(self):
        """Begin each calibration step (right then left)"""
        self.step += 1
        self.count = 0
        self.countdown_label.pack_forget()
        self.count_label.pack()
        self.timer_label.pack()
        side = 'RIGHT' if self.step == 1 else 'LEFT'
        logger.info("Calibration step %d started (%s key)", self.step, side)
        prompt = (
            f"Step {self.step}: Press {side} arrow key as fast as possible for "
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
            
            if self.step == 1:
                # First test (RIGHT) is complete
                self.controller.calibration_presses_right = self.count
                logger.info("Right presses: %d", self.count)
                
                # Show results and instructions for LEFT test
                self.count_label.pack_forget()
                self.timer_label.pack_forget()
                self.countdown_label.pack_forget()
                
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
                    text="Start LEFT Arrow Test",
                    command=self.prepare_for_left_test
                ).pack()
                
            else:
                # Second test (LEFT) is complete
                self.controller.calibration_presses_left = self.count
                total = (
                    self.controller.calibration_presses_right + self.count
                ) * 0.8
                self.controller.hard_clicks_required = int(total)
                logger.info("Left presses: %d", self.count)
                logger.info(
                    "Hard clicks requirement set to: %d",
                    self.controller.hard_clicks_required
                )
                self.count_label.pack_forget()
                self.timer_label.pack_forget()
                
                # Empty the button container
                for widget in self.button_container.winfo_children():
                    widget.destroy()
                self.button_container.pack_forget()
                
                self.label.config(
                    text=(
                        f"Calibration complete!\n\n"
                        f"RIGHT arrow: {self.controller.calibration_presses_right} presses\n"
                        f"LEFT arrow: {self.controller.calibration_presses_left} presses\n\n"
                        f"Hard task will require {self.controller.hard_clicks_required} presses."
                    )
                )
                ttk.Button(
                    self.label.master,  # Use the content frame
                    text="Proceed to Practice Trials",
                    command=lambda: self.controller.show_frame(PracticeTrialsFrame)
                ).pack(pady=20)
        else:
            remaining = end - now
            self.count_label.config(text=f"Count: {self.count}")
            self.timer_label.config(text=f"Time: {remaining:.1f}s")
            self.after(50, lambda: self._run_timer(start, end))
    
    def prepare_for_left_test(self):
        """Prepare for the LEFT arrow test after user clicks button"""
        # Remove the button
        for widget in self.button_container.winfo_children():
            widget.destroy()
        self.button_container.pack_forget()
        
        # Reset key state
        self.key_pressed = False
        
        # Start countdown for LEFT test
        self.countdown_label.pack(pady=20)
        self.start_countdown_for_step()

    def on_key_press(self, event):
        """Handle key press, but only count if key wasn't already pressed"""
        correct = 'Right' if self.step == 1 else 'Left'
        
        # Debug log to track key presses
        logger.info(f"Key pressed: {event.keysym}, expecting: {correct}, already pressed: {self.key_pressed}")
        
        if event.keysym == correct and not self.key_pressed:
            self.key_pressed = True  # Mark this key as pressed
            self.count += 1
            logger.info(f"Count incremented to: {self.count}")
    
    def on_key_release(self, event):
        """Handle key release to reset the key state"""
        correct = 'Right' if self.step == 1 else 'Left'
        
        if event.keysym == correct:
            self.key_pressed = False  # Reset key state when released
            logger.info(f"Key released: {event.keysym}")

class PracticeTrialsFrame(ttk.Frame):
    """Frame to run practice trials"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.trial_index = 0
        self.key_pressed = {}  # Track pressed state for each key
        
        # Configure the frame for centering
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create a centered content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0)
        
        self.instr = ttk.Label(content_frame, text="", wraplength=600)
        self.instr.pack(pady=20)
        self.progress = ttk.Progressbar(
            content_frame, orient='horizontal', length=400, mode='determinate'
        )
        self.progress.pack(pady=10)
        
        # Bind both key press and key release events
        self.bind_all('<KeyPress>', self.on_key_press)
        self.bind_all('<KeyRelease>', self.on_key_release)
        
        logger.info("PracticeTrialsFrame initialized")
        self.load_trial()

    def load_trial(self):
        """Load or finish practice trials"""
        if self.trial_index >= len(PRACTICE_TRIALS):
            logger.info("All practice trials complete")
            self.controller.save_data()
            self.controller.show_frame(EndFrame)
            return
        self.current = PRACTICE_TRIALS[self.trial_index]
        self.stage = 'choice'
        self.choice_time = time.time()
        text = (
            f"Practice Trial {self.trial_index+1}\n"
            f"Choose a task: Easy:-$4 (Left)  Hard: ${self.current['magnitude_hard']:.2f} (Right)\n"
            f"Probability of loss: {int(self.current['prob']*100)}%"
        )
        self.instr.config(text=text)
        self.progress['value'] = 0
        logger.info("Loaded trial %d", self.trial_index+1)

    def on_key_press(self, event):
        """Handle key press events with proper state tracking"""
        key = event.keysym.lower()
        
        if self.stage == 'choice' and key in ('left', 'right') and not self.key_pressed.get(key, False):
            # Mark key as pressed
            self.key_pressed[key] = True
            
            # record choice response time
            rt = time.time() - self.choice_time
            choice = 'Easy' if key == 'left' else 'Hard'
            clicks_req = (
                EASY_CLICKS_REQUIRED if choice == 'Easy'
                else self.controller.hard_clicks_required
            )
            duration = 7.0 if choice == 'Easy' else 21.0
            logger.info(
                "Trial %d choice: %s (RT=%.3f)",
                self.trial_index+1, choice, rt
            )
            self.stage = 'task'
            self.task_start = time.time()
            self.task_end = self.task_start + duration
            self.clicks = 0
            self.choice = choice
            self.choice_rt = rt
            self.clicks_req = clicks_req
            self.duration = duration
            
            # Reset key_pressed for next stage
            self.key_pressed = {}
            self.after(50, self.run_task)
            
        elif self.stage == 'task':
            # Determine which keys are valid for the current task
            valid_keys = ['space'] if self.choice == 'Easy' else ['left', 'right']
            
            # Only count if the key is valid and not already pressed
            if key in valid_keys and not self.key_pressed.get(key, False):
                self.key_pressed[key] = True
                self.clicks += 1

    def on_key_release(self, event):
        """Handle key release events"""
        key = event.keysym.lower()
        # Mark the key as no longer pressed
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
                self.trial_index+1,
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
                self.trial_index+1, self.clicks, self.clicks_req, complete
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
        self.key_pressed = {}  # Reset key states for next trial
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