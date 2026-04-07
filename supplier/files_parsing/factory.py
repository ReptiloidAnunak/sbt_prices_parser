from .parsers.belgrano import BelgranoParser
from .parsers.bellini import BelliniParser
from .parsers.fluorgaz import FluorgazParser
# from .parsers.imi import ImiParser
from .parsers.nueva_hera import NuevaHeraParser
from .parsers.reld import ReldParser
from .parsers.uriarte import UriarteParser
from .parsers.distribudora_jc import JcParser
from .parsers.casa_jarse import CasaJarseParser


PARSERS = {
    "belgrano": BelgranoParser,
    "bellini": BelliniParser,
    "fluorgaz": FluorgazParser,
    # "imi": ImiParser,
    "nueva_hera": NuevaHeraParser,
    "reld": ReldParser,
    "uriarte": UriarteParser,
    "distribuidora jc": JcParser,
    "casa_jarse": CasaJarseParser
}


def get_parser(supplier):
    key = supplier.name.lower().strip().replace(" ", "_")

    parser_class = PARSERS.get(key)

    if not parser_class:
        raise ValueError(f"Нет парсера для поставщика: {supplier.name}\nКлюч: {key}")

    return parser_class()