#!/usr/bin/env python
# coding: utf8

import os
import logging
import socket
import click
import configparser
import xml.etree.ElementTree as ET


from models import Extdevice, IPBXBinder, Users, Parameter, Codec, Codec2Gateway, Gateway, DnProp
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
def check_3cx_data(debug):
    """
    Check various settings in 3CX.

    Codec order in phones
    Codec order in gateway (trunk)
    Parameter
    """
    if debug:
        logger.set_min_level_to_print(logging.DEBUG)
        logger.set_min_level_to_save(logging.DEBUG)
        logger.set_min_level_to_mail(None)

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

    # Session for query
    session = ipbx_client.get_session()

    # Errors aggregation
    errors = []

    # DnProp (Soft phones)
    dnprops = session.query(DnProp).filter(DnProp.name == 'MYPHONETEMPLATEINFO').all()
    wanted_codecs = ['PCMA', 'G729', 'PCMU']
    logger.new_loop_logger()
    for dnprop in dnprops:
        logger.new_iteration(prefix=dnprop.iddnprop)
        user = session.query(Users).filter(Users.fkidextension == dnprop.fkiddn).first()
        if not user:
            continue
        prefix = 'Softphone {0} {1}'.format(user.firstname, user.lastname)
        logger.set_prefix(prefix)
        data = dnprop.value
        tree = ET.fromstring(data)
        test_codecs = []
        for codec in tree.iter('Codec'):
            test_codecs.append(codec.text)

        if len(wanted_codecs) != len(test_codecs):
            should_be = ' '.join(wanted_codecs)
            actually_is = ' '.join(test_codecs)
            error = 'Softphone {0} {1} : '.format(user.firstname, user.lastname) +\
                    'error in codec length ' +\
                    'should be {0} '.format(should_be) +\
                    'but actually is {0}'.format(actually_is)
            errors.append(error)
            continue

        index = 0
        for codec in test_codecs:
            if len(wanted_codecs) < index:
                break
            if codec != wanted_codecs[index]:
                should_be = ' '.join(wanted_codecs)
                actually_is = ' '.join(test_codecs)
                error = 'Softphone {0} {1} : '.format(user.firstname, user.lastname) +\
                        'error in codec order ' +\
                        'should be {0} '.format(should_be) +\
                        'but actually is {0}'.format(actually_is)
                errors.append(error)
                break
            index += 1
    logger.del_loop_logger()

    # Trunk check
    gateways = session.query(Gateway).all()
    wanted_codecs = ['PCMA', 'G729', 'PCMU']
    logger.new_loop_logger()
    for gateway in gateways:
        logger.new_iteration(prefix=gateway.name)
        logger.debug('Checking codec on gateway {0}'.format(gateway.host))
        codecs = session.query(Codec2Gateway).filter(Codec2Gateway.fkidgateway == gateway.idgateway).order_by(Codec2Gateway.priority).all()
        index = 0
        logger.new_loop_logger()
        for codec in codecs:
            logger.new_iteration(prefix='Priority {0}'.format(codec.priority))
            real_codec = session.query(Codec).filter(Codec.idcodec == codec.fkidcodec).first()
            logger.debug('Codec is {0}'.format(real_codec.codecrfcname))
            if len(wanted_codecs) <= index:
                break
            if wanted_codecs[index] != real_codec.codecrfcname:
                error = 'Codec on gateway {0} {1} '.format(gateway.name, gateway.host) +\
                        'Error expected {0}, got {1}'.format(wanted_codecs[index], real_codec.codecrfcname)
                errors.append(error)
                break
            index += 1
        logger.del_loop_logger()
    logger.del_loop_logger()

    # Parameter check
    parameters_to_check = {
            'E164': '0',
            'MS_LOCAL_CODEC_LIST': 'PCMA G729 PCMU G722 GSM OPUS',
            'MS_EXTERNAL_CODEC_LIST': 'PCMA G729 PCMU G722 GSM OPUS',
    }
    logger.new_loop_logger()
    for name, value in parameters_to_check.items():
        logger.new_iteration(prefix=name)
        logger.debug('Checking parameter')
        parameter = session.query(Parameter).filter(Parameter.name == name).first()
        if parameter.value != value:
            error = 'Parameter {0} '.format(name) +\
                    'Expected {0} but is {1}'.format(value, parameter.value)
            errors.append(error)
    logger.del_loop_logger()

    # Automatic update check
    parameter = session.query(Parameter).filter(Parameter.name == 'UPDATE_SCHEDULE_OPTIONS').first()
    tree = ET.fromstring(parameter.value)
    data = tree.find('UpdatesPbx')
    update_enabled = data.get('ScheduleEnabled')
    if update_enabled == 'false':
        error = 'Automatic updates are disabled, please check Wiki 3CXHelpers and fix.'
        errors.append(error)
    elif update_enabled == 'true':
        logger.debug('Automatic update are enabled')
    else:
        logger.warning('fnezjknfzekjgnejkzgnezkg')
        exit(0)

    # Phones check
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
            wanted_codecs = ['PCMA', 'G729', 'PCMU']
        elif phone_type.startswith('Snom'):
            wanted_codecs = ['G711a', 'G729', 'G711u']
        elif phone_type.startswith('Polycom'):
            wanted_codecs = ['PCMA', 'G729A/B', 'PCMU']

        if len(wanted_codecs) != len(test_codecs):
            should_be = ' '.join(wanted_codecs)
            actually_is = ' '.join(test_codecs)
            error = 'User {0} {1} '.format(user.firstname, user.lastname) +\
                    'Phone is {0} '.format(phone_type) +\
                    'error in codec length ' +\
                    'should be {0} '.format(should_be) +\
                    'but actually is {0}'.format(actually_is)
            errors.append(error)
            continue

        if not wanted_codecs:
            error = 'User {0} {1} '.format(user.firstname, user.lastname) +\
                    'Phone is {0} '.format(phone_type) +\
                    'weird phone {0}'.format(test_codecs)
            errors.append(error)
            continue

        index = 0
        for codec in test_codecs:
            if len(wanted_codecs) < index:
                break
            if codec != wanted_codecs[index]:
                should_be = ' '.join(wanted_codecs)
                actually_is = ' '.join(test_codecs)
                error = 'User {0} {1} '.format(user.firstname, user.lastname) +\
                        'Phone is {0} '.format(phone_type) +\
                        'error in codec order ' +\
                        'should be {0} '.format(should_be) +\
                        'but actually is {0}'.format(actually_is)
                errors.append(error)
                break
            index += 1
    logger.del_loop_logger()

    logger.new_loop_logger()
    if len(errors):
        logger.new_iteration(prefix='We have errors')
        host = socket.gethostname()
        logger.warning('3CX errors for {0}'.format(host))
        for error in errors:
            logger.warning(error)
    logger.del_loop_logger()


if __name__ == "__main__":
    try:
        check_3cx_data()
    except Exception as exception:
        logger.exception(exception)
