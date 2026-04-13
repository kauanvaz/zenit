import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Sum, Q
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from categories.models import Category
from .models import Transaction
from .forms import TransactionForm


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)

        # Filtros baseados em GET
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        transaction_type = self.request.GET.get('type')
        category_id = self.request.GET.get('category')

        if year:
            queryset = queryset.filter(date__year=year)

        if month:
            queryset = queryset.filter(date__month=month)

        if transaction_type:
            queryset = queryset.filter(type=transaction_type)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Totais para o período filtrado
        totals = queryset.aggregate(
            total_income=Sum('amount', filter=Q(type=Transaction.TransactionType.INCOME)),
            total_expense=Sum('amount', filter=Q(type=Transaction.TransactionType.EXPENSE))
        )

        income = totals.get('total_income') or 0
        expense = totals.get('total_expense') or 0
        net_balance = income - expense

        context['income_total'] = income
        context['expense_total'] = expense
        context['net_balance'] = net_balance

        # Dados para os filtros no template
        context['categories'] = Category.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        )
        context['transaction_types'] = Transaction.TransactionType.choices

        # Listagem de anos para o filtro
        current_year = timezone.now().year
        years = set(range(current_year - 4, current_year + 1))
        user_years = Transaction.objects.filter(user=self.request.user).dates('date', 'year')
        years.update(d.year for d in user_years)
        context['years'] = sorted(years, reverse=True)

        # Listagem de meses
        context['months'] = [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ]

        # Manter filtros nos links de paginação
        get_params = self.request.GET.copy()
        if 'page' in get_params:
            del get_params['page']
        context['filter_params'] = get_params.urlencode()

        return context


class TransactionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('transactions:list')
    success_message = 'Transação criada com sucesso.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('transactions:list')
    success_message = 'Transação atualizada com sucesso.'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'transactions/confirm_delete.html'
    success_url = reverse_lazy('transactions:list')

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Transação excluída com sucesso.')
        return super().form_valid(form)


def _get_filtered_queryset(request):
    """Return a user-scoped, filtered queryset using the same params as TransactionListView."""
    queryset = (
        Transaction.objects
        .filter(user=request.user)
        .select_related('account', 'category')
        .order_by('-date', '-created_at')
    )

    month = request.GET.get('month')
    year = request.GET.get('year')
    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')

    if year:
        queryset = queryset.filter(date__year=year)

    if month:
        queryset = queryset.filter(date__month=month)

    if transaction_type:
        queryset = queryset.filter(type=transaction_type)

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    return queryset


def _format_amount(amount):
    """Format a Decimal/float as Brazilian currency string (e.g. 1.234,56)."""
    return f'{amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _build_filter_description(request):
    """Return a human-readable string describing the active filters."""
    parts = []

    month_names = {
        '1': 'Janeiro', '2': 'Fevereiro', '3': 'Março', '4': 'Abril',
        '5': 'Maio', '6': 'Junho', '7': 'Julho', '8': 'Agosto',
        '9': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro',
    }

    year = request.GET.get('year')
    month = request.GET.get('month')
    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')

    if month and year:
        parts.append(f'{month_names.get(month, month)}/{year}')
    elif month:
        parts.append(f'{month_names.get(month, month)} (todos os anos)')
    elif year:
        parts.append(f'Ano {year}')
    else:
        parts.append('Todos os anos')

    if transaction_type == Transaction.TransactionType.INCOME:
        parts.append('Receitas')
    elif transaction_type == Transaction.TransactionType.EXPENSE:
        parts.append('Despesas')

    if category_id:
        try:
            cat = Category.objects.get(
                pk=category_id,
                **({'user': request.user} if request.user else {}),
            )
            parts.append(f'Categoria: {cat.name}')
        except Category.DoesNotExist:
            pass

    return ' | '.join(parts)


class TransactionExportCSVView(LoginRequiredMixin, View):
    """Export filtered transactions as a CSV file download."""

    def get(self, request, *args, **kwargs):
        queryset = _get_filtered_queryset(request)

        filename = f'transacoes_{date.today().isoformat()}.csv'
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Data', 'Descrição', 'Tipo', 'Categoria', 'Conta', 'Valor'])

        for transaction in queryset:
            type_display = (
                'Receita'
                if transaction.type == Transaction.TransactionType.INCOME
                else 'Despesa'
            )
            category_name = transaction.category.name if transaction.category else ''
            sign = '+' if transaction.type == Transaction.TransactionType.INCOME else '-'
            amount_str = f'{sign}{_format_amount(transaction.amount)}'

            writer.writerow([
                transaction.date.strftime('%d/%m/%Y'),
                transaction.description,
                type_display,
                category_name,
                transaction.account.name,
                amount_str,
            ])

        return response


class TransactionExportPDFView(LoginRequiredMixin, View):
    """Export filtered transactions as a PDF file download."""

    _COLOR_INCOME = colors.HexColor('#10b981')
    _COLOR_EXPENSE = colors.HexColor('#ef4444')
    _COLOR_HEADER_BG = colors.HexColor('#1e293b')
    _COLOR_TOTAL_BG = colors.HexColor('#f1f5f9')
    _COLOR_WHITE = colors.white
    _COLOR_DARK = colors.HexColor('#1e293b')

    def get(self, request, *args, **kwargs):
        queryset = _get_filtered_queryset(request)

        filename = f'transacoes_{date.today().isoformat()}.pdf'
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        doc = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Title'],
            fontSize=16,
            textColor=self._COLOR_DARK,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=12,
        )

        elements = []
        elements.append(Paragraph('Relatório de Transações', title_style))

        filter_desc = _build_filter_description(request)
        elements.append(Paragraph(filter_desc, subtitle_style))
        elements.append(Spacer(1, 0.3 * cm))

        # Table header
        col_headers = ['Data', 'Descrição', 'Tipo', 'Categoria', 'Conta', 'Valor']
        table_data = [col_headers]

        income_total = 0
        expense_total = 0

        for transaction in queryset:
            is_income = transaction.type == Transaction.TransactionType.INCOME
            type_display = 'Receita' if is_income else 'Despesa'
            category_name = transaction.category.name if transaction.category else ''
            sign = '+' if is_income else '-'
            amount_str = f'{sign}{_format_amount(transaction.amount)}'

            if is_income:
                income_total += transaction.amount
            else:
                expense_total += transaction.amount

            table_data.append([
                transaction.date.strftime('%d/%m/%Y'),
                transaction.description,
                type_display,
                category_name,
                transaction.account.name,
                amount_str,
            ])

        # Totals row
        net_balance = income_total - expense_total
        net_sign = '+' if net_balance >= 0 else ''
        table_data.append([
            '',
            '',
            '',
            '',
            'Saldo líquido:',
            f'{net_sign}{_format_amount(net_balance)}',
        ])
        totals_row_idx = len(table_data) - 1

        # Column widths for landscape A4 (usable ~25.7 cm)
        col_widths = [2.5 * cm, 8 * cm, 2.5 * cm, 3.5 * cm, 4.5 * cm, 3 * cm]

        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Build per-row text colours for income/expense
        row_text_commands = []
        for row_idx, transaction in enumerate(queryset, start=1):
            is_income = transaction.type == Transaction.TransactionType.INCOME
            text_color = self._COLOR_INCOME if is_income else self._COLOR_EXPENSE
            row_text_commands.append(
                ('TEXTCOLOR', (0, row_idx), (-1, row_idx), text_color)
            )

        table_style_commands = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self._COLOR_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self._COLOR_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            # Data rows
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ALIGN', (0, 1), (-1, -2), 'LEFT'),
            ('ALIGN', (5, 1), (5, -2), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 4),
            ('TOPPADDING', (0, 1), (-1, -2), 4),
            # Totals row
            ('BACKGROUND', (0, totals_row_idx), (-1, totals_row_idx), self._COLOR_TOTAL_BG),
            ('FONTNAME', (0, totals_row_idx), (-1, totals_row_idx), 'Helvetica-Bold'),
            ('FONTSIZE', (0, totals_row_idx), (-1, totals_row_idx), 9),
            ('ALIGN', (4, totals_row_idx), (5, totals_row_idx), 'RIGHT'),
            ('TEXTCOLOR', (0, totals_row_idx), (-1, totals_row_idx), self._COLOR_DARK),
            ('TOPPADDING', (0, totals_row_idx), (-1, totals_row_idx), 6),
            ('BOTTOMPADDING', (0, totals_row_idx), (-1, totals_row_idx), 6),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self._COLOR_HEADER_BG),
        ]

        table_style_commands.extend(row_text_commands)
        table.setStyle(TableStyle(table_style_commands))
        elements.append(table)

        doc.build(elements)
        return response
