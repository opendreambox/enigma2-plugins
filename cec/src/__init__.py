from .Cec import cec

"""	
	enum CEC_MESSAGE_IDS {
		MSG_FEATURE_ABORT = 0x00,
		MSG_IMAGE_VIEW_ON = 0x04,
		MSG_TEXT_VIEW_ON = 0x0D,
		MSG_SET_MENU_LANG = 0x32,
		MSG_STANDBY = 0x36,
		MSG_USER_CONTROL_PRESSED = 0x44,
		MSG_USER_CONTROL_RELEASED = 0x45,
		MSG_GIVE_OSD_NAME = 0x46,
		MSG_SET_OSD_NAME = 0x47,
		MSG_SET_OSD_STRING = 0x64,
		MSG_SYSTEM_AUDIO_MODE_REQUEST = 0x70,
		MSG_GIVE_AUDIO_STATUS = 0x71,
		MSG_SET_SYSTEM_AUDIO_MODE = 0x72,
		MSG_REPORT_AUDIO_STATUS = 0x7a,
		MSG_GIVE_SYSTEM_AUDIO_MODE_STATUS = 0x7d,
		MSG_SYSTEM_AUDIO_MODE_STATUS = 0x7e,
		MSG_ROUTING_CHANGE = 0x80,
		MSG_ROUTING_INFORMATION = 0x81,
		MSG_ACTIVE_SOURCE = 0x82,
		MSG_GIVE_PHYS_ADDR = 0x83,
		MSG_REPORT_PHYS_ADDR = 0x84,
		MSG_REQUEST_ACTIVE_SOURCE = 0x85,
		MSG_SET_STREAMPATH = 0x86,
		MSG_DEVICE_VENDOR_ID = 0x87,
		MSG_VENDOR_COMMAND = 0x89,
		MSG_VENDOR_REMOTE_BUTTON_DOWN = 0x8a,
		MSG_VENDOR_REMOTE_BUTTON_UP = 0x8b,
		MSG_GIVE_DEVICE_VENDOR_ID = 0x8c,
		MSG_MENU_REQUEST = 0x8d,
		MSG_MENU_STATUS = 0x8e,
		MSG_GIVE_DEVICE_POWER_STATUS = 0x8f,
		MSG_REPORT_POWER_STATUS = 0x90,
		MSG_GET_MENU_LANG = 0x91,
		MSG_SET_AUDIO_RATE = 0x9a,
		MSG_INACTIVE_SOURCE = 0x9D,
		MSG_VERSION = 0x9e,
		MSG_GET_CEC_VERSION = 0x9f,
		MSG_VENDOR_COMMAND_WITH_ID = 0xa0,
		MSG_GIVE_DECK_STATUS = 0x1a,
		MSG_DECK_STATUS = 0x1b,
		MSG_DECK_CONTROL = 0x42,
	};

	enum CEC_ABORT_REASON {
		ABORT_REASON_UNRECOGNIZED_OPCODE = 0x00,
		ABORT_REASON_NOT_IN_CORRECT_MODE_TO_RESPOND = 0x01,
		ABORT_REASON_CANNOT_PROVIDE_SOURCE = 0x02,
		ABORT_REASON_INVALID_OPERAND = 0x03,
		ABORT_REASON_REFUSED =0x04
	};

	enum CEC_LOGICAL_ADDR {
		ADDR_TV = 0,
		ADDR_RECORDING_DEVICE_1 = 1,
		ADDR_RECORDING_DEVICE_2 = 2,
		ADDR_TUNER_1 = 3,
		ADDR_PLAYBACK_DEVICE_1 = 4,
		ADDR_AUDIO_SYSTEM = 5,
		ADDR_TUNER_2 = 6,
		ADDR_TUNER_3 = 7,
		ADDR_PLAYBACK_DEVICE_2 = 8,
		ADDR_RECORDING_DEVICE_3 = 9,
		ADDR_TUNER_4 = 10,
		ADDR_PLAYBACK_DEVICE_3 = 11,
		ADDR_RESERVED_1 = 12,
		ADDR_RESERVED_2 = 13,
		ADDR_FREE_USE = 14,
		ADDR_UNREGISTERED_BROADCAST = 15, //unregistered as initiator address, broadcast as destination address
	};

	enum CEC_VENDOR {
		VENDOR_DREAM = 0x000934,
		VENDOR_AKAI = 0x0020C7,
		VENDOR_AMAZON = 0x004571,
		VENDOR_AOC = 0x002467,
		VENDOR_BENQ = 0x8065E9,
		VENDOR_BROADCOM = 0x18C086,
		VENDOR_DAEWOO = 0x009053,
		VENDOR_DENON = 0x0005CD,
		VENDOR_GOOGLE = 0x001a11,
		VENDOR_GRUNDIG = 0x00D0D5,
		VENDOR_HARMAN_KARDON = 0x001950,
		VENDOR_HARMAN_KARDON2 = 0x9C645E,
		VENDOR_LG = 0x00E091,
		VENDOR_LOEWE = 0x000982,
		VENDOR_MARANTZ = 0x000678,
		VENDOR_MEDION = 0x000CB8,
		VENDOR_ONKYO = 0x0009B0,
		VENDOR_OPPO = 0x0022de,
		VENDOR_PANASONIC = 0x008045,
		VENDOR_PHILIPS = 0x00903E,
		VENDOR_PIONEER = 0x00E036,
		VENDOR_PULSE_EIGHT = 0x001582,
		VENDOR_SAMSUNG = 0x0000F0,
		VENDOR_SHARP = 0x08001F,
		VENDOR_SONY = 0x080046,
		VENDOR_TOSHIBA = 0x000039,
		VENDOR_TOSHIBA2 = 0x000CE7,
		VENDOR_VIZIO = 0x6B746D,
		VENDOR_YAMAHA = 0x00A0DE,
		VENDOR_UNKNOWN = 0
	};

	enum CEC_KEYS {
		RC_SELECT = 0x00,
		RC_UP = 0x01,
		RC_DOWN = 0x02,
		RC_LEFT = 0x03,
		RC_RIGHT = 0x04,
		RC_RIGHT_UP = 0x05,
		RC_RIGHT_DOWN = 0x06,
		RC_LEFT_UP = 0x07,
		RC_LEFT_DOWN = 0x08,
		RC_ROOT_MENU = 0x09,
		RC_SETUP_MENU = 0x0A,
		RC_CONTENTS_MENU = 0x0B,
		RC_FAVORITE_MENU = 0x0C,
		RC_EXIT = 0x0D,
		RC_0 = 0x20,
		RC_1 = 0x21,
		RC_2 = 0x22,
		RC_3 = 0x23,
		RC_4 = 0x24,
		RC_5 = 0x25,
		RC_6 = 0x26,
		RC_7 = 0x27,
		RC_8 = 0x28,
		RC_9 = 0x29,
		RC_CHANNEL_UP = 0x30,
		RC_CHANNEL_DOWN = 0x31,
		RC_INFO = 0x35,
		RC_HELP = 0x36,
		RC_PAGE_UP = 0x37,
		RC_PAGE_DOWN = 0x38,
		RC_POWER = 0x40,
		RC_VOLUME_UP = 0x41,
		RC_VOLUME_DOWN = 0x42,
		RC_MUTE = 0x43,
		RC_PLAY = 0x44,
		RC_STOP = 0x45,
		RC_PAUSE = 0x46,
		RC_RECORD = 0x47,
		RC_RWD = 0x48,
		RC_FWD = 0x49,
		RC_EPG = 0x53,
		RC_TIMER = 0x54,
		RC_PLAY_F = 0x60,
		RC_PAUSEPLAY_F = 0x61,
		RC_REC_F = 0x62,
		RC_STOP_F = 0x64,
		RC_MUTE_F = 0x65,
		RC_POWER_F = 0x6B,
		RC_POWER_OFF = 0x6C,
		RC_POWER_ON = 0x6D,
		RC_BLUE = 0x71,
		RC_RED = 0x72,
		RC_GREEN = 0x73,
		RC_YELLOW = 0x74,
	};

	enum CEC_DEVICE_TYPE {
		DEVICE_TYPE_TV = 0,
		DEVICE_TYPE_RECORDING,
		DEVICE_TYPE_RESERVED,
		DEVICE_TYPE_TUNER,
		DEVICE_TYPE_PLAYBACK,
		DEVICE_TYPE_AUDIO_SYSTEM,
		DEVICE_TYPE_PURE_SWITCH,
		DEVICE_TYPE_VIDEO_PROCESSOR
	};

	enum CEC_POWER_STATE
	{
		POWER_STATE_ON = 0,
		POWER_STATE_STANDBY = 1,
		POWER_STATE_TRANSITION_STANDBY_TO_ON = 2,
		POWER_STATE_TRANSITION_ON_TO_STANDBY = 3,
		POWER_STATE_UNKNOWN = 0xF,
	};

	enum CEC_DECK_INFO
	{
		DECK_INFO_PLAY = 0x11,
		DECK_INFO_RECORD,
		DECK_INFO_PLAY_REVERSE,
		DECK_INFO_STILL,
		DECK_INFO_SLOW,
		DECK_INFO_SLOW_REVERSE,
		DECK_INFO_FFW,
		DECK_INFO_RWD,
		DECK_INFO_NO_MEDIA,
		DECK_INFO_STOP,
		DECK_INFO_SKIP_FWD,
		DECK_INFO_SKIP_RWD,
		DECK_INFO_INDEX_SEARCH_FWD,
		DECK_INFO_INDEX_SEARCH_REVERSE,
		DECK_INFO_OTHER_STATE
	};
"""