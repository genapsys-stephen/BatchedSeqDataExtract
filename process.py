import json
import csv

def process_json(flows, data):
# ------------------- data comes from summary.json (read_aligner) -----------------------
    one_percentile = data["active_sensor_stats"]["one_percentile"]
    cs = data["cluster_size"]
    flow_order = data['flow_order']


    # Calc approximate # of flows 
    # def determine_flows(flow_list):
    #     count = 0
    #     for val in flow_list:
    #         if val == 'A':
    #             count += 1
    #         elif val == 'T':
    #             count += 1
    #         elif val == 'G':
    #             count += 1
    #         elif val == 'C':
    #             count += 1
    #     return count 

    # # Determines if flows is 133 or 300 (Can be modified to accomodate dif # of flows in the future)
    # def classify_flows(flow_num):
    #     if flow_num > 123 or flow_num < 143:
    #         return 133
    #     elif flow_num > 290 or flow_num < 310:
    #         return 300

    # flow_num = determine_flows(flow_order)
    # print('FLOW NUM: ', determine_flows(flow_order))
    # flow_group = classify_flows(flow_num)
    # print('FLOW GROUP: ', flow_group)


    # Cluster size up to 15 sensors
    def calc_surface_hit():
        cluster_list = []
        for x in range(1,16):
            # Account for scenario where there is NOT 15 values in cluster_size list
            if str(x) in cs:
                cluster_list.append(cs[str(x)])
            else: 
                print("A # between 1 to 16 is missing from cluster_list")
                break

        if len(cluster_list) < 15:
            return 0
        else:
            return sum(cluster_list)

    if flows == 133:
        return {
            "Acc80@50": "{:.3%}".format(1 - data["heatmaps"]["80%_@_50"]["cumsum_tot_error_pct"]["-1"] / 100),
            "Depth80@50": data["heatmaps"]["80%_@_50"]["depth"]["-1"][0],
            "Active": 5 * data["n_sensors_act"],
            "Aligned 32 HPs": one_percentile["aligned_count"],
            "BP20>98.5 32HPs": data["n_sensors_above_target_accuracy"]["98.5"]["20"],
            "BP50>98.5 32HPs": data["n_sensors_above_target_accuracy"]["98.5"]["50"],
            "Polyclonal (PC)": one_percentile["total_pc_count"],
            "Surface Hit": calc_surface_hit(),
        }
    elif flows == 300:
        return {
            "Acc80@20": "{:.3%}".format(1 - data["heatmaps"]["80%_@_20"]["cumsum_tot_error_pct"]["-1"] / 100),
            "Depth80@20": data["heatmaps"]["80%_@_20"]["depth"]["-1"][0],
            "Acc80@50": "{:.3%}".format(1 - data["heatmaps"]["80%_@_50"]["cumsum_tot_error_pct"]["-1"] / 100),
            "Depth80@50": data["heatmaps"]["80%_@_50"]["depth"]["-1"][0],
            "Acc80@75": "{:.3%}".format(1 - data["heatmaps"]["80%_@_75"]["cumsum_tot_error_pct"]["-1"] / 100),
            "Depth80@75": data["heatmaps"]["80%_@_75"]["depth"]["-1"][0],
            "Active": 5 * data["n_sensors_act"],
            "Aligned 32 HPs": one_percentile["aligned_count"],
            "BP50>98.5 32HPs": data["n_sensors_above_target_accuracy"]["98.5"]["50"],
            "BP75>98.5 32HPs": data["n_sensors_above_target_accuracy"]["98.5"]["75"],
            "Polyclonal (PC)": one_percentile["total_pc_count"],
            "Surface Hit": calc_surface_hit(),
        }


def process_csv(flows, SNR_data):
# ------------------- SNR data comes from SNR.csv -----------------------
    snr_csv_list = list(SNR_data)

    jumps_50 = 10
    jumps_std = 13
    jumps_raw_50 = 4
   
    def create_noise_idxs(input):
        noise_idxs = []
        for idx, row in enumerate(input):
            if row[1].strip() == 'B0':
                noise_idxs.append(idx)
        noise_idxs = noise_idxs[1:-1]
        return noise_idxs

    def increment_list_by_one(input):
        new_list = [x+1 for x in input]
        # print(new_list)
        return(new_list)

    # Key: AVG(K26, K28, K30, K32, K34)
    key_idxs = [25, 27, 29, 31, 33]
    noise_idxs = create_noise_idxs(snr_csv_list)
    jb_idxs = noise_idxs
    jbo_idxs = increment_list_by_one(noise_idxs)

    try:
        key_list = [abs(float(snr_csv_list[idx][jumps_50])) for idx in key_idxs]
        noise_list = [abs(float(snr_csv_list[idx][jumps_std])) for idx in noise_idxs]
        # print('NOISE LIST: ', noise_list)

        # JUMP_WARMUP
        jw_idxs = [6, 8, 10, 12, 14, 16]
        jw_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jw_idxs]

        # JUMP_WARMUP_O
        jwo_idxs = [7, 9, 11, 13, 15, 17]
        jwo_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jwo_idxs]

        # print(noise_list)

        jb_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jb_idxs]

        jbo_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jbo_idxs]

        return {
            "Key": round(sum(key_list) / len(key_list), 1),
            "Noise": round((sum(noise_list) / len(noise_list)), 1),
            "Jump Warm Up": round((sum(jw_list) / len(jw_list)) - (sum(jwo_list) / len(jwo_list))),
            "Jump B Flows": round((sum(jb_list) / len(jb_list)) - (sum(jbo_list) / len(jbo_list)))
        }

    except IndexError as e:
        if str(e) == "list index out of range":
            print("Potential Reasons for the error: ")
            print("-------------------------------------")
            print("1) Is the correct file being downloaded?")
            print("2) Did you set flows to the correct value (133 or 300) in config.json?")
            print("-------------------------------------")
