from web_parsers_app.parsers.ansal import run as ansal_run


PARSER_NAME = "ansal_retail"


def run():
    return ansal_run(retail=True)


if __name__ == "__main__":
    run()