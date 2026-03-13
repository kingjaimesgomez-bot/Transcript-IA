"""
exporters/pdf_exporter.py
Genera PDF profesional del arreglo musical completo.
"""
from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas as rl_canvas


GREEN  = colors.HexColor("#00ff87")
AMBER  = colors.HexColor("#e8c547")
DARK   = colors.HexColor("#0f0f14")
WHITE  = colors.white
GRAY   = colors.HexColor("#4a4a55")
LGRAY  = colors.HexColor("#1c1c24")


class PDFExporter:

    def export(self, analysis: dict, output_path: str) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2.5*cm, bottomMargin=2*cm,
            title=analysis.get("titulo", "Arreglo Musical"),
            author="Transcript IA",
        )
        styles = self._build_styles()
        story = self._build_story(analysis, styles)
        doc.build(
            story,
            onFirstPage=self._draw_header_footer,
            onLaterPages=self._draw_header_footer,
        )
        return output_path

    def export_bytes(self, analysis: dict) -> bytes:
        import io
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2.5*cm, bottomMargin=2*cm,
            title=analysis.get("titulo", "Arreglo Musical"),
            author="Transcript IA",
        )
        styles = self._build_styles()
        story = self._build_story(analysis, styles)
        doc.build(story, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
        return buf.getvalue()

    def _build_styles(self) -> dict:
        return {
            "title": ParagraphStyle(
                "title", fontSize=28, textColor=WHITE,
                backColor=DARK, alignment=TA_CENTER,
                fontName="Helvetica-Bold", spaceAfter=6, leading=34,
            ),
            "subtitle": ParagraphStyle(
                "subtitle", fontSize=11, textColor=AMBER,
                alignment=TA_CENTER, fontName="Helvetica",
                spaceAfter=4, leading=14,
            ),
            "section": ParagraphStyle(
                "section", fontSize=13, textColor=GREEN,
                fontName="Helvetica-Bold", spaceBefore=16,
                spaceAfter=6, leading=16,
            ),
            "subsection": ParagraphStyle(
                "subsection", fontSize=11, textColor=AMBER,
                fontName="Helvetica-Bold", spaceBefore=10,
                spaceAfter=4, leading=14,
            ),
            "body": ParagraphStyle(
                "body", fontSize=9, textColor=WHITE,
                fontName="Helvetica", leading=14, spaceAfter=4,
            ),
            "mono": ParagraphStyle(
                "mono", fontSize=8, textColor=GREEN,
                fontName="Courier", leading=12,
                spaceAfter=3, leftIndent=12,
            ),
        }

    def _build_story(self, analysis: dict, styles: dict) -> list:
        s = styles
        story = []

        story.append(Paragraph(analysis.get("titulo", "Arreglo Musical"), s["title"]))
        story.append(Spacer(1, 0.3*cm))

        info_data = [[
            "🎵 Tonalidad", analysis.get("tonalidad","–"),
            "⏱ Tempo", f"{analysis.get('tempo','–')} BPM",
            "📐 Compás", analysis.get("compas","4/4"),
            "🎭 Género", analysis.get("genero","–"),
        ]]
        info_table = Table(info_data, colWidths=[2.5*cm]*8)
        info_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), LGRAY),
            ("TEXTCOLOR",    (0,0),(-1,-1), GRAY),
            ("TEXTCOLOR",    (1,0),(1,0),   GREEN),
            ("TEXTCOLOR",    (3,0),(3,0),   GREEN),
            ("TEXTCOLOR",    (5,0),(5,0),   GREEN),
            ("TEXTCOLOR",    (7,0),(7,0),   GREEN),
            ("FONTNAME",     (0,0),(-1,-1), "Helvetica"),
            ("FONTSIZE",     (0,0),(-1,-1), 8),
            ("ALIGN",        (0,0),(-1,-1), "CENTER"),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
            ("GRID",         (0,0),(-1,-1), 0.5, DARK),
            ("TOPPADDING",   (0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("▸ ESTRUCTURA DE LA CANCIÓN", s["section"]))
        estructura = analysis.get("estructura", [])
        if estructura:
            struct_data = [["Sección", "Compases", "Descripción"]]
            for sec in estructura:
                struct_data.append([
                    sec.get("seccion",""),
                    sec.get("compases",""),
                    sec.get("descripcion",""),
                ])
            struct_table = Table(struct_data, colWidths=[3*cm, 2.5*cm, 11.5*cm])
            struct_table.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,0),  DARK),
                ("TEXTCOLOR",     (0,0),(-1,0),  GREEN),
                ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0,0),(-1,-1), 8),
                ("BACKGROUND",    (0,1),(-1,-1), LGRAY),
                ("TEXTCOLOR",     (0,1),(-1,-1), WHITE),
                ("TEXTCOLOR",     (0,1),(0,-1),  AMBER),
                ("FONTNAME",      (0,1),(0,-1),  "Helvetica-Bold"),
                ("ALIGN",         (1,0),(1,-1),  "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("GRID",          (0,0),(-1,-1), 0.5, DARK),
                ("TOPPADDING",    (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ]))
            story.append(struct_table)
        story.append(Spacer(1, 0.4*cm))

        story.append(HRFlowable(width="100%", thickness=1, color=LGRAY))
        story.append(Paragraph("▸ ARREGLO POR INSTRUMENTO", s["section"]))

        for inst in analysis.get("instrumentos", []):
            block = []
            block.append(Paragraph(
                f"◈  {inst.get('nombre','Instrumento').upper()}  "
                f"<font color='#4a4a55' size='8'>— Rango: {inst.get('rango','–')} "
                f"· MIDI: {inst.get('midi_program',0)}</font>",
                s["subsection"]
            ))
            for sec in inst.get("secciones", []):
                block.append(Paragraph(
                    f"<b><font color='#e8c547'>{sec.get('nombre','')}:</font></b>  {sec.get('descripcion','')}",
                    s["body"]
                ))
                if sec.get("patron"):
                    block.append(Paragraph(f"Patrón: {sec.get('patron')}", s["mono"]))
                if sec.get("tecnicas"):
                    block.append(Paragraph(f"Técnicas: {', '.join(sec.get('tecnicas',[]))}", s["mono"]))
                if sec.get("notas_destacadas"):
                    block.append(Paragraph(f"Notas destacadas: {', '.join(sec.get('notas_destacadas',[]))}", s["mono"]))
            story.append(KeepTogether(block))
            story.append(Spacer(1, 0.2*cm))

        armonia = analysis.get("armonia", {})
        if armonia:
            story.append(HRFlowable(width="100%", thickness=1, color=LGRAY))
            story.append(Paragraph("▸ ARMONÍA Y PROGRESIONES", s["section"]))
            for label, val in [
                ("Progresión principal", armonia.get("progresion_principal","")),
                ("Coro",                armonia.get("progresion_coro","")),
                ("Modo",                armonia.get("modo","")),
                ("Modulaciones",        ", ".join(armonia.get("modulaciones",[])) or "Ninguna"),
            ]:
                if val:
                    story.append(Paragraph(
                        f"<font color='#e8c547'>{label}:</font>  <font color='#00ff87'>{val}</font>",
                        s["body"]
                    ))
            story.append(Spacer(1, 0.3*cm))

        produccion = analysis.get("produccion", {})
        if produccion:
            story.append(HRFlowable(width="100%", thickness=1, color=LGRAY))
            story.append(Paragraph("▸ NOTAS DE PRODUCCIÓN", s["section"]))
            for fx in produccion.get("efectos", []):
                story.append(Paragraph(f"  › {fx}", s["mono"]))
            if produccion.get("dinamica"):
                story.append(Paragraph(
                    f"<font color='#e8c547'>Dinámica:</font>  {produccion.get('dinamica')}",
                    s["body"]
                ))

        notas = analysis.get("notas_arreglista","")
        if notas:
            story.append(HRFlowable(width="100%", thickness=1, color=LGRAY))
            story.append(Paragraph("▸ NOTAS DEL ARREGLISTA", s["section"]))
            story.append(Paragraph(notas, s["body"]))

        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            "<font color='#1c1c24'>Generado por Transcript IA · Powered by Claude AI</font>",
            ParagraphStyle("footer_note", fontSize=7, alignment=TA_CENTER)
        ))
        return story

    def _draw_header_footer(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        canvas.setFillColor(DARK)
        canvas.rect(0, h-1.8*cm, w, 1.8*cm, fill=1, stroke=0)
        canvas.setFillColor(GREEN)
        canvas.rect(0, h-1.8*cm, w, 2, fill=1, stroke=0)
        canvas.setFillColor(GREEN)
        canvas.rect(1.8*cm, h-1.4*cm, 0.9*cm, 0.9*cm, fill=1, stroke=0)
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(2.0*cm, h-1.15*cm, "T")
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(3.0*cm, h-1.15*cm, "Transcript IA")
        canvas.setFillColor(GRAY)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(3.0*cm, h-1.45*cm, "AI Music Arranger")

        canvas.setFillColor(DARK)
        canvas.rect(0, 0, w, 1.2*cm, fill=1, stroke=0)
        canvas.setFillColor(GREEN)
        canvas.rect(0, 1.2*cm, w, 1, fill=1, stroke=0)
        canvas.setFillColor(GRAY)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(2*cm, 0.45*cm, "Transcript IA · Powered by Claude AI")
        canvas.drawRightString(w-2*cm, 0.45*cm, f"Página {doc.page}")

        canvas.restoreState()
