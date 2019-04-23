import os
import logging
import click
import configparser


from models import Extdevice, IPBXBinder
from alkivi.logger import Logger

# Define the global logger
logger = Logger(min_log_level_to_mail=None,
                min_log_level_to_save=logging.DEBUG,
                min_log_level_to_print=logging.DEBUG,
                emails=['monitoring@alkivi.fr'])


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))


@click.command()
@click.option('--debug', default=False, is_flag=True,
              help='Toggle Debug mode')
def check_phones_codec(debug):
    """Check order of phones codec."""
    if debug:
        logger.set_min_level_to_print(logging.DEBUG)
        logger.set_min_level_to_save(logging.DEBUG)

    config_file = os.path.join(ROOT_DIR, '.config')
    logger.info(config_file)
    config = configparser.RawConfigParser()
    config.read(config_file)

    # 3CX
    db = config.get('3cx', 'database')
    dbuser = config.get('3cx', 'user')
    dbpass = config.get('3cx', 'password')

    # Do your code here
    logger.info("Program Start")

    # Load object
    ipbx_client = IPBXBinder(db, dbuser, dbpass)

    # Query
    session = ipbx_client.get_session()
    ipbx_extdevices = session.query(Extdevice).all()
    logger.debug('test', ipbx_extdevices)


if __name__ == "__main__":
    try:
        check_phones_codec()
    except Exception as exception:
        logger.exception(exception)
