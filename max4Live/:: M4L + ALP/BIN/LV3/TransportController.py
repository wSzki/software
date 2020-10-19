import Live
from FaderfoxComponent import FaderfoxComponent
from consts import *

class TransportController(FaderfoxComponent):
    """
    Transport section of LV3 faderfox controllers
    """
    __module__ = __name__
    __doc__ = 'Class representing the transport section of faderfox controllers'

    QuantizationList = [
        Live.Song.Quantization.q_no_q,
        Live.Song.Quantization.q_8_bars,
        Live.Song.Quantization.q_4_bars,
        Live.Song.Quantization.q_2_bars,
        Live.Song.Quantization.q_bar,
        Live.Song.Quantization.q_half,
        Live.Song.Quantization.q_half_triplet,
        Live.Song.Quantization.q_quarter,
        Live.Song.Quantization.q_quarter_triplet,
        Live.Song.Quantization.q_eight,
        Live.Song.Quantization.q_eight_triplet,
        Live.Song.Quantization.q_sixtenth,
        Live.Song.Quantization.q_sixtenth_triplet,
        Live.Song.Quantization.q_thirtytwoth
        ]

    def __init__(self, parent):
        TransportController.realinit(self, parent)

    def realinit(self, parent):
        """
        Actual initialization method
        """
        FaderfoxComponent.realinit(self, parent)
        self.parent.song().add_clip_trigger_quantization_listener(self.on_quantization_changed)

    def get_quantization_step(self):
        return self.QuantizationList.index(self.song().clip_trigger_quantization)

    def on_quantization_changed(self):
        """
        Song quantization change callback
        """
        # send midi feedback !? XXX
        pass

    def receive_midi_cc(self, channel, cc_no, cc_value):
        # global functions
        """
        MIDI callback
        """
        if channel == GLOBAL_CHANNEL:
            if cc_no == CC_GLOBAL_STOP:
                self.parent.song().stop_playing()
            elif cc_no == CC_GLOBAL_PLAY:
                self.parent.song().start_playing()
            elif cc_no == CC_TRACK_WINDOW_SELECT:
                # move track window
                val = self.parent.relative_to_absolute(cc_value)
                _idx = self.parent.lv3_start_track + val
                tracks = self.parent.get_all_lv3_tracks()
                if _idx < 0:
                    _idx = 0
                if _idx >= len(tracks) - 8:
                    _idx = len(tracks) - 8
                self.parent.set_track_window(_idx)

            elif cc_no == CC_CLIP_SCENE_START:
                clip_idx = self.helper.selected_scene_idx()
                track = self.parent.song().view.selected_track
                if track:
                    if clip_idx < len(track.clip_slots):
                        slot = track.clip_slots[clip_idx]
                        slot.set_fire_button_state(cc_value == 127)

            elif (cc_no == CC_CLIP_SCENE_STOP) and (cc_value == 127):
                clip_idx = self.helper.selected_scene_idx()
                track = self.parent.song().view.selected_track
                if track:
                    if clip_idx < len(track.clip_slots):
                        slot = track.clip_slots[clip_idx]
                        if slot.has_clip:
                            slot.clip.stop()

            elif (cc_no == CC_ENCODER1_TAP_TEMPO) and (cc_value == 127):
                self.parent.song().tap_tempo()

            elif cc_no == CC_ENCODER2_NUDGE_DOWN:
                setattr(self.parent.song(), 'nudge_down', cc_value == 127)

            elif cc_no == CC_ENCODER3_NUDGE_UP:
                setattr(self.parent.song(), 'nudge_up', cc_value == 127)

            elif (cc_no == CC_ENCODER4_VIEW_TOGGLE) and (cc_value == 127):
                view = self.parent.application().view
                if view.is_view_visible('Detail/Clip'):
                    view.show_view('Detail/DeviceChain')
                else:
                    view.show_view('Detail/Clip')

            elif cc_no == CC_ENCODER1_TEMPO_FINE:
                val = self.parent.relative_to_absolute(cc_value)
                self.parent.song().tempo += val * 0.01

            elif cc_no == CC_ENCODER2_QUANTIZATION:
                val = self.parent.relative_to_absolute(cc_value)
                step = self.get_quantization_step()
                new_step = step + val
                if new_step < 0:
                    new_step = 0
                if new_step >= len(self.QuantizationList):
                    new_step = len(self.QuantizationList) - 1
                self.parent.song().clip_trigger_quantization = self.QuantizationList[new_step]

        if channel == MASTER_CHANNEL:
            if cc_no == CC_SCENE_SELECT:
                val = self.parent.relative_to_absolute(cc_value)
                idx = self.helper.selected_scene_idx() + val
                new_scene_idx = min(len(self.parent.song().scenes) - 1, max(0, idx))
                self.parent.song().view.selected_scene = self.parent.song().scenes[new_scene_idx]

            elif cc_no == CC_SCENE_START:
                self.parent.song().view.selected_scene.set_fire_button_state(cc_value == 127)

            elif (cc_no == CC_SCENE_STOP) and (cc_value == 127):
                self.parent.song().stop_all_clips()

    def build_midi_map(self, script_handle, midi_map_handle):
        """
        Rebuild the midi map
        """

        def forward_cc(chan, cc):
            """
            Helper method to map a CC message
            """
            return Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, chan, cc)

        forward_cc(GLOBAL_CHANNEL, CC_GLOBAL_STOP)
        forward_cc(GLOBAL_CHANNEL, CC_GLOBAL_PLAY)

        forward_cc(MASTER_CHANNEL, CC_SCENE_SELECT)
        forward_cc(MASTER_CHANNEL, CC_SCENE_START)
        forward_cc(MASTER_CHANNEL, CC_SCENE_STOP)

        forward_cc(GLOBAL_CHANNEL, CC_TRACK_WINDOW_SELECT)
        forward_cc(GLOBAL_CHANNEL, CC_CLIP_SCENE_START)
        forward_cc(GLOBAL_CHANNEL, CC_CLIP_SCENE_STOP)

        forward_cc(SEND_A_CHANNEL, CC_SEND_SELECT)
        forward_cc(SEND_B_CHANNEL, CC_SEND_SELECT)

        # special functions
        forward_cc(GLOBAL_CHANNEL, CC_ENCODER1_TAP_TEMPO)
        forward_cc(GLOBAL_CHANNEL, CC_ENCODER2_NUDGE_DOWN)
        forward_cc(GLOBAL_CHANNEL, CC_ENCODER3_NUDGE_UP)
        forward_cc(GLOBAL_CHANNEL, CC_ENCODER4_VIEW_TOGGLE)

        # XXX tempo fine, quantization
        forward_cc(GLOBAL_CHANNEL, CC_ENCODER1_TEMPO_FINE)
        forward_cc(GLOBAL_CHANNEL, CC_ENCODER2_QUANTIZATION)

    def disconnect(self):
        """
        Script disconnect callback
        """
        self.parent.song().remove_clip_trigger_quantization_listener(self.on_quantization_changed)
