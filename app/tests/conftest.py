import os
import configparser
from pathlib import Path

import pytest

from fuseki_manager import FusekiAdminClient#, FusekiDataClient
from fuseki_manager.exceptions import DatasetNotFoundError

from bemserver.database.ontology.manager import (
    ontology_manager_factory)


def ontology_db_config():

    test_settings_file = os.getenv('BEMTEST_SETTINGS_FILE')
    config = configparser.ConfigParser()    
    config.read(test_settings_file)
    cfg = config['TESTING']
    return {
        'dataset': cfg['DATASET'],
        'host': cfg['HOST'],
        'port': cfg['PORT'],
        'ssl': False,
        'metadata': {
            'path': cfg['METADATA_PATH'],
            'files': [
                'BuildingInfrastructure.rdf',
                'Property.rdf',
                'UserBehaviour.rdf',
                'sosa.rdf', 'ssn.rdf', 'Services.rdf'
            ],
        },
        'config_file': {
            'path': 'tests/database/ontology',
            'file': 'bemserver_test.ttl',
        },
    }


def _build_onto_metadata_path(metadata_path, filename):
    cur_path = Path(os.path.realpath(__file__))
    return cur_path.parent.parent / metadata_path / filename


def init_onto_db(use_file=False):
    db_config = ontology_db_config()

    admin_client = FusekiAdminClient(
        host=db_config['host'], port=db_config.get('port'),
        is_secured=db_config.get('ssl', False))

    try:
        admin_client.delete_dataset(db_config['dataset'], force_drop_data=True)
    except DatasetNotFoundError:
        pass
    if use_file:
        admin_client.create_dataset_from_config_file(
            _build_onto_metadata_path(db_config['config_file']['path'],
                                      db_config['config_file']['file']))
    else:
        admin_client.create_dataset(db_config['dataset'])
    # upload description files
    onto_files = [
        _build_onto_metadata_path(db_config['metadata']['path'], cur_filename)
        for cur_filename in db_config['metadata']['files']
    ]
    admin_client.restore_data(db_config['dataset'], onto_files)

    onto_db_url = 'http{ssl}://{host}{sep_port}{port}/{ds_name}'.format(
        ssl='s' if db_config.get('ssl', False) else '',
        host=db_config['host'],
        sep_port=':' if db_config.get('port') is not None else '',
        port=db_config.get('port', ''),
        ds_name=db_config['dataset'])
    return onto_db_url


@pytest.fixture()
def init_onto_mgr_fact():
    onto_db_url = init_onto_db(use_file=True)
    ontology_manager_factory.open(onto_db_url)
    yield
    ontology_manager_factory.close()
