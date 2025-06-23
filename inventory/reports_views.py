# backend/inventory/reports_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, BaseRenderer
from .models import InventoryItem, InventoryMovement # Assuming Category and Supplier are imported via InventoryItem
from .serializers import InventoryItemSerializer, InventoryMovementSerializer
from datetime import datetime, timedelta, date
from django.db import models 

# Dependencias para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO


class PassthroughPDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class InventoryReportView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, PassthroughPDFRenderer]

    def get(self, request, *args, **kwargs):
        report_type = request.query_params.get('report_type')
        report_format = request.query_params.get('format', 'json')
        
        data = []
        message = ""
        
        try:
            if report_type == 'current_stock':
                items = InventoryItem.objects.all()
                serializer = InventoryItemSerializer(items, many=True)
                data = serializer.data
                message = 'Reporte de stock actual generado exitosamente.'

            elif report_type == 'low_stock':
                items = InventoryItem.objects.filter(quantity__lte=models.F('low_stock_threshold'))
                serializer = InventoryItemSerializer(items, many=True)
                data = serializer.data
                message = 'Reporte de ítems con stock bajo generado exitosamente.'

            elif report_type == 'expiring_soon':
                today = date.today()
                expiring_threshold_date_6_months = today + timedelta(days=180)
                
                items = InventoryItem.objects.filter(
                    expiration_date__gte=today,
                    expiration_date__lte=expiring_threshold_date_6_months
                )
                serializer = InventoryItemSerializer(items, many=True)
                data = serializer.data
                message = 'Reporte de ítems por vencer pronto generado exitosamente.'

            elif report_type == 'movement_history':
                start_date_str = request.query_params.get('start_date')
                end_date_str = request.query_params.get('end_date')
                item_id = request.query_params.get('item_id')
                movement_type = request.query_params.get('movement_type')
                movements = InventoryMovement.objects.all().order_by('-movement_date')

                if start_date_str:
                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        movements = movements.filter(movement_date__date__gte=start_date)
                    except ValueError:
                        return Response({"error": "Formato de fecha de inicio inválido. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
                
                if end_date_str:
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                        movements = movements.filter(movement_date__date__lte=end_date)
                    except ValueError:
                        return Response({"error": "Formato de fecha de fin inválido. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
                
                if item_id:
                    movements = movements.filter(item_id=item_id)
                
                if movement_type:
                    movements = movements.filter(movement_type=movement_type)

                serializer = InventoryMovementSerializer(movements, many=True)
                data = serializer.data
                message = 'Reporte de historial de movimientos generado exitosamente.'

            else:
                return Response({"error": "Tipo de reporte inválido."}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(f"Error general al obtener datos del reporte: {e}")
            return Response({"error": f"Error interno al preparar los datos del reporte: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if report_format == 'pdf':
            try:
                pdf_buffer = None
                if report_type in ['current_stock', 'low_stock', 'expiring_soon']:
                    pdf_buffer = self.generate_item_report_pdf(report_type, data)
                elif report_type == 'movement_history':
                    pdf_buffer = self.generate_movement_report_pdf(report_type, data)
                else:
                    return Response({"error": "Tipo de reporte no soportado para PDF."}, status=status.HTTP_400_BAD_REQUEST)

                response = Response(pdf_buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf"'
                return response
            
            except Exception as e:
                # This catch will now provide a more specific error if 'category_name' is the issue
                print(f"Error al generar el PDF para reporte {report_type}: {e}")
                return Response({"error": f"Error al generar el PDF: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'report_type': report_type,
            'data': data,
            'message': message
        }, status=status.HTTP_200_OK)

    def generate_item_report_pdf(self, report_type, data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        title_map = {
            'current_stock': 'Reporte de Stock Actual',
            'low_stock': 'Reporte de Ítems con Stock Bajo',
            'expiring_soon': 'Reporte de Ítems por Vencer Pronto',
        }
        elements.append(Paragraph(title_map.get(report_type, 'Reporte de Inventario'), styles['h1']))
        elements.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['h3']))
        elements.append(Spacer(1, 0.2 * inch))

        headers = ['Nombre', 'N° Serie', 'Cant.', 'Umbral', 'Categoría', 'Proveedor', 'Fecha Venc.', 'Estado Stock', 'Estado Venc.']
        table_data = [headers]

        for item in data:
            # Safely get expiration_date, handling potential None
            expiration_date_str = item.get('expiration_date')
            if expiration_date_str:
                try:
                    expiration_date_str = datetime.strptime(expiration_date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                except ValueError:
                    expiration_date_str = 'Formato Inválido' # Or log it
            else:
                expiration_date_str = 'N/A'

            # Use .get() method to safely access dictionary keys, providing a default if key is missing or value is None
            status_stock = 'Bajo' if item.get('is_low_stock') else 'Normal'
            status_expiry = 'VENCIDO' if item.get('is_expired') else ('Por Vencer' if item.get('is_expiring_soon') else 'Vigente')
            
            table_data.append([
                Paragraph(item.get('name', 'N/A'), styles['Normal']),
                item.get('serial_number', 'N/A'),
                str(item.get('quantity', '0')), # Ensure quantity is always a string
                str(item.get('low_stock_threshold', '0')), # Ensure threshold is always a string
                item.get('category_name', 'N/A'), # FIX: Use .get() here for robustness
                item.get('supplier_name', 'N/A'), # FIX: Use .get() here for robustness
                expiration_date_str,
                status_stock,
                status_expiry
            ])

        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.5*inch, 0.6*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#DCE6F1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_movement_report_pdf(self, report_type, data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph('Reporte de Historial de Movimientos', styles['h1']))
        elements.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['h3']))
        elements.append(Spacer(1, 0.2 * inch))

        headers = ['Ítem', 'Tipo Mov.', 'Cant.', 'Realizado por', 'Fecha y Hora', 'Proyecto', 'Notas']
        table_data = [headers]

        for movement in data:
            try:
                mov_date_str = movement.get('movement_date')
                if mov_date_str:
                    # Handle both Z and non-Z formats if possible, or ensure consistency
                    mov_date = datetime.fromisoformat(mov_date_str.replace('Z', '+00:00'))
                    movement_date_str = mov_date.strftime('%d/%m/%Y %H:%M')
                else:
                    movement_date_str = 'N/A'
            except (ValueError, TypeError):
                movement_date_str = str(movement.get('movement_date', 'Error de Fecha')) # Fallback for malformed dates

            table_data.append([
                Paragraph(movement.get('item_name', 'N/A'), styles['Normal']),
                movement.get('get_movement_type_display', movement.get('movement_type', 'N/A')),
                str(movement.get('quantity', '0')),
                movement.get('moved_by_username', 'N/A'),
                movement_date_str,
                movement.get('project', 'N/A'),
                Paragraph(movement.get('notes', 'N/A'), styles['Normal'])
            ])

        table = Table(table_data, colWidths=[1.5*inch, 0.8*inch, 0.5*inch, 1.2*inch, 1.2*inch, 1*inch, 1.7*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#DCE6F1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer