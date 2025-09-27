# core/style.py
from PySide6.QtWidgets import QApplication

COLORS = {
    "primary": "#22307B",
    "primaryContainer": "#E7EAFF",
    "onPrimary": "#FFFFFF",
    "secondary": "#4A5BD3",
    "surface": "#F5F7FB",
    "surfaceVariant": "#EEF1F8",
    "onSurface": "#0F172A",
    "outline": "#D3D9EC",
    "muted": "#475569",
}

def material_stylesheet() -> str:
    c = COLORS
    return f"""
    * {{
        font-family: 'Inter','Segoe UI',system-ui,sans-serif;
        color:{c['onSurface']};
    }}
    QMainWindow, QWidget {{ background:{c['surface']}; }}

    /* Inputs */
    QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
        background:white; border:1px solid {c['outline']};
        border-radius:12px; padding:10px 12px;
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
        border:2px solid {c['secondary']};
    }}

    /* Buttons */
    QPushButton.primary {{
        background:{c['primary']}; color:{c['onPrimary']};
        border:none; border-radius:12px; padding:12px 16px; font-weight:700;
    }}
    QPushButton.primary:hover {{ background:{c['secondary']}; }}
    QPushButton.tonal {{
        background:{c['primaryContainer']}; color:{c['primary']};
        border:none; border-radius:12px; padding:12px 16px; font-weight:700;
    }}
    QPushButton.outlined {{
        background:transparent; color:{c['primary']};
        border:1.5px solid {c['primary']}; border-radius:12px; padding:10px 14px;
        font-weight:700;
    }}

    /* Cards & Tables */
    #Card {{
        background:white; border:1px solid {c['outline']};
        border-radius:18px;
    }}
    QTableView {{
        background:white; border:1px solid {c['outline']}; border-radius:14px;
        gridline-color:{c['outline']};
        selection-background-color:{c['primaryContainer']};
        selection-color:{c['primary']};
        outline:0;
    }}
    QHeaderView::section {{
        background:{c['surfaceVariant']}; border:none; padding:10px 12px; font-weight:800;
    }}

    /* Nav buttons (left rail) */
    #NavButton {{
        min-height:42px; text-align:left; padding-left:16px;
    }}

    /* KPI labels */
    .kpiTitle {{ font-size:12px; color:{c['muted']}; }}
    .kpiValue {{ font-size:28px; font-weight:900; }}
    """

def apply_style(app: QApplication):
    app.setStyleSheet(material_stylesheet())
