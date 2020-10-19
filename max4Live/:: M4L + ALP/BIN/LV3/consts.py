# MIDI values
STATUS_MASK = 0xF0
CHAN_MASK   = 0x0F

CC_STATUS      = 0xB0
NOTEON_STATUS  = 0x90
NOTEOFF_STATUS = 0x80

STATUS_ON  = 0x7F
STATUS_OFF = 0x00

# encoder 1 - 4 for the selected track
# channel 1-8 for track 1-8
# channel 9-10 for send A - B
# channel 11 for master
TRACK1_CHANNEL = 0
TRACK2_CHANNEL = 1
TRACK3_CHANNEL = 2
TRACK4_CHANNEL = 3
TRACK5_CHANNEL = 4
TRACK6_CHANNEL = 5
TRACK7_CHANNEL = 6
TRACK8_CHANNEL = 7
SEND_A_CHANNEL = 8
SEND_B_CHANNEL = 9
MASTER_CHANNEL = 10
GLOBAL_CHANNEL = 11

TRACK_CHANNELS = range(TRACK1_CHANNEL, TRACK8_CHANNEL + 1)
TRACK_NO_MASTER_CHANNELS = range(TRACK1_CHANNEL, SEND_B_CHANNEL + 1)
ALL_TRACK_CHANNELS = range(TRACK1_CHANNEL, MASTER_CHANNEL + 1)

# led status
CC_LED_OFF = 0
CC_LED_BLINK = 63
CC_LED_ON = 127

# encoder turn
CC_MACRO1_SELECTED_TRACK = 24
CC_MACRO2_SELECTED_TRACK = 25
CC_MACRO3_SELECTED_TRACK = 26
CC_MACRO4_SELECTED_TRACK = 27
CC_PAN_SELECTED_TRACK    = 10 # in pan mode
CC_SENDB_SELECTED_TRACK  = 13 # in send mode

# encoder push
CC_MACRO5_ON_OFF_SELECTED_TRACK = 28
CC_MACRO6_ON_OFF_SELECTED_TRACK = 29
CC_MACRO7_ON_OFF_SELECTED_TRACK = 30
CC_MACRO8_ON_OFF_SELECTED_TRACK = 31
CC_PAN_CENTER_SELECTED_TRACK = 11
CC_SENDA_ON_OFF_SELECTED_TRACK  = 12

# encoder with shift (channel 12)
CC_ENCODER1_TEMPO_FINE   = 24
CC_ENCODER2_QUANTIZATION = 25
CC_ENCODER3_CUE          = 26
CC_ENCODER4_MASTER_VOLUME = 27

# encoder push with shift
CC_ENCODER1_TAP_TEMPO   = 28
CC_ENCODER2_NUDGE_DOWN  = 29
CC_ENCODER3_NUDGE_UP    = 30
CC_ENCODER4_VIEW_TOGGLE = 31

# scene encoder
CC_SCENE_SELECT = 6 # channel 11
# scene encoder with shift
CC_TRACK_WINDOW_SELECT = 9 # channel 12
# scene encoder push with scene mode
CC_SCENE_START = 03 # channel 11
# scene encoder push without scene mode
CC_CLIP_SCENE_START = 03 # channel 12
# scene encoder push with shift with scene mode
CC_SCENE_STOP = 00 # channel 11
# scene encoder push with shift without scene mode
CC_CLIP_SCENE_STOP = 00 # channel 12

# faders (channel 1-8)
CC_VOLUME_FADER = 7

# FX1 X stick commands (without stick track mode) 
CC_MACRO7_SEND = 1 # channel 9
# FX1 Y stick commands (without stick track mode)
CC_MACRO8_SEND = 2 # channel 9

# black keys without shift only send CC value 127
# green/blue/black keys with key mode 1 (launch) send 127 on press and 0 on release
# green/blue/black keys with key mode 2 (stop) send 127 on press
# green/blue/black keys with key mode 3-8 send 127 and 0 (toggle)
# gray keys send 127 and 0 toggle

# black select keys (without shift) control their leds on their own
# gray / green /blue/black keys control their leds alone in key mode 3 - 8 or off
# status is needed for all keys (0 = off, 63 = blink, 127 = on)
# blink only for launch keys (0 = no clip, 63 = play, 127 = clip loaded)

# gray keys
# FX1 key without stick track mode
CC_MACRO6_ON_OFF = 4 # channel 9
# FX2 key
CC_MACRO6_ON_OFF_SENDB = 6 # channel 9

# black keys
CC_TRACK_SELECT = 8 # channel 1-8
# black key with shift -> see track key commands

# FX key
CC_SEND_SELECT = 8 # channel 9 - 10 (led blink for send B)
# FX key with shift
CC_GLOBAL_STOP = 15 # channel 12

# master key
CC_MASTER_SELECT = 8   # channel 11
# master key with shift
CC_GLOBAL_PLAY = 14 # channel 12

# green / blue keys -> see track key commands
# track key commands
CC_LAUNCH_CLIP = 16 # channel 1 -11
CC_STOP_CLIP   = 17
CC_ACTIVE_TRACK = 18
CC_SOLO_TRACK   = 19
CC_RECORD_TRACK = 20
CC_MONITOR_TRACK = 21
CC_SEND_A_TRACK = 22
CC_SEND_B_TRACK = 23
