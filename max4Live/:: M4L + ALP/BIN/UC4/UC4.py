import Live
import sys
from FaderfoxHelper import FaderfoxHelper
from ParamMap import ParamMap
from TransportController import TransportController
from TrackController import TrackController
from consts import *
# from Tracing import Traced

# class UC4(Traced):
class UC4():
    """
    UC4 script main object
    """
    __doc__ = "Faderfox UC4 controller script"
    __version__ = "v1.0"
    __name__ = "Faderfox UC4"
    __module__ = __name__
    # __myCommands__ = True
    __myCommands__ = False
    # __myDebug__ = True
    __myDebug__ = False
    __filter_funcs__ = ["update_display", "log", "exec_commands", "song", "send_midi"]

    def __init__(self, c_instance):
        # do real init thing because of tracing
        UC4.realinit(self, c_instance)

    def realinit(self, c_instance):
        """ Do the real initialization. """
        if self.__myCommands__:
            if sys.platform == "win32":
                self.commandfile = "C:/ableton-debug-cmd.txt"
            else:
                self.commandfile = "/tmp/ableton-debug-cmd"

        # self.log("UC4 started")
        self.helper = FaderfoxHelper(self)
        self.param_map = ParamMap(self)

        self.c_instance = c_instance
        self.show_message(self.__name__ + " " + self.__version__)

        # Register callbacks for the main script handler
        self.on_scene_selected_callback = self.on_scene_selected
        self.song().view.add_selected_scene_listener(self.on_scene_selected_callback)

        self.selected_scene = None
        self.scene_clip_slots = []
        self.refresh_clip_slots = True

        # Instantiate controllers. We have 2 controllers, one for general transport parameters, one
        # for track specific functionality
        self.transportController = TransportController(self)
        self.trackController = TrackController(self)
        self.components = [self.transportController, self.trackController]

        self.initializeMidi = True

        self.log("realinit request rebuild")
        self.request_rebuild_midi_map()

    def relative_to_absolute(self, cc_value):
        """ Convert a relative CC to an absolute value. """
        val = 0
        if cc_value >= 64:
            val = cc_value - 128
        else:
            val = cc_value
        return val

    ###########################################################
    #
    # Tracks
    #
    ###########################################################
    def get_all_tracks(self):
        res = list(self.song().visible_tracks) + list(self.song().return_tracks) + [self.song().master_track]
        for i in range(len(res), 16):
            res += [None]
        return res[0:16]

    def get_track_by_idx(self, idx):
        tracks = self.get_all_tracks()
        if idx >= len(tracks):
            return None
        return tracks[idx]

    ###########################################################
    #
    # Script callbacks
    #
    ###########################################################

    def on_scene_selected(self):
        """ Called when a new scene is selected.

        - Add clip slot listeners for all the clips in the scene
        - Send the selected scene back to LV3
        - Move the track window
        """
        if self.selected_scene:
            self.selected_scene.remove_clip_slots_listener(self.on_scene_clip_slots)
        self.selected_scene = self.song().view.selected_scene
        self.selected_scene.add_clip_slots_listener(self.on_scene_clip_slots)
        self.on_scene_clip_slots()
        scene_idx = self.helper.selected_scene_idx()
        self.send_midi((CC_STATUS | UC4_CH2, CC_SCENE_SELECT, min(scene_idx + 1, 99)))
        self.send_midi((CC_STATUS | UC4_CH1, CC_GLOBAL_SCENE_SELECT, min(scene_idx + 1, 99)))
        # self.trackController.set_tracks_status("playing_slot_index", 0)
        self.trackController.send_all_track_status()
        
    def on_scene_clip_slots(self):
        """
        Remove clip listeners, and add new clip listeners, refresh the clip slots.
        """
        for slot in self.scene_clip_slots:
            try:
                slot.remove_has_clip_listener(self.on_slot_has_clip)
            except:
                pass
        self.scene_clip_slots = self.selected_scene.clip_slots
        for slot in self.scene_clip_slots:
            slot.add_has_clip_listener(self.on_slot_has_clip)
        self.on_slot_has_clip()

    def on_slot_has_clip(self):
        self.refresh_clip_slots = True

    ###########################################################
    #
    # Ableton API methods
    #
    ###########################################################
    def disconnect(self):
        """
        Called on MIDI Script shutdown
        """
        self.song().view.remove_selected_scene_listener(self.on_scene_selected_callback)
        if self.selected_scene:
            self.selected_scene.remove_clip_slots_listener(self.on_scene_clip_slots)
        for slot in self.scene_clip_slots:
            slot.remove_has_clip_listener(self.on_slot_has_clip)
        for c in self.components:
            c.disconnect()

    def application(self):
        """
        Return the application object
        """
        return Live.Application.get_application()

    def song(self):
        """
        Return the song object
        """
        return self.c_instance.song()

    def suggest_input_port(self):
        """
        Suggest a port name
        """
        return str("Faderfox Ctrl")

    def suggest_output_port(self):
        """
        Suggest an output port name
        """
        return str("Faderfox Ctrl")

    def can_lock_to_devices(self):
        """
        This script can lock to devices
        """
        return True

    def lock_to_device(self, device):
        """
        Called when the script is locked to a device
        """
        self.log("lock to device %s" % device)
        self.trackController.lock_to_device(device)

    def unlock_from_device(self, device):
        """
        Called when the script is unlocked
        """
        self.log("unlock from device %s" % device)
        self.trackController.unlock_from_device(device)

    def set_appointed_device(self, device):
        """
        Set the scripts appointed device
        """
        self.log("set appointed device %s" % device)
        pass

    def toggle_lock(self):
        """
        Toggle lock
        """
        self.c_instance.toggle_lock()

    def suggest_map_mode(self, cc_no):
        """
        Suggest the default CC map mode
        """
        return Live.MidiMap.MapMode.relative_two_compliment

    def restore_bank(self, bank):
        """
        Restore the script bank
        """
        pass

    def show_message(self, message):
        """
        Display a message (compatibility with live 5)
        """
        if hasattr(self.c_instance, 'show_message'):
            self.c_instance.show_message(message)

    def instance_identifier(self):
        """
        Return the C objects instance identifier
        """
        return self.c_instance.instance_identifier()

    def connect_script_instances(self, instantiated_scripts):
        """
        Connect instantiated scripts (when linking scripts)
        """
        pass

    def request_rebuild_midi_map(self):
        """
        Request a rebuild of the midi map
        """
        self.c_instance.request_rebuild_midi_map()

    def send_midi(self, midi_event_bytes):
        """
        Send out midi bytes
        """
        self.log("send midi %s" % (list(midi_event_bytes)))
        self.c_instance.send_midi(midi_event_bytes)

    def refresh_state(self):
        """
        Refresh the script's state.

        Send out scene select and track select CCs to controller.
        """
        # self.send_midi((CC_STATUS | MASTER_CHANNEL, CC_SCENE_SELECT,
        #                 min(self.helper.selected_scene_idx() + 1, 99)))
        # self.send_midi((CC_STATUS | GLOBAL_CHANNEL, CC_TRACK_WINDOW_SELECT,
        #                 min(self.start_track + 1, 99)))
        for c in self.components:
            c.refresh_state()

    def build_midi_map(self, midi_map_handle):
        """
        Build a midi map (calls all registered components)
        """
        self.log("rebuild midi map")
        script_handle = self.c_instance.handle()
        self.param_map.remove_mappings()
        for c in self.components:
            self.log("rebuild midi map for %s" % c)
            c.build_midi_map(script_handle, midi_map_handle)
        self.log("end rebuild midi map")

    def update_display(self):
        """
        Update the display.

        Send out the refreshed track status to the controller
        """
        if self.initializeMidi:
            self.initializeMidi = False

        if self.refresh_clip_slots:
            for _idx in range(8):
                self.trackController.set_tracks_status("playing_slot_index", NOTE_LAUNCH_TRACK_BASE)
            self.refresh_clip_slots = False

        for c in self.components:
            c.update_display()
        self.exec_commands()

    def receive_midi(self, midi_bytes):
        """
        MIDI receive callback

        Dispatches CC and notes to the registered components
        """
        channel = (midi_bytes[0] & CHAN_MASK)
        status = (midi_bytes[0] & STATUS_MASK)
        if status == CC_STATUS:
            cc_no = midi_bytes[1]
            cc_value = midi_bytes[2]
            for c in self.components:
                c.receive_midi_cc(channel, cc_no, cc_value)
            self.param_map.receive_midi_cc(channel, cc_no, cc_value)
        elif (status == NOTEON_STATUS) or (status == NOTEOFF_STATUS):
            self.log("received note midi_bytes %s" % (midi_bytes,))
            note_no = midi_bytes[1]
            note_vel = midi_bytes[2]
            for c in self.components:
                c.receive_midi_note(channel, status, note_no, note_vel)
            self.param_map.receive_midi_note(channel, status, note_no, note_vel)
        else:
            pass

    #####################################################################
    #
    # Debug helpers
    #
    #####################################################################
    def exec_commands(self):
        """ Check if new commands have been written to the command file, parse them and execute them."""
        if not self.__myCommands__:
            return

        # read command from command file
        file = open(self.commandfile, "r")
        commands = file.readlines()
        file.close()

        # execute commands
        for command in commands:
            command = command.strip()
            try:
                result = eval(command).__str__()
#                if (isinstance(result, unicode)):
#                    result = result.encode("latin-1")
                self.log("%s = %s" % (command, result))
            except Exception, inst:
                self.log("exception: %s" % inst)
                self.log("while executing %s" % command)

            # clear command file
            file = open(self.commandfile, "w")
            file.write("")
            file.close()

    def log(self, string):
        """ Write a string to the debug log file. """
        if self.__myDebug__:
#            if (isinstance(string, unicode)):
#                self.file.write(string.encode("latin-1") + "\n")
#            else:
            self.c_instance.log_message("%s" % (string))
            # self.file.write(("%s" % string) + "\n")
            # self.file.flush()
