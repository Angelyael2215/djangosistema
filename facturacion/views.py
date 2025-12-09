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
    y = height - 30*mm

    p.setFont('Helvetica-Bold', 14)
    p.drawString(x_margin, y, f"Factura: {factura.folio}")
    p.setFont('Helvetica', 10)
    y -= 8*mm
    p.drawString(x_margin, y, f"Fecha: {factura.fecha}")
    y -= 6*mm
    p.drawString(x_margin, y, f"Cliente: {factura.cliente.nombre}  RFC: {factura.cliente.rfc or ''}")
    y -= 10*mm

    # Table headers
    p.setFont('Helvetica-Bold', 10)
    p.drawString(x_margin, y, 'Descripción')
    p.drawString(x_margin+90*mm, y, 'Cantidad')
    p.drawString(x_margin+110*mm, y, 'P.Unit')
    p.drawString(x_margin+140*mm, y, 'Importe')
    y -= 6*mm
    p.setFont('Helvetica', 10)

    for item in factura.items.all():
        p.drawString(x_margin, y, item.descripcion[:60])
        p.drawRightString(x_margin+120*mm, y, str(item.cantidad))
        p.drawRightString(x_margin+140*mm, y, f"{item.precio_unitario:.2f}")
        p.drawRightString(x_margin+180*mm, y, f"{item.importe:.2f}")
        y -= 6*mm
        if y < 40*mm:
            p.showPage()
            y = height - 30*mm

    y -= 8*mm
    p.drawRightString(x_margin+180*mm, y, f"Subtotal: {factura.subtotal:.2f}")
    y -= 6*mm
    p.drawRightString(x_margin+180*mm, y, f"Impuestos: {factura.impuestos:.2f}")
    y -= 6*mm
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
