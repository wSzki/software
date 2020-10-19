import Live
from FaderfoxComponent import FaderfoxComponent
from ParamMap import ParamMap
from consts import *

#noinspection PyCallingNonCallable
class TrackController(FaderfoxComponent):
    """
    Class controlling track control and parameters for LV3
    """
    __module__ = __name__
    __doc__ = 'Class controlling track control and parameters for LV3'
    __filter_funcs__ = ["update_display", "log"]

    def __init__(self, parent):
        TrackController.realinit(self, parent)

    def realinit(self, parent):
        """
        Actual initialization method
        """
        FaderfoxComponent.realinit(self, parent)

        # device locking
        self.device_locked = False
        self.device = None

        # keep tracks of our listeners
        self.tracks_with_listener = []
        self.track_panning_listeners = {}

        self.reset_status_cache()

    def remove_track_listeners(self):
        """
        Remove all registered listeners
        """
        for track in self.tracks_with_listener:
            if track:
                if track.can_be_armed:
                    track.remove_arm_listener(self.on_track_arm_changed)
                if hasattr(track, "mute"):
                    track.remove_mute_listener(self.on_track_mute_changed)
                if hasattr(track, "solo"):
                    track.remove_solo_listener(self.on_track_solo_changed)
                if hasattr(track, "playing_slot_index"):
                    track.remove_playing_slot_index_listener(self.on_track_playing_slot_index_changed)
                if hasattr(track, "current_monitoring_state"):
                    track.remove_current_monitoring_state_listener(self.on_track_monitoring_changed)
                track.mixer_device.panning.remove_value_listener(self.on_track_panning_changed)
        self.tracks_with_listener = []

    ###########################################################
    #
    # Track status callbacks
    #
    ###########################################################
    def on_track_panning_changed(self, *args, **kwargs):
        """
        Track panning callback
        """
        self.log("track panning changed : %s, %s" % (args, kwargs))
        self.set_tracks_panning_status()

    def on_track_arm_changed(self):
        """
        Track arm changed
        """
        self.set_tracks_status("arm", CC_RECORD_TRACK)

    def on_track_playing_slot_index_changed(self):
        """
        Track playing slot callback
        """
        self.set_tracks_status("playing_slot_index", CC_LAUNCH_CLIP)

    def on_track_mute_changed(self):
        """
        Track mute callback
        """
        self.set_tracks_status("mute", CC_ACTIVE_TRACK)

    def on_track_solo_changed(self):
        """
        Track solo callback
        """
        self.set_tracks_status("solo", CC_SOLO_TRACK)

    def on_track_monitoring_changed(self):
        """
        Track monitoring callback
        """
        self.set_tracks_status("current_monitoring_state", CC_MONITOR_TRACK)


    ###########################################################
    #
    # Track handling
    #
    ###########################################################

    # track status cache
    def reset_status_cache(self):
        """
        Reset the track status cache
        """
        self.log("reset status cache")
        self.status_cache = {"mute": {},
                             "solo": {},
                             "arm": {},
                             "current_monitoring_state": {},
                             "playing_slot_index": {},
                             "launch_status": {},
                             "stop_status": {},
                             "panning": {}}
        self.send_all_track_status()
        self.log("end reset status cache")

    def send_all_track_status(self):
        """
        Send the status of all tracks out to LV3
        """
        self.on_track_arm_changed()
        self.on_track_mute_changed()
        self.on_track_solo_changed()
        self.on_track_monitoring_changed()
        self.on_track_playing_slot_index_changed()
        self.set_tracks_panning_status()
        for idx in range(0, 8):
            self.send_track_launch_status(idx)

    def send_track_launch_status(self, channel):
        """ Send the launch status back to LV3.

        - ON: clip present
        - OFF: not playing, no clip
        - BLINK: track playing
        """
        track = self.parent.get_lv3_track_from_channel(channel)

        launch_status = 0
        stop_status = 0
        clip_idx = self.helper.selected_scene_idx()

        if track:
            if track.is_foldable:
                # default status for foldable tracks is stopped
                stop_status = 127

                # check if the current clip controls_other clips (launch_status = 127)
                if clip_idx < len(track.clip_slots):
                    clip_slot = track.clip_slots[clip_idx]
                    if clip_slot.controls_other_clips:
                        launch_status = 127
                    if clip_slot.playing_status == 1:
                        launch_status = 63

                # then, we go over each clip_slot, and check if it controls other clips
                # and is playing (then stop_status = 0)
                for clip_slot in track.clip_slots:
                    if clip_slot.controls_other_clips:
                        self.log("clip slot on track %s has playing status %s" % (track.name, clip_slot.playing_status))
                        if clip_slot.playing_status == 1:
                            stop_status = 0
                            break

            else:
                # for normal tracks, default status is playing (stop_status = 0), and no clip launchable (launch_status = 0)
                
                if hasattr(track, "playing_slot_index"):
                    if clip_idx < len(track.clip_slots):
                        clip_slot = track.clip_slots[clip_idx]

                        # if the current clip_slot has a clip, make it launchable
                        if clip_slot.has_clip:
                            launch_status = 127

                        # if that slot is actually playing, make it blink
                        if track.playing_slot_index == clip_idx:
                            launch_status = 63

                        # check if the track is playing at all
                        if track.playing_slot_index < 0:
                            stop_status = 127

        if self.status_cache["launch_status"].get(channel, None) != launch_status:
            self.status_cache["launch_status"][channel] = launch_status
            self.parent.send_midi((CC_STATUS | channel, CC_LAUNCH_CLIP, launch_status))
        if self.status_cache["stop_status"].get(channel, None) != stop_status:
            self.status_cache["stop_status"][channel] = stop_status
            self.parent.send_midi((CC_STATUS | channel, CC_STOP_CLIP, stop_status))

    def set_tracks_panning_status(self):
        """ set status attribute for a track, and send CC back to LV3. """
        (tracks, track_channels) = self.parent.get_lv3_all_tracks_channels()

        self.log("set tracks panning status")
        _idx = 0
        for track in tracks:
            if not track:
                continue

            status = track.mixer_device.panning.value == 0
            channel = track_channels[_idx]

            if self.status_cache["panning"].get(channel, None) != status:
                if status:
                    self.parent.send_midi((CC_STATUS | channel, CC_PAN_CENTER_SELECTED_TRACK, 0))
                else:
                    self.parent.send_midi((CC_STATUS | channel, CC_PAN_CENTER_SELECTED_TRACK, 127))
                self.status_cache["panning"][channel] = status
            _idx += 1

    def set_tracks_status(self, attr, cc):
        """ set status attribute for a track, and send CC back to LV3. """
        (tracks, track_channels) = self.parent.get_lv3_all_tracks_channels()

        _idx = 0
        for track in tracks:
            channel = track_channels[_idx]
            _idx += 1

            if attr == "playing_slot_index":
                self.send_track_launch_status(channel)
                continue

            if not hasattr(track, attr):
                status = False
            elif hasattr(track, "can_be_armed") and (not track.can_be_armed) and (attr == "arm"):
                status = False
            else:
                status = track.__getattribute__(attr)
                if attr == "mute":
                    status = not status

            if self.status_cache[attr].get(channel, None) != status:
                self.status_cache[attr][channel] = status
                self.log("status for track %s channel %s attr %s: %s" % (_idx, channel, attr, status))

                # interpret this one here to work around toggling switch in LV3
                if attr == "current_monitoring_state":
                    cc_value = 0
                    if status == 1:
                        cc_value = 127
                    elif status == 0:
                        cc_value = 63
                    self.parent.send_midi((CC_STATUS | channel, cc, cc_value))
                else:
                    if status:
                        self.parent.send_midi((CC_STATUS | channel, cc, 127))
                    else:
                        self.parent.send_midi((CC_STATUS | channel, cc, 0))

    def track_find_first_rack(self, track):
        """
        Helper method to find the first rack in a track
        """
        if self.device_locked and self.device and self.helper.is_rack(self.device):
            return self.device

        for device in track.devices:
            if self.helper.is_rack(device):
                return device

        return None

    def start_track(self, track_idx, button_state):
        """
        Start the given track
        """
        scene = self.parent.song().view.selected_scene
        if len(scene.clip_slots) > track_idx:
            clip_slot = scene.clip_slots[track_idx]
            clip_slot.set_fire_button_state(button_state)

    # normal functions
    def disconnect(self):
        """
        Called on script disconnect
        """
        self.remove_track_listeners()


    ###########################################################
    #
    # Device lock handling
    #
    ###########################################################
    def lock_to_device(self, device):
        """
        Lock to a specific device.

        XXX Normally we should only be able to lock to rack devices
        """
        if device:
            self.device_locked = True
            self.device = device
            self.parent.request_rebuild_midi_map()

    def unlock_from_device(self, device):
        """
        Unlock from device
        """
        if device and (device == self.device):
            self.device_locked = False
        self.parent.request_rebuild_midi_map()

    ###########################################################
    #
    # MIDI handling
    #
    ###########################################################
    def receive_midi_cc(self, channel, cc_no, cc_value):
        """
        Midi CC callback
        """
        self.log("received cc %s %s %s" % (channel, cc_no, cc_value))

        # disallow jumping to inexisting tracks
        if (cc_no == CC_TRACK_SELECT) and (cc_value == 127):
            self.parent.set_lv3_track(channel)

        track = self.parent.get_lv3_track_from_channel(channel)
        track_idx = self.parent.get_lv3_track_real_idx(track)
        # track_idx = self.parent.lv3_start_track + channel

        # ignore CC if the track is not available
        if not track:
            return

        self.log("for track %s" % track.name)

        mixer_device = track.mixer_device
        sends = mixer_device.sends[0:2]

        if (cc_no == CC_PAN_CENTER_SELECTED_TRACK) and (cc_value == 127):
            mixer_device.panning.value = 0

        # explicit handling of send buttons
        if len(sends) > 0:
            if (cc_no == CC_SENDA_ON_OFF_SELECTED_TRACK) or (cc_no == CC_SEND_A_TRACK):
                sends[0].value = cc_value / 127.0

        if len(sends) > 1:
            if cc_no == CC_SEND_B_TRACK:
                sends[1].value = cc_value / 127.0

        # explicit handling of macro push buttons
        rack = self.track_find_first_rack(track)
        if rack:
            if (cc_no >= CC_MACRO5_ON_OFF_SELECTED_TRACK) and (cc_no <= CC_MACRO8_ON_OFF_SELECTED_TRACK):
                param_idx = cc_no - CC_MACRO5_ON_OFF_SELECTED_TRACK + 5
                param = rack.parameters[param_idx]
                if cc_value == 127:
                    param.value = param.max
                elif cc_value == 0:
                    param.value = param.min

            if cc_no == CC_MACRO6_ON_OFF:
                param_idx = 6
                param = rack.parameters[param_idx]
                if cc_value == 127:
                    param.value = param.max
                elif cc_value == 0:
                    param.value = param.min

        # the following functions are not valid for the master channel
        if cc_no == CC_LAUNCH_CLIP:
            if channel in TRACK_CHANNELS:
                self.start_track(track_idx, cc_value == 127)
            elif channel == MASTER_CHANNEL:
                self.parent.song().view.selected_scene.set_fire_button_state(cc_value == 127)

        if (cc_no == CC_STOP_CLIP) and (cc_value == 127):
            if channel in TRACK_CHANNELS:
                track.stop_all_clips()
                # self.helper.stop_track(track_idx)
            elif channel == MASTER_CHANNEL:
                self.parent.song().stop_all_clips()

        if cc_no == CC_ACTIVE_TRACK:
            if channel == MASTER_CHANNEL:
                pass
            else:
                track.__setattr__('mute', cc_value == 0)

        if cc_no == CC_SOLO_TRACK:
            if channel == MASTER_CHANNEL:
                pass
            else:
                track.solo = (cc_value == 127)

        if cc_no == CC_RECORD_TRACK:
            if channel == MASTER_CHANNEL:
                pass
            else:
                if track.can_be_armed:
                    track.arm = (cc_value == 127)

        if cc_no == CC_MONITOR_TRACK:
            if channel == MASTER_CHANNEL:
                pass
            else:
                if hasattr(track, "current_monitoring_state"):
                    self.helper.switch_monitor_track(track)

    ###########################################################
    #
    # Build the MIDI Map
    #
    ###########################################################
    def build_midi_map(self, script_handle, midi_map_handle):
        """
        Build the MIDI Map for the component
        """
        self.map_track_params(script_handle, midi_map_handle)

        def forward_cc(chan, cc):
            """
            Request ableton to forward a CC message to the script
            """
            return Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, chan, cc)

        forward_cc(MASTER_CHANNEL, CC_TRACK_SELECT)

        for chan in ALL_TRACK_CHANNELS:
            forward_cc(chan, CC_TRACK_SELECT)
            # key commands
            forward_cc(chan, CC_LAUNCH_CLIP)
            forward_cc(chan, CC_STOP_CLIP)
            forward_cc(chan, CC_ACTIVE_TRACK)
            forward_cc(chan, CC_SOLO_TRACK)
            forward_cc(chan, CC_RECORD_TRACK)
            forward_cc(chan, CC_MONITOR_TRACK)
            # send a center
            forward_cc(chan, CC_PAN_CENTER_SELECTED_TRACK)
            # sends push button functionality (can't be done with map because of pickup)
            forward_cc(chan, CC_SEND_A_TRACK)
            forward_cc(chan, CC_SEND_B_TRACK)
            forward_cc(chan, CC_SENDA_ON_OFF_SELECTED_TRACK)
            # macro push button functionality
            forward_cc(chan, CC_MACRO5_ON_OFF_SELECTED_TRACK)
            forward_cc(chan, CC_MACRO6_ON_OFF_SELECTED_TRACK)
            forward_cc(chan, CC_MACRO7_ON_OFF_SELECTED_TRACK)
            forward_cc(chan, CC_MACRO8_ON_OFF_SELECTED_TRACK)
            forward_cc(chan, CC_MACRO6_ON_OFF)


    def map_track_params(self, script_handle, midi_map_handle):
        """ Map the track parameters. """

        self.remove_track_listeners()

        # XXX add return tracks
        (tracks, track_channels) = self.parent.get_lv3_all_tracks_channels()

        for (track, channel) in zip(tracks, track_channels):
            if not track:
                continue

            # look for the first rack in the track, and map it to macro knobs and buttons
            rack = self.track_find_first_rack(track)
            if rack:
                self.log("found rack: %s" % rack)
                param_idx = 0
                for parameter in rack.parameters[1:5]:
                    ParamMap.map_with_feedback(midi_map_handle, channel, CC_MACRO1_SELECTED_TRACK + param_idx,
                                               parameter, Live.MidiMap.MapMode.relative_two_compliment)
                    param_idx += 1
                for parameter in rack.parameters[5:9]:
                    ParamMap.map_with_feedback(midi_map_handle, channel, CC_MACRO1_SELECTED_TRACK + param_idx,
                                               parameter, Live.MidiMap.MapMode.absolute)
                    param_idx += 1

                # FX key 1
                ParamMap.map_with_feedback(midi_map_handle, channel, CC_MACRO6_ON_OFF,
                                           rack.parameters[6], Live.MidiMap.MapMode.absolute)
                ParamMap.map_with_feedback(midi_map_handle, channel, CC_MACRO7_SEND,
                                           rack.parameters[7], Live.MidiMap.MapMode.absolute)
                ParamMap.map_with_feedback(midi_map_handle, channel, CC_MACRO8_SEND,
                                           rack.parameters[8], Live.MidiMap.MapMode.absolute)


            # add listeners for the track status
            if not track in self.tracks_with_listener:
                if hasattr(track, "can_be_armed") and track.can_be_armed:
                    track.add_arm_listener(self.on_track_arm_changed)
                if hasattr(track, "mute"):
                    track.add_mute_listener(self.on_track_mute_changed)
                if hasattr(track, "solo"):
                    track.add_solo_listener(self.on_track_solo_changed)
                if hasattr(track, "playing_slot_index"):
                    track.add_playing_slot_index_listener(self.on_track_playing_slot_index_changed)
                if hasattr(track, "current_monitoring_state"):
                    track.add_current_monitoring_state_listener(self.on_track_monitoring_changed)
                track.mixer_device.panning.add_value_listener(self.on_track_panning_changed)
                self.tracks_with_listener.append(track)

            # map the tracks mixer device
            mixer_device = track.mixer_device

            parameter = mixer_device.panning
            ParamMap.map_with_feedback(midi_map_handle, channel, CC_PAN_SELECTED_TRACK,
                                       parameter, Live.MidiMap.MapMode.relative_two_compliment)

            # map without feedback XXX
            parameter = mixer_device.volume
            ParamMap.map_with_feedback(midi_map_handle, channel, CC_VOLUME_FADER,
                                       parameter, Live.MidiMap.MapMode.absolute)

            sends = mixer_device.sends[0:2]
            _send_idx = 0
            for send in sends:
                if _send_idx == 0:
                    ParamMap.map_with_feedback(midi_map_handle, channel, CC_SENDA_ON_OFF_SELECTED_TRACK,
                                               send, Live.MidiMap.MapMode.absolute)
                if _send_idx == 1:
                    ParamMap.map_with_feedback(midi_map_handle, channel, CC_SENDB_SELECTED_TRACK,
                                               send, Live.MidiMap.MapMode.relative_two_compliment)

                ParamMap.map_with_feedback(midi_map_handle, channel, CC_SEND_A_TRACK + _send_idx,
                                           send, Live.MidiMap.MapMode.absolute)

                _send_idx += 1

            channel += 1

        # reset the status cache of all tracks
        self.reset_status_cache()

        # master volume
        track = self.parent.song().master_track
        parameter = track.mixer_device.volume
        ParamMap.map_with_feedback(midi_map_handle, GLOBAL_CHANNEL, CC_ENCODER4_MASTER_VOLUME,
                                   parameter, Live.MidiMap.MapMode.relative_two_compliment)

        # cue volume
        if hasattr(track.mixer_device, "cue_volume"):
            parameter = track.mixer_device.cue_volume
            ParamMap.map_with_feedback(midi_map_handle, GLOBAL_CHANNEL, CC_ENCODER3_CUE,
                                       parameter, Live.MidiMap.MapMode.relative_two_compliment)
