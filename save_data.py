from __future__ import print_function

import argparse
import copy
import json
import os
import platform
import re
import shutil
import time
from datetime import datetime
from zipfile import ZipFile
import csv
import urllib
import httplib2
import requests

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


from populate import process_json, process_csv

ENV_DATA = {
    'dev': {
        'google_storage': 'https://storage.googleapis.com/genapsys-platform-dev-2-robert-lab',
        'api_url': 'https://cloudapp.dev.genapsys.com:443/api/v1/analyses',
        'key_file': 'key.txt'
    },
    'genhub': {
        'google_storage': 'https://storage.googleapis.com/genapsys-platform-stg-alpha-test',
        'api_url': 'https://genhub.genapsys.com/api/v1/analyses',
        'key_file': 'genhub_key.txt'
    },
    # jax has not been tested
    'jax': {
        'google_storage': 'https://storage.googleapis.com/genapsys-stg-data-jax',
        'api_url': 'https://genhub.genapsys.com:443/api/v1/analyses',
        'key_file': 'jax_key.txt'
    }
}

# Figures to pull from GCP
figures_dict = {
	"sign_filter": ["Active_sensors_boxplot_stats.csv"],
	"read_aligner": ["summary.json"],
}


def get_json(path):
    with open(path) as json_file:
        data = json.load(json_file)
    return data

def is_url_valid(url):
    valid = False
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        valid = True
    return valid


gcp_env = ENV_DATA['dev'] # GCP info
config = get_json('./add_plots_to_google_slides_config.json') # Path to config.json file
analysis_ids = config['analysis_list'] # List of samples provided in config.json file
analysis_ids = [str(a_id) if not isinstance(a_id, str) else a_id for a_id in analysis_ids]  # Make sure samples in analysis list are strings
sample_list = config['sample_list']

def get_cloud_path(analysis_id, genv):
    # Getting the analysis paths from the ID

    with open(genv['key_file'], "r") as key_text_file:
        api_key = key_text_file.readline().strip()
        # print('API_KEY', api_key)

    # api call to the data base to get the analysis paths json file
    api_url = genv['api_url']
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    data = json.dumps({"api_key": api_key, "analyses": [analysis_id]})
    response = requests.get(api_url, headers=headers, timeout=10000, data=data, verify=True)
    db_query = response.json()

    if db_query.get('data'):
        db_run_id = db_query['data'][0]['runs'][0]
        analysis_paths = db_query['data'][0]['output'][str(db_run_id)]['paths']['modules']

        # fix keys for backward compatibility
        temp_analysis_paths = copy.deepcopy(analysis_paths)
        for key, value in temp_analysis_paths.items():
            analysis_paths[key + '_path'] = value
            analysis_paths.pop(key)

        analysis_paths['run_information'] = db_query['data'][0]['output'][str(db_run_id)]['paths']['run_information']
        analysis_paths['directory_version'] = db_query['data'][0]['output'][str(db_run_id)]['paths'].get(
            'directory_version', 1)
        analysis_paths['eureka_context_id'] = db_query['data'][0]['config'].get('eureka_context','')
        # print("Eureka Context: '{}'".format(analysis_paths['eureka_context_id']))
        analysis_root = db_query['data'][0]['output'][str(db_run_id)]['paths']['analysis_config_path'].replace(
            '/analysis_config.json', '')
    else:
        print('query to database did not return analysis paths')
        analysis_root = analysis_paths = None

    return analysis_root, analysis_paths


def get_data_paths(analysis_ids, gcp_env):
    paths_list = []
    print('Getting cloud analysis data paths...')
    for analysis_id in analysis_ids:
        analysis_root, data_paths = get_cloud_path(analysis_id, gcp_env)
        paths_list.append(data_paths)

    return paths_list


analysis_list = get_data_paths(analysis_ids, gcp_env) # Get GCP paths to samples listed in analysis list --> returns JSON *** USEFUL ***


def is_date(date_text):
    try:
        datetime.strptime(date_text, '%Y_%m_%d_%H_%M_%S')
        valid = True
    except ValueError:
        valid = False

    return valid


def get_module_url_from_path(key, path_json_obj, analysis_id, gcp_env, attempt=None):
    # key is sensor_id, sign_filter, read_aligner, binary_caller
    # analysis_id is id from cloudapp that we provide to JSON file
    # print('PATH JSON OBJ: ', path_json_obj)
    # print('ANALYSIS ID: ', analysis_id)

    # get module url from module path
    path_to_module = path_json_obj.get(key + '_path')
    # print('PATH TO MODULE: ', path_to_module)
    # print('KEY: ', key)
    # print('PATH TO MODULE: ', path_to_module)

    if '/' not in key:  # R1 or R2 not specified use R1 as default read
        key2 = 'R1/%s' % key
        if key2 + '_path' in path_json_obj:
            path_to_module = path_json_obj.get(key2 + '_path')
    elif not path_to_module and 'R1/' in key:  # key is R1/<module> but template does not have R1/
        key2 = key.lstrip('R1/')
        if key2 + '_path' in path_json_obj:
            path_to_module = path_json_obj.get(key2 + '_path')
    if not path_to_module:
        return None
    if is_date(path_to_module.split('/')[-1].split('.')[-1]):
        # folder structure version 1
        path_to_module = path_to_module.replace('/data/gcs', '/results/%s/gcs' % analysis_id)
    else:
        # folder structure version 2
        path_to_module = path_to_module.replace('/data/gcs', '/results')

    module_url = gcp_env['google_storage'] + path_to_module
    # if not is_url_valid(module_url) and attempt is None:
    #     module_url = get_module_url_from_path(key, path_json_obj, path_json_obj.get("eureka_context_id"), gcp_env, 1)
    # print('MODULE URL: ', module_url)
    return module_url



def analyze():
    with open('seq_stats.csv', mode='w') as file:
        fieldnames = ['Chip Label', 'Acc80@75', 'Depth80@75','Key', 'Noise', 'Active','Aligned 32 HPs', 'BP50>98.5 32HPs', 'BP75>98.5 32HPs', 'Polyclonal (PC)','Surface Hit','Jump Warm Up','Jump B Flows']
        
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        extracted_data = []
        # Loop through samples
        for i, analysis in enumerate(analysis_list):
            analysis_id = analysis['run_information']['analysis_id']

            data_dict = {}
            # Loop through sign_filter, read_aligner, binary_caller, sensor_id
            for key in figures_dict.keys():
                # print('KEY: ', key)
                # URL for a module (sign_filter, read_aligner, binary_caller, sensor_id)
                module_url = get_module_url_from_path(key, analysis, analysis_id, gcp_env)

                # print('MODULE URL: ', module_url)
                # Loop through every figure in figures_dictionary
                for element in figures_dict.get(key):
                    url = module_url + '/' + element
                    if not is_url_valid(url):
                        # Looks like there may be alternate URLS for certain files/samples depending on the analysis for that sample
                        module_url = get_module_url_from_path(key, analysis, analysis.get("eureka_context_id"), gcp_env, 1)
                        url = module_url + '/' + element
                        if not is_url_valid(url):
                            print("File %s doesn't exist, skipping." % url)
                            # missing_figures_list.append((key, element))
                            continue
                    # print('URL: ', url)
                    # print('ELEMENT: ', element)
                    if element == 'summary.json':
                        json_file = urllib.request.urlopen(url)
                        summary = json.loads(json_file.read().decode())
                        json_data = process_json(summary)
                        data_dict.update(json_data)
                        # print('Summary.json data: ', json_data)

                    elif element == 'Active_sensors_boxplot_stats.csv':
                        csv_file = urllib.request.urlopen(url)
                        # SNR_CSV = open(csv_file, 'r')
                        # readlines not calculating properly
                        SNR_CSV = [l.decode('utf-8') for l in csv_file.readlines()]
                        SNR_data = csv.reader(SNR_CSV, delimiter=',')
                        # for i, line in enumerate(SNR_data):
                        #     print('line: ', i, line)
                        # print('SNR_data: ', SNR_data)
                        csv_json = process_csv(SNR_data)
                        data_dict.update(csv_json)
                        # print('CSV DATA: ', csv_json)
            data_dict['Chip Label'] = sample_list[i]

            extracted_data.append(data_dict)
            csv_writer.writerow(data_dict)


        # print('EXTRACTED DATA: ', extracted_data)
        print('======================== DATA EXTRACTED & SAVED TO seq_stats.csv ========================')

analyze()