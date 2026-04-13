from django.core.management.base import BaseCommand
from categories.models import Category


class Command(BaseCommand):
    help = 'Cria as categorias padrão (globais) para receitas e despesas.'

    def handle(self, *args, **options):
        # Categorias de Receita
        income_categories = [
            {'name': 'Salário', 'color': '#10B981'},
            {'name': 'Freelance', 'color': '#3B82F6'},
            {'name': 'Investimentos', 'color': '#8B5CF6'},
            {'name': 'Outros', 'color': '#64748B'},
        ]

        for cat_data in income_categories:
            category, created = Category.objects.get_or_create(
                user=None,
                name=cat_data['name'],
                type=Category.CategoryType.INCOME,
                defaults={'color': cat_data['color']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoria "{category.name}" (Receita) criada.'))
            else:
                self.stdout.write(self.style.WARNING(f'Categoria "{category.name}" (Receita) já existe.'))

        # Categorias de Despesa
        expense_categories = [
            {'name': 'Alimentação', 'color': '#EF4444'},
            {'name': 'Transporte', 'color': '#F59E0B'},
            {'name': 'Saúde', 'color': '#EC4899'},
            {'name': 'Educação', 'color': '#6366F1'},
            {'name': 'Lazer', 'color': '#F43F5E'},
            {'name': 'Moradia', 'color': '#8B5CF6'},
            {'name': 'Outros', 'color': '#64748B'},
        ]

        for cat_data in expense_categories:
            category, created = Category.objects.get_or_create(
                user=None,
                name=cat_data['name'],
                type=Category.CategoryType.EXPENSE,
                defaults={'color': cat_data['color']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoria "{category.name}" (Despesa) criada.'))
            else:
                self.stdout.write(self.style.WARNING(f'Categoria "{category.name}" (Despesa) já existe.'))

        self.stdout.write(self.style.SUCCESS('Seed de categorias finalizado.'))
