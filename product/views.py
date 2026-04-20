
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO

from product.models import Product, ProductSupplier
from supplier.models import Supplier
import pandas as pd
from datetime import datetime
import logging
from django.core.files.base import ContentFile


logger = logging.getLogger(__name__)


@csrf_exempt
def import_products(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    # --- Парсим JSON ---
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    supplier_name = data.get('supplier')
    products_json_lst = data.get('products', [])
    

    df = pd.DataFrame(products_json_lst)
    filename = f"{supplier_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    logger.info(f"FILE CREATED: {filename}")
    print('\n\n')


    

    if not supplier_name:
        return JsonResponse({'error': 'supplier is required'}, status=400)

    supplier, _ = Supplier.objects.get_or_create(name=supplier_name)

    updated = 0
    not_found = 0

    for item in products_json_lst:
        code = item.get('code')
        title = item.get('title')
        price = item.get('price')

        if not code:
            continue
        product_price_obj = ProductSupplier.objects.filter(supplier_prod_code=code).first()

        if not product_price_obj:
            not_found += 1
            logger.warning(f"Not found {title}")
            continue
        else:
            updated += 1
            logger.info(f"Found: {product_price_obj.product.title_sbt} == {title}")
            product_price_obj.price_wholesale = price
            product_price_obj.supplier_prod_title = title
            product_price_obj.save()
            logger.info(f'Updated: {product_price_obj.product.title_sbt}')

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    # имя файла
    filename = f"products_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

    # сохраняем в модель
    supplier.price_list.save(
        filename,
        ContentFile(buffer.read()),
        save=True
    )
            

    return JsonResponse({
        'status': 'ok',
        'supplier': supplier_name,
        'updated': updated,
        'not_found': not_found,
        'total': len(products_json_lst)
    })