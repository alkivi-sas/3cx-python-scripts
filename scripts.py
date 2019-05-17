import os
import logging
import click
import configparser
import xml.etree.ElementTree as ET 


from models import Extdevice, IPBXBinder, Users
from alkivi.logger import Logger

# Define the global logger
logger = Logger(min_log_level_to_mail=logging.WARNING,
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

    logger.new_loop_logger()
    for device in ipbx_extdevices:
        prefix = 'Extension {0}'.format(device.fkidextension)
        logger.new_iteration(prefix=prefix)
        logger.debug('Getting user')
        user = session.query(Users).filter(Users.fkidextension == device.fkidextension).first()
        prefix = '{0} {1}'.format(user.firstname, user.lastname)
        logger.set_prefix(prefix)
        phone_type = device.filename2
        logger.info('Phone is {0}'.format(phone_type))
        data = device.pv_settings
        tree = ET.fromstring(data)
        codecs = {}
        for codec in tree.iter('Codec'):
            name = codec.attrib['DisplayText']
            priority = codec.attrib['Priority']
            codecs[priority] = name
        test_codecs = []
        for key in sorted(codecs.keys()):
                test_codecs.append(codecs[key])
        wanted_codecs = None
        if phone_type.startswith('Yealink'):
            wanted_codecs = ['PCMA', 'G729', 'PCMU', 'G722']
        elif phone_type.startswith('Snom'):
            wanted_codecs = ['G711a', 'G729', 'G711u', 'G722']
        elif phone_type.startswith('Polycom'):
            wanted_codecs = ['PCMA', 'G729A/B', 'PCMU', 'G722']

        if not wanted_codecs:
            logger.warning('Weird phone', test_codecs)
            continue

        index = 0
        for codec in test_codecs:
            if len(wanted_codecs) < index:
                break
            if codec != wanted_codecs[index]:
                logger.warning('error in codec order', test_codecs)
                break
            index += 1
    logger.del_loop_logger()



if __name__ == "__main__":
    try:
        check_phones_codec()
    except Exception as exception:
        logger.exception(exception)
