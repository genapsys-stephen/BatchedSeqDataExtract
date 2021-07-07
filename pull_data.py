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

from process import process_json, process_csv

ENV_DATA = {
    "dev": {
        "google_storage": "https://storage.googleapis.com/genapsys-platform-dev-2-robert-lab",
        "api_url": "https://cloudapp.dev.genapsys.com:443/api/v1/analyses",
        "key_file": "key.txt"
    }
}

# ==================================================== Figures to pull from GCP =========================================================
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


gcp_env = ENV_DATA["dev"] # GCP info
config = get_json("./config.json") # Path to config.json file
analysis_ids = config["analysis_list"] # List of samples provided in config.json file
analysis_ids = [str(a_id) if not isinstance(a_id, str) else a_id for a_id in analysis_ids]  # Make sure samples in analysis list are strings
sample_list = config["sample_list"]

flows = None
flows = int(config["flows"])

def get_cloud_path(analysis_id, genv):
    # Getting the analysis paths from the ID
    with open(genv["key_file"], "r") as key_text_file:
        api_key = key_text_file.readline().strip()

    # api call to the data base to get the analysis paths json file
    api_url = genv["api_url"]
    headers = {"Content-type": "application/json", "Accept": "application/json"}
    data = json.dumps({"api_key": api_key, "analyses": [analysis_id]})
    response = requests.get(api_url, headers=headers, timeout=10000, data=data, verify=True)
    # print('REPONSE: ', response)
    db_query = response.json()

    # print("DB QUERY: ", db_query)

    # path is not always found for valid runs/re-analysis
    if db_query.get("data"):
        db_run_id = db_query["data"][0]["runs"][0]
        analysis_paths = db_query["data"][0]["output"][str(db_run_id)]["paths"]["modules"]

        # fix keys for backward compatibility
        temp_analysis_paths = copy.deepcopy(analysis_paths)
        for key, value in temp_analysis_paths.items():
            analysis_paths[key + "_path"] = value
            analysis_paths.pop(key)

        analysis_paths["run_information"] = db_query["data"][0]["output"][str(db_run_id)]["paths"]["run_information"]
        analysis_paths["directory_version"] = db_query["data"][0]["output"][str(db_run_id)]["paths"].get(
            "directory_version", 1)
        analysis_paths["eureka_context_id"] = db_query["data"][0]["config"].get("eureka_context","")
        # print("Eureka Context: "{}"".format(analysis_paths["eureka_context_id"]))
        analysis_root = db_query["data"][0]["output"][str(db_run_id)]["paths"]["analysis_config_path"].replace(
            "/analysis_config.json", "")

    # 4/9/21 Been noticing that analysis paths are not always found
    else:
        print("query to database did not return analysis paths")
        analysis_root = analysis_paths = None

    return analysis_root, analysis_paths


def get_data_paths(analysis_ids, gcp_env):
    paths_list = []
    print("Getting cloud analysis data paths...")
    for analysis_id in analysis_ids:
        print('analysis id: ', analysis_id)
        analysis_root, data_paths = get_cloud_path(analysis_id, gcp_env)
        paths_list.append(data_paths)
    
    # print('PATHS-LIST: ', paths_list)

    return paths_list


analysis_list = get_data_paths(analysis_ids, gcp_env) # Get GCP paths to samples listed in analysis list --> returns JSON *** USEFUL ***

def is_date(date_text):
    try:
        datetime.strptime(date_text, "%Y_%m_%d_%H_%M_%S")
        valid = True
    except ValueError:
        valid = False

    return valid


def get_module_url_from_path(key, path_json_obj, analysis_id, gcp_env, attempt=None):
    # key is sensor_id, sign_filter, read_aligner, binary_caller
    # analysis_id is id from cloudapp that we provide to JSON file
    # get module url from module path
    path_to_module = path_json_obj.get(key + "_path")

    if "/" not in key:  # R1 or R2 not specified use R1 as default read
        key2 = "R1/%s" % key
        if key2 + "_path" in path_json_obj:
            path_to_module = path_json_obj.get(key2 + "_path")
    elif not path_to_module and "R1/" in key:  # key is R1/<module> but template does not have R1/
        key2 = key.lstrip("R1/")
        if key2 + "_path" in path_json_obj:
            path_to_module = path_json_obj.get(key2 + "_path")
    if not path_to_module:
        return None
    if is_date(path_to_module.split("/")[-1].split(".")[-1]):
        # folder structure version 1
        path_to_module = path_to_module.replace("/data/gcs", "/results/%s/gcs" % analysis_id)
    else:
        # folder structure version 2
        path_to_module = path_to_module.replace("/data/gcs", "/results")

    module_url = gcp_env["google_storage"] + path_to_module
    # if not is_url_valid(module_url) and attempt is None:
    #     module_url = get_module_url_from_path(key, path_json_obj, path_json_obj.get("eureka_context_id"), gcp_env, 1)
    return module_url


def analyze():
    with open("seq_stats.csv", mode="w", newline="") as file:

        # print(analysis_list[0])

        if flows == 133:
            fieldnames = ["Run ID","Chip Label", "Analysis ID", "Acc80@50", "Depth80@50","Key", "Noise", "Active","Aligned 32 HPs", "BP20>98.5 32HPs", "BP50>98.5 32HPs", "Polyclonal (PC)","Surface Hit","Jump Warm Up","Jump B Flows"]
        elif flows == 300:
            fieldnames = ["Run ID","Chip Label", "Analysis ID", "Acc80@20", "Depth80@20", "Acc80@50", "Depth80@50", "Acc80@75", "Depth80@75","Key", "Noise", "Active","Aligned 32 HPs", "BP50>98.5 32HPs", "BP75>98.5 32HPs", "Polyclonal (PC)","Surface Hit","Jump Warm Up","Jump B Flows"]
        else:
            print("Please check config.json file that flows is 133 or 300")

        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        # extracted_data = [] # extracted_data doesn't appear to be doing anything
        
        # Loop through samples
        for i, analysis in enumerate(analysis_list):
            analysis_id = analysis["run_information"]["analysis_id"]
            data_dict = {} #data_dict created for each sample
            # print("ANALYSIS: ", analysis)
            # Loop through sign_filter, read_aligner, binary_caller, sensor_id
            for key in figures_dict.keys():
                module_url = get_module_url_from_path(key, analysis, analysis_id, gcp_env)
                # print('MODULE URL: ', module_url)
                # https://storage.googleapis.com/genapsys-platform-dev-2-robert-lab/results/S000456/S000456_RUN_2021_04_08_11_34_05/eureka/84000/84000/20210409.100450/R1/read_aligner
                # https://console.cloud.google.com/storage/browser/genapsys-platform-dev-2-robert-lab/results/B000150/B000150_RUN_2021_04_08_13_36_51/eureka/84075/84075/20210409.123637/R1/read_aligner?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&prefix=&forceOnObjectsSortingFiltering=false
                # Loop through every figure in figures_dictionary
                for element in figures_dict.get(key):
                    url = str(module_url) + "/" + element
                    if not is_url_valid(url):
                        # Looks like there may be alternate URLS for certain files/samples depending on the analysis for that sample
                        module_url = get_module_url_from_path(key, analysis, analysis.get("eureka_context_id"), gcp_env, 1)
                        
                        url = module_url + "/" + element
                        # print('URL: ', url)
                        if not is_url_valid(url):
                            print("File %s doesn't exist, skipping." % url)
                            # missing_figures_list.append((key, element))
                            continue
                    if element == "summary.json":
                        json_file = urllib.request.urlopen(url)
                        summary = json.loads(json_file.read().decode())
                        json_data = process_json(flows, summary)
                        data_dict.update(json_data)

                    elif element == "Active_sensors_boxplot_stats.csv":
                        csv_file = urllib.request.urlopen(url)
                        SNR_CSV = [l.decode("utf-8") for l in csv_file.readlines()]
                        SNR_data = csv.reader(SNR_CSV, delimiter=",")
                        csv_json = process_csv(flows, SNR_data)
                        data_dict.update(csv_json)
            data_dict["Run ID"] = analysis["run_information"]["run_id"]
            data_dict["Chip Label"] = sample_list[i]
            data_dict["Analysis ID"] = analysis_id

            # extracted_data.append(data_dict)
            csv_writer.writerow(data_dict)
            # print('DATA_DICT: ', data_dict)


        print("======================== DATA EXTRACTED & SAVED TO seq_stats.csv ========================")


if __name__ == "__main__":
    analyze()