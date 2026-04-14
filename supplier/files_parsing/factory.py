from .parsers.belgrano import BelgranoParser
from .parsers.bellini import BelliniParser
from .parsers.fluorgaz import FluorgazParser
from .parsers.imi import ImiParser
from .parsers.nueva_hera import NuevaHeraParser
from .parsers.reld import ReldParser
from .parsers.uriarte import UriarteParser
from .parsers.distribudora_jc import JcParser
from .parsers.casa_jarse import CasaJarseParser
from .parsers.favale import FavaleParser


PARSERS = {
    "belgrano": BelgranoParser,
    "bellini": BelliniParser,
    "fluorgaz": FluorgazParser,
    "favale": FavaleParser,
    "imi": ImiParser,
    "importadora_nueva_hera": NuevaHeraParser,
    "reld": ReldParser,
    "uriarte": UriarteParser,
    "distribuidora_jc": JcParser,
    "casa_jarse": CasaJarseParser
}


def get_parser(supplier):
    key = supplier.name.lower().strip().replace(" ", "_")

    parser_class = PARSERS.get(key)

    if not parser_class:
        
        try:
            parser_class = PARSERS.get(key.lower())
        except ValueError:
            print(f"Нет парсера для поставщика: {key}")
            

    return parser_class()