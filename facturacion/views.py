from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Factura, FacturaItem, Cliente
from .forms import FacturaForm, FacturaItemFormSet, ClienteForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
import csv
from datetime import date
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import io
try:
    from openpyxl import Workbook
    _HAS_OPENPYXL = True
except Exception:
    _HAS_OPENPYXL = False
from django.contrib.staticfiles import finders
from django.conf import settings

def is_hr_or_admin(user):
    return getattr(user, 'role', None) in ['HR','ADMIN']

@login_required
def factura_list(request):
    facturas = Factura.objects.all()
    return render(request, 'facturacion/factura_list.html', {'facturas': facturas})

@login_required
@user_passes_test(is_hr_or_admin)
def factura_create(request):
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        formset = FacturaItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            # Ensure at least one non-deleted item exists
            valid_items = [f for f in formset if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
            if not valid_items:
                form.add_error(None, 'Debes agregar al menos un item a la factura.')
            else:
                factura = form.save(commit=False)
                factura.subtotal = Decimal('0.00')
                factura.impuestos = Decimal('0.00')
                factura.total = Decimal('0.00')
                factura.save()
                total = Decimal('0.00')
                for item_form in formset:
                    if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                        item = item_form.save(commit=False)
                        item.factura = factura
                        item.save()
                        # item.importe is Decimal; sum using Decimal
                        total += (item.importe or Decimal('0.00'))
                factura.subtotal = total
                # Simple tax calculation (IVA 16%) using Decimal
                tax_rate = Decimal('0.16')
                factura.impuestos = (total * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                factura.total = (factura.subtotal + factura.impuestos).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                factura.save()
                messages.success(request, 'Factura creada correctamente.')
                return redirect('facturacion:factura_detail', factura.id)
    else:
        form = FacturaForm()
        formset = FacturaItemFormSet()
    return render(request, 'facturacion/factura_form.html', {'form': form, 'formset': formset})

@login_required
def factura_detail(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    return render(request, 'facturacion/factura_detail.html', {'factura': factura})

@login_required
def factura_pdf(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x_margin = 20*mm
    y = height - 20*mm

    # Force use of PNG logo only. Look for facturacion/logo.png in static files or STATIC_ROOT.
    logo_path = None
    try:
        logo_path = finders.find('facturacion/logo.png')
    except Exception:
        logo_path = None
    if not logo_path and settings.STATIC_ROOT:
        import os
        candidate = os.path.join(settings.STATIC_ROOT, 'facturacion', 'logo.png')
        if os.path.exists(candidate):
            logo_path = candidate

    image_drawn = False
    if logo_path:
        try:
            logo_w = 36 * mm
            logo_h = 36 * mm
            p.drawImage(logo_path, x_margin, height - logo_h - 12*mm, width=logo_w, height=logo_h, mask='auto')
            image_drawn = True
        except Exception:
            image_drawn = False

    # Header text
    p.setFont('Helvetica-Bold', 16)
    # place title to the right of logo
    p.drawString(x_margin + 42*mm, height - 24*mm, f"Factura: {factura.folio}")
    p.setFont('Helvetica', 10)
    p.drawString(x_margin + 42*mm, height - 32*mm, f"Fecha: {factura.fecha}")
    cliente_line = f"Cliente: {factura.cliente.nombre if factura.cliente else ''}  RFC: {factura.cliente.rfc or ''}"
    p.drawString(x_margin + 42*mm, height - 40*mm, cliente_line)
    y = height - 48*mm
    # If no image was drawn, render a simple shield-style logo using vector drawing
    if not image_drawn:
        try:
            # draw a simple shield using path
            shield_w = 36 * mm
            shield_h = 44 * mm
            cx = x_margin + shield_w/2
            top_y = height - 12*mm
            path = p.beginPath()
            path.moveTo(cx - shield_w/2, top_y - 10)
            path.lineTo(cx + shield_w/2, top_y - 10)
            path.lineTo(cx + shield_w/3, top_y - shield_h/2)
            path.lineTo(cx, top_y - shield_h)
            path.lineTo(cx - shield_w/3, top_y - shield_h/2)
            path.close()
            p.setFillColorRGB(0.17,0.19,0.22)
            p.setStrokeColorRGB(0.06,0.07,0.08)
            p.setLineWidth(1)
            p.drawPath(path, stroke=1, fill=1)
            # sword rectangle
            p.setFillColorRGB(0.75,0.78,0.8)
            p.rect(cx - 4, top_y - shield_h - 6, 8, 18, stroke=0, fill=1)
        except Exception:
            pass

    # Table headers
    p.setFont('Helvetica-Bold', 10)
    p.drawString(x_margin, y, 'Descripción')
    p.drawRightString(x_margin+120*mm, y, 'Cantidad')
    p.drawRightString(x_margin+145*mm, y, 'P.Unit')
    p.drawRightString(x_margin+180*mm, y, 'Importe')
    y -= 6*mm
    p.setFont('Helvetica', 10)

    for item in factura.items.all():
        p.drawString(x_margin, y, (item.descripcion or '')[:80])
        p.drawRightString(x_margin+120*mm, y, str(item.cantidad))
        p.drawRightString(x_margin+145*mm, y, f"{item.precio_unitario:.2f}")
        p.drawRightString(x_margin+180*mm, y, f"{item.importe:.2f}")
        y -= 6*mm
        if y < 40*mm:
            p.showPage()
            y = height - 30*mm

    y -= 8*mm
    # Totals box
    p.setFont('Helvetica-Bold', 11)
    p.drawRightString(x_margin+180*mm, y, f"Subtotal: {factura.subtotal:.2f}")
    y -= 6*mm
    p.drawRightString(x_margin+180*mm, y, f"Impuestos: {factura.impuestos:.2f}")
    y -= 6*mm
    p.setFont('Helvetica-Bold', 12)
    p.drawRightString(x_margin+180*mm, y, f"Total: {factura.total:.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


@login_required
@user_passes_test(is_hr_or_admin)
def cliente_list(request):
    clientes = Cliente.objects.all()
    return render(request, 'facturacion/cliente_list.html', {'clientes': clientes})


@login_required
@user_passes_test(is_hr_or_admin)
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, 'Cliente creado correctamente.')
            return redirect('facturacion:cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'facturacion/cliente_form.html', {'form': form})


@login_required
@user_passes_test(is_hr_or_admin)
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('facturacion:cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'facturacion/cliente_form.html', {'form': form, 'cliente': cliente})


@login_required
@user_passes_test(is_hr_or_admin)
def reportes_mes(request):
    """Reporte general por mes: suma totales e lista facturas del mes seleccionado."""
    # Parámetros
    year = request.GET.get('year')
    month = request.GET.get('month')
    cliente_id = request.GET.get('cliente_id')
    estado = request.GET.get('estado')

    today = date.today()
    if not year:
        year = today.year
    else:
        try:
            year = int(year)
        except ValueError:
            year = today.year
    if not month:
        month = today.month
    else:
        try:
            month = int(month)
        except ValueError:
            month = today.month

    qs = Factura.objects.filter(fecha__year=year, fecha__month=month).select_related('cliente')
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    if estado:
        qs = qs.filter(estado=estado)
    totals = qs.aggregate(total_monto=Sum('total'), total_impuestos=Sum('impuestos'), subtotal=Sum('subtotal'))

    clientes = Cliente.objects.all()

    # Pagination
    per_page = 25
    ordered_qs = qs.order_by('fecha', 'folio')
    paginator = Paginator(ordered_qs, per_page)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Build base querystring without page param for pagination links and exports
    base_qs = request.GET.copy()
    if 'page' in base_qs:
        base_qs.pop('page')
    base_qs = base_qs.urlencode()

    context = {
        'facturas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'totals': totals,
        'year': year,
        'month': month,
        'clientes': clientes,
        'selected_cliente': cliente_id,
        'selected_estado': estado,
        'base_qs': base_qs,
        'has_openpyxl': _HAS_OPENPYXL,
    }
    return render(request, 'facturacion/reporte_mes.html', context)


@login_required
@user_passes_test(is_hr_or_admin)
def export_facturas_csv(request):
    """Exporta a CSV las facturas filtradas (year+month+cliente_id opcionales)."""
    year = request.GET.get('year')
    month = request.GET.get('month')
    cliente_id = request.GET.get('cliente_id')
    estado = request.GET.get('estado')

    qs = Factura.objects.all().select_related('cliente')
    if year:
        try:
            qs = qs.filter(fecha__year=int(year))
        except ValueError:
            pass
    if month:
        try:
            qs = qs.filter(fecha__month=int(month))
        except ValueError:
            pass
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    if estado:
        qs = qs.filter(estado=estado)

    # Build CSV
    response = HttpResponse(content_type='text/csv')
    filename = f"facturas_{year or 'all'}_{month or 'all'}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(['Folio', 'Fecha', 'Cliente', 'Subtotal', 'Impuestos', 'Total', 'Estado'])
    for f in qs.order_by('fecha', 'folio'):
        writer.writerow([
            f.folio,
            f.fecha.strftime('%Y-%m-%d'),
            f.cliente.nombre if f.cliente else '',
            f.subtotal,
            f.impuestos,
            f.total,
            getattr(f, 'estado', '')
        ])
    return response


@login_required
@user_passes_test(is_hr_or_admin)
def export_facturas_xls(request):
    """Exporta las facturas filtradas a XLSX usando openpyxl si está instalado."""
    if not _HAS_OPENPYXL:
        return HttpResponse('openpyxl no está instalado en el servidor. Instálalo para habilitar la exportación XLSX.', status=500)

    year = request.GET.get('year')
    month = request.GET.get('month')
    cliente_id = request.GET.get('cliente_id')
    estado = request.GET.get('estado')

    qs = Factura.objects.all().select_related('cliente')
    if year:
        try:
            qs = qs.filter(fecha__year=int(year))
        except ValueError:
            pass
    if month:
        try:
            qs = qs.filter(fecha__month=int(month))
        except ValueError:
            pass
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    if estado:
        qs = qs.filter(estado=estado)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Facturas'
    headers = ['Folio', 'Fecha', 'Cliente', 'Subtotal', 'Impuestos', 'Total', 'Estado']
    ws.append(headers)
    for f in qs.order_by('fecha', 'folio'):
        ws.append([
            f.folio,
            f.fecha.strftime('%Y-%m-%d'),
            f.cliente.nombre if f.cliente else '',
            float(f.subtotal or 0),
            float(f.impuestos or 0),
            float(f.total or 0),
            getattr(f, 'estado', '')
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"facturas_{year or 'all'}_{month or 'all'}.xlsx"
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
