from random import choice, randint
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

class Personality:

    def __init__(self, **kwargs):
        self.eye = 'blue'
        self.object_reaction_end_time = None

        # Configurable interval range
        self.min_interval = kwargs.get('min_interval', 20)  # Default minimum 20 seconds
        self.max_interval = kwargs.get('max_interval', 60)  # Default maximum 60 seconds

        self.last_motion_time = datetime.now()
        self.last_vision_time = None
        self.next_action_time = self.calculate_next_action_time()
        self.last_status_time = None
        self.last_serial_time = None
        
        # Initialize status LED colors (default to 'off')
        self.led_colors = ['off'] * 5

        pub.subscribe(self.loop, 'loop:1')
        pub.subscribe(self.handle_vision_detections, 'vision:detections')
        pub.subscribe(self.update_motion_time, 'motion')
        pub.subscribe(self.track_serial_idle, 'serial')

        # Define possible actions
        self.actions = [
            self.braillespeak,
            self.random_neopixel_eye,
            self.move_antenna
        ]

    def loop(self):
        # Handle ongoing object reaction
        if self.object_reaction_end_time and datetime.now() >= self.object_reaction_end_time:
            pub.sendMessage('led', identifiers=[
                'right', 'top_right', 'top_left', 'left', 
                'bottom_left', 'bottom_right'
            ], color="off")
            self.object_reaction_end_time = None

        # Update the middle eye LED based on conditions
        self.update_middle_eye_led()
        
        self.random_neopixel_status()

        # Check if it's time for the next action
        if datetime.now() >= self.next_action_time:
            action = choice(self.actions)
            action()
            self.next_action_time = self.calculate_next_action_time()
        
        # If serial has been idle for more than 10 seconds, call random_animation()
        if self.last_serial_time and datetime.now() - self.last_serial_time > timedelta(seconds=10):
            self.random_animation()
            
    def random_animation(self):
        
        animations = [
            'head_shake',
            'head_left',
            'head_right',
            'wake',
            'look_down',
            'look_up'
        ]
        animation = choice(animations)
        pub.sendMessage('log', msg=f"[Personality] Random animation triggered: {animation}")
        pub.sendMessage('animate', action=animation)

    # Calculate the next action time
    def calculate_next_action_time(self):
        interval = randint(self.min_interval, self.max_interval)  # Use configurable interval range
        return datetime.now() + timedelta(seconds=interval)

    # Braillespeak: Outputs short messages as tones
    def braillespeak(self):
        messages = ["Hi", "Hello", "Hai", "Hey"]
        msg = choice(messages)
        pub.sendMessage('speak', msg=msg)
        pub.sendMessage('log', msg=f"[Personality] Braillespeak triggered: {msg}")

    # Buzzer: Outputs a specific tone
    def buzzer_tone(self):
        frequency = randint(300, 1000)  # Random frequency between 300Hz and 1000Hz
        length = round(randint(1, 5) / 10, 1)  # Random length between 0.1s and 0.5s
        pub.sendMessage('buzz', frequency=frequency, length=length)
        pub.sendMessage('log', msg=f"[Personality] Buzzer tone triggered: {frequency}Hz for {length}s")

    # Buzzer: Plays one of two predefined tunes
    def buzzer_song(self):
        songs = ["happy birthday", "merry christmas"]
        song = choice(songs)
        pub.sendMessage('play', song=song)
        pub.sendMessage('log', msg=f"[Personality] Buzzer song triggered: {song}")

    # Neopixels: Toggles random status LEDs
    def random_neopixel_status(self):
        if not self.last_status_time or datetime.now() - self.last_status_time > timedelta(seconds=3):
            self.last_status_time = datetime.now()
            color = choice(["red", "green", "blue", "white_dim", "purple", "yellow", "orange", "pink", "off"])
            pub.sendMessage('led', identifiers=[0], color=color)
            for i in range(4, 0, -1):
                if i+1 < 5:
                    self.led_colors[i] = self.led_colors[i-1]
            for i in range(1, 5):
                pub.sendMessage('led', identifiers=[i], color=self.led_colors[i])
            self.led_colors[0] = color
            pub.sendMessage('log', msg=f"[Personality] Neopixel status triggered set to {color}")

    # Neopixels: Toggles random eye LEDs
    def random_neopixel_eye(self):
        positions = [
            'right', 'top_right', 'top_left', 'left', 
            'bottom_left', 'bottom_right'
        ]
        position = choice(positions)
        color = choice(["white_dim"])
        pub.sendMessage('led', identifiers=positions, color=color)
        pub.sendMessage('log', msg=f"[Personality] Neopixel eye ring set to {color}")

    # Antenna: Moves to a random angle between -40 and 40 degrees
    def move_antenna(self):
        angle = randint(-40, 40)
        pub.sendMessage('piservo:move', angle=angle)
        pub.sendMessage('log', msg=f"[Personality] Antenna moved to angle: {angle}")

    # Vision: Handles detected objects
    def handle_vision_detections(self, matches):
        # if there are matches and the object reaction end time is in the past
        if matches and len(matches) > 0 and (self.object_reaction_end_time is None or datetime.now() >= self.object_reaction_end_time):
            pub.sendMessage('log', msg=f"[Personality] Vision detected objects: {matches}")
            self.last_vision_time = datetime.now()
            # Trigger temporary reaction for detected objects
            self.random_neopixel_eye()
            self.object_reaction_end_time = datetime.now() + timedelta(seconds=3)

    # Motion: Updates the last motion time
    def update_motion_time(self):
        self.last_motion_time = datetime.now()

    # Updates the middle eye LED based on the current state
    def update_middle_eye_led(self):
        now = datetime.now()
        if self.last_vision_time and now - self.last_vision_time <= timedelta(seconds=30):
            pub.sendMessage('led', identifiers='middle', color='green')
        elif now - self.last_motion_time > timedelta(seconds=30):
            pub.sendMessage('led', identifiers='middle', color='red')
        else:
            pub.sendMessage('led', identifiers='middle', color='blue')

    def track_serial_idle(self, type, identifier, message):
        self.last_serial_time = datetime.now()