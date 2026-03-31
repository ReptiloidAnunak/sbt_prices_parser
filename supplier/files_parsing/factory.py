from .parsers.belgrano import BelgranoParser
from .parsers.bellini import BelliniParser
from .parsers.fluorgaz import FluorgazParser
# from .parsers.imi import ImiParser
from .parsers.nueva_hera import NuevaHeraParser
from .parsers.reld import ReldParser
from .parsers.uriarte import UriarteParser


PARSERS = {
    "belgrano": BelgranoParser,
    "bellini": BelliniParser,
    "fluorgaz": FluorgazParser,
    # "imi": ImiParser,
    "nueva_hera": NuevaHeraParser,
    "reld": ReldParser,
    "uriarte": UriarteParser,
}


def get_parser(supplier):
    key = supplier.name.lower().strip()

    parser_class = PARSERS.get(key)

    if not parser_class:
        raise ValueError(f"Нет парсера для поставщика: {supplier.name}")

    return parser_class()