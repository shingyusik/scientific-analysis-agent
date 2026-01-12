"""
Centralized constants for the Scientific Analysis Agent application.

This module contains all magic numbers, sizes, delays, and default values
used throughout the application to improve maintainability.
"""

# =============================================================================
# Window Dimensions
# =============================================================================
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900

# =============================================================================
# UI Element Sizes
# =============================================================================
RESET_BUTTON_WIDTH = 50
SPINBOX_WIDTH = 100
CHAT_BUBBLE_MAX_WIDTH = 400
OFFSET_LIST_MIN_WIDTH = 400

# =============================================================================
# Timing / Delays (milliseconds)
# =============================================================================
UI_REENABLE_DELAY_MS = 100
DEFAULT_ANIMATION_INTERVAL_MS = 100
SCROLL_TO_BOTTOM_DELAY_MS = 10

# =============================================================================
# Text Preview Lengths
# =============================================================================
TOOL_RESULT_PREVIEW_LENGTH = 100
LOG_MESSAGE_PREVIEW_LENGTH = 50
CHAT_TOOL_PREVIEW_LENGTH = 80

# =============================================================================
# Rendering Defaults
# =============================================================================
DEFAULT_POINT_SIZE = 3.0
DEFAULT_LINE_WIDTH = 1.0
DEFAULT_GAUSSIAN_SCALE_FACTOR = 0.05
DEFAULT_OPACITY = 1.0
OPACITY_SLIDER_MAX = 100

# =============================================================================
# VTK Arrow/Preview Geometry
# =============================================================================
DEFAULT_ARROW_SHAFT_RADIUS = 0.05
DEFAULT_ARROW_TIP_RADIUS = 0.15
DEFAULT_ARROW_TIP_LENGTH = 0.3
DEFAULT_ARROW_RESOLUTION = 20
DEFAULT_PLANE_PREVIEW_OPACITY = 0.4

# =============================================================================
# Scalar Bar / Legend Defaults
# =============================================================================
DEFAULT_SCALAR_BAR_POSITION_X = 0.9
DEFAULT_SCALAR_BAR_POSITION_Y = 0.3
DEFAULT_SCALAR_BAR_WIDTH = 0.08
DEFAULT_SCALAR_BAR_HEIGHT = 0.4
DEFAULT_SCALAR_BAR_NUM_LABELS = 5
DEFAULT_SCALAR_BAR_TITLE_SEPARATION = 12

DEFAULT_LEGEND_SETTINGS = {
    "font_size": 12,
    "font_color": (1.0, 1.0, 1.0),
    "bold": True,
    "italic": False,
    "position_x": DEFAULT_SCALAR_BAR_POSITION_X,
    "position_y": DEFAULT_SCALAR_BAR_POSITION_Y,
    "width": DEFAULT_SCALAR_BAR_WIDTH,
    "height": DEFAULT_SCALAR_BAR_HEIGHT,
}

# =============================================================================
# Default Background Color
# =============================================================================
DEFAULT_BACKGROUND_COLOR = (0.32, 0.34, 0.43)

# =============================================================================
# Camera Default Position (Isometric)
# =============================================================================
DEFAULT_CAMERA_POSITION = (1, 1, 1)
DEFAULT_CAMERA_FOCAL_POINT = (0, 0, 0)
DEFAULT_CAMERA_VIEW_UP = (0, 0, 1)

# =============================================================================
# Orientation Axes Widget
# =============================================================================
AXES_WIDGET_VIEWPORT = (0.0, 0.0, 0.2, 0.2)

# =============================================================================
# Background Presets
# =============================================================================
BACKGROUND_PRESETS = {
    "Warm Gray (Default)": ((0.32, 0.34, 0.43), None),
    "Blue Gray": ((0.25, 0.30, 0.38), None),
    "Dark Gray": ((0.15, 0.15, 0.18), None),
    "Neutral Gray": ((0.3, 0.3, 0.3), None),
    "Light Gray": ((0.8, 0.8, 0.82), None),
    "White": ((0.95, 0.95, 0.97), None),
    "Black": ((0.05, 0.05, 0.07), None),
    "Gradient Background": ((0.2, 0.2, 0.3), (0.5, 0.5, 0.6)),
}

# =============================================================================
# Representation Styles
# =============================================================================
REPRESENTATION_STYLES = [
    "Surface",
    "Wireframe",
    "Points",
    "Surface With Edges",
    "Point Gaussian",
]
