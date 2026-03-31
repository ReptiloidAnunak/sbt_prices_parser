from celery import shared_task
from supplier.models import Supplier
from supplier.files_parsing.factory import get_parser


@shared_task
def process_price_list(supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)

    file_path = supplier.price_list.path
    

    parser = get_parser(supplier)
    data = parser.parse(file_path)

    print(f"Обработано {len(data)} строк")
    print(data)