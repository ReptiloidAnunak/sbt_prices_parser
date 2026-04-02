from celery import shared_task
from supplier.models import Supplier
from product.models import ProductSupplier
from supplier.files_parsing.factory import get_parser


@shared_task
def process_price_list(supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    file_path = supplier.price_list.path
    parser = get_parser(supplier)
    data = parser.parse(file_path)
    print(f"Обработано {len(data)} строк")
    print('-----------')
    print(data)
    for prod in data:
        prod_supplier = ProductSupplier.objects.filter(supplier_prod_code= prod['code']).first()
        if prod_supplier:
            prod_supplier.supplier_prod_title = prod['title']
            prod_supplier.price_wholesale = prod['price']
            prod_supplier.save()