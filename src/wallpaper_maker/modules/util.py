STYLES = [
    "Blur",
    "Flip",
    "InverseBlur",
    "InverseBlurDarker",
    "InverseNegate",
    "InversePixelate",
    "LogoColors",
    "Negate",
    "Pixelate",
    "ThroughBlack",
]

NEED_BLUR = "OverlayBlur"
NEED_BLUR_DARK = set(["Blur", "InverseBlur"])
NEED_BLUR_DARKER = set(["InverseBlurDarker"])
NEED_BRIGHTENED = set(["Blur"])
NEED_FLIP = set(["Flip"])
NEED_LOGOCOLORS = set(["LogoColors"])
NEED_NEGATE = set(["InverseNegate", "Negate"])
NEED_PIXELATE = set(["InversePixelate", "Pixelate"])

ALL_COLORS_DICT = {
    "AerospaceOrange": "#FD5000",
    "AmaranthPurple": "#AC1361",
    "Amethyst": "#9B5DE5",
    "AnexiaBlue": "#003CA6",
    "Aquamarine": "#00F5D4",
    "ArchBlue": "#0F94D2",
    "Black": "#000000",
    "BrilliantRose": "#F15BB5",
    "CambridgeBlue": "#7DA27F",
    "DebianRed": "#A80030",
    "DeepSkyBlue": "#00BBF9",
    "EndeavourPurple": "#7E3EBE",
    "FedoraBlue": "#51A2DA",
    "KnappBlue": "#029AA9",
    "Lion": "#AD9667",
    "Maize": "#FEE440",
    "ManjaroGreen": "#35BFA4",
    "MidnightGreen": "#115E6B",
    "MintGreen": "#69B53F",
    "Nachtblau": "#222D5A",
    "Sapphire": "#004EAA",
    "SelectiveYellow": "#FFB92A",
    "SovietRed": "#CC0000",
    "SuseGreen": "#30BA78",
    "Tannengrün": "#27352A",
    "Tekhelet": "#592B8A",
    "UbuntuOrange": "#E95420",
    "Verkehrsrot": "#BB1F11",
    "White": "#FFFFFF",
}


class TempImagePointers:
    blurred_dark: str
    blurred_darker: str
    blurred: str
    brightened: str
    flipped: str
    logocolored: str
    mask: str
    negated: str
    pixelated: str
    shadow: str
    wal: str


class TempMaskPointers:
    logocolor: str
    mask: str
    maskname: str
    shadow: str
    size: tuple[int, int]


class TempEffectPointers:
    blurred_dark: str
    blurred_darker: str
    blurred: str
    brightened: str
    flipped: str
    negated: str
    pixelated: str
    size: tuple[int, int]
    wal: str
    walfile: str
    walname: str
