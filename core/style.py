# core/style.py
from PySide6.QtWidgets import QApplication

# Material 3 "Deep Blue" Palette
H1 = "font-size: 24px; font-weight: bold; color: #1a1a1a; margin-bottom: 10px;"
BODY = "font-size: 14px; color: #1b1b1f;"

COLORS = {
    "primary": "#3448A3",           # Deeper, more vibrant blue
    "onPrimary": "#FFFFFF",
    "primaryContainer": "#DEE0FF",  # Soft blue container
    "onPrimaryContainer": "#00105C",
    
    "secondary": "#5B5D72",         # Neutral-ish secondary
    "onSecondary": "#FFFFFF",
    "secondaryContainer": "#E0E1F9",
    "onSecondaryContainer": "#181A2C",
    
    "tertiary": "#77536D",          # Rose/Mauve accent
    "onTertiary": "#FFFFFF",
    "tertiaryContainer": "#FFD7F1",
    "onTertiaryContainer": "#2D1228",
    
    "error": "#BA1A1A",
    "onError": "#FFFFFF",
    "errorContainer": "#FFDAD6",
    "onErrorContainer": "#410002",
    
    "background": "#FEFBFF",        # Very light off-white
    "onBackground": "#1B1B1F",
    "surface": "#FEFBFF",
    "onSurface": "#1B1B1F",
    "surfaceVariant": "#E3E1EC",    # For inputs, dividers
    "onSurfaceVariant": "#46464F",
    "outline": "#767680",
    "outlineVariant": "#C7C5D0",
    
    "shadow": "#000000",
    "scrim": "#000000",
    "inverseSurface": "#303034",
    "inverseOnSurface": "#F2F0F4",
    "inversePrimary": "#BAC3FF",
}

def material_stylesheet() -> str:
    c = COLORS
    return f"""
    /* Global Reset & Typography */
    * {{
        font-family: 'Segoe UI', 'Roboto', 'Inter', sans-serif;
        font-size: 14px;
        color: {c['onSurface']};
        selection-background-color: {c['primary']};
        selection-color: {c['onPrimary']};
    }}
    
    QMainWindow, QWidget {{
        background-color: {c['background']};
    }}

    /* --- Inputs (TextFields) --- */
    QLineEdit, QTextEdit, QPlainTextEdit, QDateTimeEdit, QComboBox {{
        background-color: {c['surface']};
        border: 1px solid {c['outline']};
        border-radius: 4px; /* Material 3 uses smaller radius for inputs usually, or full pill */
        padding: 8px 12px;
        font-size: 14px;
        color: {c['onSurface']};
        selection-background-color: {c['primary']};
    }}
    QLineEdit:hover, QTextEdit:hover, QComboBox:hover {{
        border: 1px solid {c['onSurface']}; /* Darker outline on hover */
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 2px solid {c['primary']}; /* Thick primary border on focus */
        padding: 7px 11px; /* Adjust padding to prevent shift */
        background-color: {c['surface']};
    }}
    QLineEdit[readOnly="true"] {{
        background-color: {c['surfaceVariant']};
        border: none;
    }}

    /* --- Buttons --- */
    QPushButton {{
        border-radius: 20px; /* Full pill shape */
        padding: 10px 24px;
        font-weight: 600;
        font-size: 14px;
        border: none;
    }}
    
    /* Filled Button (Primary) */
    QPushButton[class="primary"] {{
        background-color: {c['primary']};
        color: {c['onPrimary']};
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {c['primary']}D9; /* 85% opacity */
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: {c['primary']}B3; /* 70% opacity */
    }}

    /* Tonal Button (Secondary/Tonal) */
    QPushButton[class="tonal"] {{
        background-color: {c['secondaryContainer']};
        color: {c['onSecondaryContainer']};
    }}
    QPushButton[class="tonal"]:hover {{
        background-color: {c['secondaryContainer']}D9;
    }}
    
    /* Outlined Button */
    QPushButton[class="outlined"] {{
        background-color: transparent;
        border: 1px solid {c['outline']};
        color: {c['primary']};
    }}
    QPushButton[class="outlined"]:hover {{
        background-color: {c['primary']}14; /* 8% opacity primary overlay */
        border: 1px solid {c['primary']};
    }}
    
    /* Text Button (Ghost) */
    QPushButton[class="text"] {{
        background-color: transparent;
        color: {c['primary']};
        padding: 8px 16px;
    }}
    QPushButton[class="text"]:hover {{
        background-color: {c['primary']}14;
    }}

    /* --- Cards (Surfaces) --- */
    QFrame#Card {{
        background-color: {c['surface']};
        border: 1px solid {c['outlineVariant']};
        border-radius: 12px;
    }}
    /* Elevated Card effect if needed, usually requires shadow implementation which QSS doesn't do well alone */

    /* --- Navigation Rail --- */
    QPushButton#NavButton {{
        text-align: left;
        padding: 12px 16px;
        border-radius: 24px; /* Pill shape */
        margin: 4px 8px;
        font-weight: 500;
        color: {c['onSurfaceVariant']};
        background-color: transparent;
    }}
    QPushButton#NavButton:hover {{
        background-color: {c['onSurface']}14; /* 8% opacity */
    }}
    QPushButton#NavButton:checked, QPushButton#NavButton[class="primary"] {{
        background-color: {c['secondaryContainer']};
        color: {c['onSecondaryContainer']};
        font-weight: 700;
    }}

    /* --- Tables --- */
    QTableView {{
        background-color: {c['surface']};
        border: 1px solid {c['outlineVariant']};
        border-radius: 8px;
        gridline-color: {c['surfaceVariant']};
        selection-background-color: {c['primaryContainer']};
        selection-color: {c['onPrimaryContainer']};
    }}
    QTableView::item:selected {{
        background-color: {c['primaryContainer']};
        color: {c['onPrimaryContainer']};
        border-bottom: 2px solid {c['primary']}; /* Add a bottom border to highlight */
    }}
    QTableView::item:hover {{
        background-color: {c['surfaceVariant']}; /* Hover effect */
    }}
    QTableView::item:selected:hover {{
        background-color: {c['primaryContainer']}; /* Keep selection color on hover */
    }}
    QHeaderView::section {{
        background-color: {c['surface']};
        color: {c['onSurfaceVariant']};
        border: none;
        border-bottom: 1px solid {c['outlineVariant']};
        padding: 12px;
        font-weight: 600;
    }}
    QTableCornerButton::section {{
        background-color: {c['surface']};
        border: none;
    }}

    /* --- Scrollbars --- */
    QScrollBar:vertical {{
        border: none;
        background: {c['surfaceVariant']};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['outline']};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    """

def apply_style(app: QApplication):
    app.setStyleSheet(material_stylesheet())
    # Set a default font if possible, though QSS handles most
    from PySide6.QtGui import QFont
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
