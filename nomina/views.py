from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import SalarioBase, PeriodoNomina, ReciboPago, Percepcion, Deduccion
from polls.models import Trabajador

LINE_HEIGHT = 18

@login_required
def periodo_list(request):
    periodos = PeriodoNomina.objects.all()

    estado = request.GET.get('estado', 'abierto')
    tipo = request.GET.get('tipo', '')
    buscar = request.GET.get('buscar', '')

    if estado == 'abierto':
        periodos = periodos.filter(cerrado=False)
    elif estado == 'cerrado':
        periodos = periodos.filter(cerrado=True)

    if tipo:
        periodos = periodos.filter(tipo_periodo=tipo)

    if buscar:
        periodos = periodos.filter(descripcion__icontains=buscar)

    return render(request, 'nomina/periodo_list.html', {
        'periodos': periodos,
        'filtros': {
            'estado': estado,
            'tipo': tipo,
            'buscar': buscar,
        }
    })

@login_required
def periodo_create(request):
    if request.method == 'POST':
        tipo_periodo = request.POST.get('tipo_periodo')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        descripcion = request.POST.get('descripcion', '')

        try:
            PeriodoNomina.objects.create(
                tipo_periodo=tipo_periodo,
                fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date(),
                fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date(),
                descripcion=descripcion
            )
            messages.success(request, 'Período creado exitosamente.')
            return redirect('nomina:periodo_list')
        except Exception as e:
            messages.error(request, f'Error al crear período: {str(e)}')

    return render(request, 'nomina/periodo_create.html')

def trabajador_tiene_salario(trabajador):
    try:
        return hasattr(trabajador, 'salario_base') and trabajador.salario_base is not None
    except SalarioBase.DoesNotExist:
        return False

@login_required
def periodo_detail(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    recibos = periodo.recibos.all()

    trabajadores_sin_recibo = []
    for trabajador in Trabajador.objects.filter(estado='Activo').exclude(recibos__periodo=periodo):
        trabajadores_sin_recibo.append({
            'trabajador': trabajador,
            'tiene_salario': trabajador_tiene_salario(trabajador),
        })

    return render(request, 'nomina/periodo_detail.html', {
        'periodo': periodo,
        'recibos': recibos,
        'trabajadores_sin_recibo': trabajadores_sin_recibo,
    })

@login_required
def recibo_detail(request, pk):
    recibo = get_object_or_404(ReciboPago, pk=pk)
    impuestos = recibo.total_impuestos()

    return render(request, 'nomina/recibo_detail.html', {
        'recibo': recibo,
        'salario_dias': recibo.salario_por_dias(),
        'horas_extras': recibo.horas_extras_monto(),
        'retardos': recibo.retardos_monto(),
        'impuestos': impuestos,
    })

def guardar_salario(trabajador, salario_diario):
    if not salario_diario:
        return

    try:
        salario_decimal = Decimal(salario_diario)
    except (InvalidOperation, TypeError, ValueError):
        return

    try:
        salario_obj = trabajador.salario_base
        salario_obj.salario_diario = salario_decimal
        salario_obj.save()
    except SalarioBase.DoesNotExist:
        SalarioBase.objects.create(trabajador=trabajador, salario_diario=salario_decimal)


def parse_decimal(value, default=Decimal('0.00')):
    if value in (None, ''):
        return default
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return default


def parse_int(value, default=0):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

@login_required
def crear_recibo(request, periodo_id, trabajador_id):
    periodo = get_object_or_404(PeriodoNomina, pk=periodo_id)
    trabajador = get_object_or_404(Trabajador, pk=trabajador_id)

    if ReciboPago.objects.filter(trabajador=trabajador, periodo=periodo).exists():
        messages.error(request, 'Ya existe un recibo para este trabajador en este período.')
        return redirect('nomina:periodo_detail', pk=periodo_id)

    tiene_salario = trabajador_tiene_salario(trabajador)

    if request.method == 'POST':
        salario_diario = request.POST.get('salario_diario')
        if salario_diario:
            guardar_salario(trabajador, salario_diario)
            tiene_salario = True

        horas_por_turno = parse_decimal(request.POST.get('horas_por_turno', '0'))
        dias_trabajados = parse_decimal(request.POST.get('dias_trabajados', '0'))
        horas_extras = parse_decimal(request.POST.get('horas_extras', '0'))
        retardos = parse_int(request.POST.get('retardos', '0'))

        with transaction.atomic():
            recibo = ReciboPago.objects.create(
                trabajador=trabajador,
                periodo=periodo,
                puesto=request.POST.get('puesto', ''),
                lugar_servicio=request.POST.get('lugar_servicio', ''),
                horario_turno=request.POST.get('horario_turno', ''),
                horas_por_turno=horas_por_turno,
                dias_trabajados=dias_trabajados,
                horas_extras=horas_extras,
                retardos=retardos,
            )

            tipos_percepcion = request.POST.getlist('tipo_percepcion[]')
            desc_percepcion = request.POST.getlist('descripcion_percepcion[]')
            monto_percepcion = request.POST.getlist('monto_percepcion[]')

            for i in range(len(tipos_percepcion)):
                if tipos_percepcion[i] and monto_percepcion[i]:
                    monto = parse_decimal(monto_percepcion[i])
                    Percepcion.objects.create(
                        recibo=recibo,
                        tipo=tipos_percepcion[i],
                        descripcion=desc_percepcion[i] or tipos_percepcion[i],
                        monto=monto
                    )

            tipos_deduccion = request.POST.getlist('tipo_deduccion[]')
            desc_deduccion = request.POST.getlist('descripcion_deduccion[]')
            monto_deduccion = request.POST.getlist('monto_deduccion[]')

            for i in range(len(tipos_deduccion)):
                if tipos_deduccion[i] and monto_deduccion[i]:
                    monto = parse_decimal(monto_deduccion[i])
                    Deduccion.objects.create(
                        recibo=recibo,
                        tipo=tipos_deduccion[i],
                        descripcion=desc_deduccion[i] or tipos_deduccion[i],
                        monto=monto
                    )

            recibo.save()

            messages.success(request, 'Recibo creado exitosamente.')
            return redirect('nomina:recibo_detail', pk=recibo.pk)

    return render(request, 'nomina/crear_recibo.html', {
        'periodo': periodo,
        'trabajador': trabajador,
        'tiene_salario': tiene_salario,
    })

@login_required
def salario_list(request):
    salarios = SalarioBase.objects.filter(activo=True).select_related('trabajador')
    trabajadores_sin_salario = Trabajador.objects.filter(estado='Activo').exclude(salario_base__isnull=False)
    return render(request, 'nomina/salario_list.html', {
        'salarios': salarios,
        'trabajadores_sin_salario': trabajadores_sin_salario,
    })

@login_required
def salario_edit(request, pk):
    salario = get_object_or_404(SalarioBase, pk=pk)
    return salario_create(request, trabajador_id=salario.trabajador.pk)

@login_required
def salario_create(request, trabajador_id=None):
    trabajador = None
    salario = None
    if trabajador_id:
        trabajador = get_object_or_404(Trabajador, pk=trabajador_id)
        try:
            salario = trabajador.salario_base
        except SalarioBase.DoesNotExist:
            salario = None

    if request.method == 'POST':
        trabajador_id = request.POST.get('trabajador')
        salario_diario = request.POST.get('salario_diario')

        try:
            trabajador = get_object_or_404(Trabajador, pk=trabajador_id)
            salario_decimal = None
            try:
                salario_decimal = Decimal(salario_diario)
            except (InvalidOperation, TypeError, ValueError):
                messages.error(request, 'El salario ingresado no es válido.')

            if salario_decimal is not None:
                if hasattr(trabajador, 'salario_base'):
                    salario_obj = trabajador.salario_base
                    salario_obj.salario_diario = salario_decimal
                    salario_obj.save()
                else:
                    SalarioBase.objects.create(trabajador=trabajador, salario_diario=salario_decimal)
                messages.success(request, f'Salario asignado a {trabajador.nombre} exitosamente.')
                return redirect('nomina:salario_list')
        except Exception as e:
            messages.error(request, f'Error al asignar salario: {str(e)}')

    trabajadores = Trabajador.objects.filter(estado='Activo')
    return render(request, 'nomina/salario_create.html', {
        'trabajador': trabajador,
        'trabajadores': trabajadores,
        'salario': salario,
    })

@login_required
def descargar_recibo_pdf(request, pk):
    recibo = get_object_or_404(ReciboPago, pk=pk)
    impuestos = recibo.total_impuestos()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{recibo.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 40

    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(40, y, 'Recibo de Pago')
    y -= 30

    pdf.setFont('Helvetica', 10)
    pdf.drawString(40, y, f'Trabajador: {recibo.trabajador.nombre} {recibo.trabajador.apellido}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Período: {recibo.periodo}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Puesto: {recibo.puesto or "-"}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Lugar de servicio: {recibo.lugar_servicio or "-"}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Horario turno: {recibo.horario_turno or "-"}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Horas por turno: {recibo.horas_por_turno}')
    y -= LINE_HEIGHT * 2

    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(40, y, 'Percepciones')
    y -= LINE_HEIGHT
    pdf.setFont('Helvetica', 10)
    pdf.drawString(40, y, f'Salario por días trabajados: ${recibo.salario_por_dias():.2f}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Horas extras: ${recibo.horas_extras_monto():.2f}')
    y -= LINE_HEIGHT
    for percepcion in recibo.percepciones.all():
        pdf.drawString(40, y, f'{percepcion.descripcion}: ${percepcion.monto:.2f}')
        y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Total percepciones: ${recibo.total_percepciones:.2f}')
    y -= LINE_HEIGHT * 2

    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(40, y, 'Deducciones')
    y -= LINE_HEIGHT
    pdf.setFont('Helvetica', 10)
    pdf.drawString(40, y, f'Retardos: ${recibo.retardos_monto():.2f}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'ISR: ${impuestos["isr"]:.2f}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'IMSS: ${impuestos["imss"]:.2f}')
    y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Pensión: ${impuestos["pension"]:.2f}')
    y -= LINE_HEIGHT
    for deduccion in recibo.deducciones.all():
        pdf.drawString(40, y, f'{deduccion.descripcion}: ${deduccion.monto:.2f}')
        y -= LINE_HEIGHT
    pdf.drawString(40, y, f'Total deducciones: ${recibo.total_deducciones:.2f}')
    y -= LINE_HEIGHT * 2

    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(40, y, f'Neto a pagar: ${recibo.neto_pagar:.2f}')
    y -= LINE_HEIGHT

    if recibo.notas:
        y -= LINE_HEIGHT
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(40, y, 'Notas')
        y -= LINE_HEIGHT
        pdf.setFont('Helvetica', 10)
        pdf.drawString(40, y, recibo.notas)

    pdf.showPage()
    pdf.save()
    return response
