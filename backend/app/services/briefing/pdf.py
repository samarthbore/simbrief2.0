import io
from datetime import datetime, timezone
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)


def generate_flight_briefing_pdf(
    plan_data: Dict[str, Any],
    branding_title: str = "Aviation Flight Planner",
) -> bytes:
    """
    Generate an OFP (Operational Flight Plan) PDF briefing document using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )
    bold_body_style = ParagraphStyle(
        "BoldBodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#b91c1c"),
        alignment=1,  # Center
    )

    elements = []

    # Header with Branding
    header_table_data = [
        [
            Paragraph(f"<b>{branding_title.upper()}</b>", title_style),
            Paragraph(
                f"<b>OFP BRIEFING</b><br/>ID: {plan_data.get('plan_code', 'N/A')}<br/>"
                f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                subtitle_style,
            ),
        ]
    ]
    header_table = Table(header_table_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=6, spaceAfter=8))

    # Educational Disclaimer Box
    elements.append(
        Table(
            [[Paragraph("SIMULATION & EDUCATIONAL USE ONLY — NOT FOR REAL-WORLD FLIGHT OPERATIONS OR DISPATCH", disclaimer_style)]],
            colWidths=[7.0 * inch],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fee2e2")),
                ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#ef4444")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ],
        )
    )
    elements.append(Spacer(1, 10))

    # Flight Summary Table
    dep = plan_data.get("departure", {})
    dest = plan_data.get("destination", {})
    ac = plan_data.get("aircraft", {})

    dep_text = f"<b>{dep.get('ident', 'N/A')}</b> ({dep.get('icao', '')}/{dep.get('iata', '')})<br/>{dep.get('name', 'Unknown')}<br/>{dep.get('municipality', '')}, {dep.get('iso_country', '')}<br/>Elev: {dep.get('elevation_ft', 'N/A')} ft"
    dest_text = f"<b>{dest.get('ident', 'N/A')}</b> ({dest.get('icao', '')}/{dest.get('iata', '')})<br/>{dest.get('name', 'Unknown')}<br/>{dest.get('municipality', '')}, {dest.get('iso_country', '')}<br/>Elev: {dest.get('elevation_ft', 'N/A')} ft"

    flight_info = [
        [
            Paragraph("<b>DEPARTURE</b>", bold_body_style),
            Paragraph(dep_text, body_style),
            Paragraph("<b>DESTINATION</b>", bold_body_style),
            Paragraph(dest_text, body_style),
        ],
        [
            Paragraph("<b>AIRCRAFT</b>", bold_body_style),
            Paragraph(f"<b>{ac.get('name', 'N/A')}</b> [{ac.get('identifier', 'N/A')}]<br/>Cruise: {ac.get('cruise_speed_kts', 'N/A')} KTAS<br/>Fuel Flow: {ac.get('fuel_flow_kg_hr', 'N/A')} kg/h", body_style),
            Paragraph("<b>CRUISE / OBJECTIVE</b>", bold_body_style),
            Paragraph(f"Alt: FL{int(plan_data.get('cruise_altitude_ft', 33000)/100):03d}<br/>Objective: {plan_data.get('routing_objective', 'Great Circle').replace('_', ' ').title()}", body_style),
        ],
    ]
    summary_table = Table(flight_info, colWidths=[1.5 * inch, 2.0 * inch, 1.5 * inch, 2.0 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # Fuel and Operational Performance
    perf = plan_data.get("performance", {})
    flight_time_formatted = perf.get("flight_time_formatted", f"{round(plan_data.get('estimated_flight_time_min', 0))}m")
    
    fuel_table_data = [
        [
            Paragraph("<b>CATEGORY</b>", bold_body_style),
            Paragraph("<b>VALUE</b>", bold_body_style),
            Paragraph("<b>NOTES</b>", bold_body_style),
        ],
        [
            Paragraph("Total Distance", body_style),
            Paragraph(f"<b>{round(plan_data.get('total_distance_nm', 0), 1)} NM</b> ({round(plan_data.get('total_distance_nm', 0) * 1.852, 1)} km)", body_style),
            Paragraph("Great-circle / navigation arc", body_style),
        ],
        [
            Paragraph("Estimated Flight Time", body_style),
            Paragraph(f"<b>{flight_time_formatted}</b>", body_style),
            Paragraph("Zero-wind groundspeed assumption", body_style),
        ],
        [
            Paragraph("Trip Fuel", body_style),
            Paragraph(f"{round(perf.get('trip_fuel_kg', plan_data.get('estimated_fuel_burn_kg', 0)), 1)} kg", body_style),
            Paragraph("En-route burn", body_style),
        ],
        [
            Paragraph("Reserve Fuel (45 min)", body_style),
            Paragraph(f"{round(perf.get('reserve_fuel_kg', 0), 1)} kg", body_style),
            Paragraph("IFR statutory alternate & final reserve", body_style),
        ],
        [
            Paragraph("Taxi Allowance", body_style),
            Paragraph(f"{round(perf.get('taxi_fuel_kg', 0), 1)} kg", body_style),
            Paragraph("Ground taxi & APU consumption", body_style),
        ],
        [
            Paragraph("<b>TOTAL REQUIRED FUEL</b>", bold_body_style),
            Paragraph(f"<b>{round(perf.get('total_fuel_required_kg', plan_data.get('estimated_fuel_burn_kg', 0)), 1)} kg</b>", bold_body_style),
            Paragraph("Minimum ramp release fuel", bold_body_style),
        ],
    ]
    fuel_table = Table(fuel_table_data, colWidths=[2.2 * inch, 2.0 * inch, 2.8 * inch])
    fuel_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(Paragraph("<b>PERFORMANCE & FUEL BREAKDOWN</b>", section_style))
    elements.append(fuel_table)
    elements.append(Spacer(1, 10))

    # Waypoint Navigation Log Table
    waypoints: List[Dict[str, Any]] = plan_data.get("waypoints", [])
    if waypoints:
        wp_rows = [
            [
                Paragraph("<b>#</b>", bold_body_style),
                Paragraph("<b>IDENT</b>", bold_body_style),
                Paragraph("<b>TYPE</b>", bold_body_style),
                Paragraph("<b>LAT / LON</b>", bold_body_style),
                Paragraph("<b>CRS (°T)</b>", bold_body_style),
                Paragraph("<b>LEG (NM)</b>", bold_body_style),
                Paragraph("<b>TOTAL (NM)</b>", bold_body_style),
            ]
        ]

        for idx, wp in enumerate(waypoints[:30]):  # Limit to 30 for PDF fit
            wp_rows.append(
                [
                    Paragraph(str(idx + 1), body_style),
                    Paragraph(f"<b>{wp.get('ident', f'WP{idx+1}')}</b>", body_style),
                    Paragraph(wp.get("node_type", "FIX"), body_style),
                    Paragraph(f"{wp.get('latitude', 0.0):.3f}, {wp.get('longitude', 0.0):.3f}", body_style),
                    Paragraph(f"{wp.get('bearing_deg', 0.0):.0f}°", body_style),
                    Paragraph(f"{wp.get('leg_distance_nm', 0.0):.1f}", body_style),
                    Paragraph(f"{wp.get('cumulative_distance_nm', 0.0):.1f}", body_style),
                ]
            )

        wp_table = Table(wp_rows, colWidths=[0.3 * inch, 1.2 * inch, 0.8 * inch, 2.1 * inch, 0.8 * inch, 0.9 * inch, 0.9 * inch])
        wp_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(KeepTogether([
            Paragraph("<b>NAVIGATION LOG & ROUTE WAYPOINTS</b>", section_style),
            wp_table,
        ]))
        elements.append(Spacer(1, 10))

    # Assumptions & Limitations Footer
    notes = [
        f"<b>Calculation Assumptions:</b> {perf.get('assumptions', plan_data.get('calculation_assumptions', 'Standard zero-wind profile'))}",
        f"<b>Data Sources:</b> Airport data normalized from OurAirports (Public Domain / CC0). World texture from Natural Earth (Public Domain).",
    ]
    for n in notes:
        elements.append(Paragraph(n, body_style))
        elements.append(Spacer(1, 3))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
