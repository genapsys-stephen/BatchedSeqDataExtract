import json
import csv

def process_json(data):
    one_percentile = data['active_sensor_stats']['one_percentile']
    cs = data['cluster_size']
    # Cluster size up to 15 sensors
    def calc_surface_hit():
        cluster_list = []
        for x in range(1,16):
            # Account for scenario where there is NOT 15 values in cluster_size list
            if str(x) in cs:
                cluster_list.append(cs[str(x)])
            else: 
                print('A # between 1 to 16 is missing from cluster_list')
                break

        if len(cluster_list) < 15:
            return 0
        else:
            return sum(cluster_list)

    return {
        "Acc80@75": 1 - data['heatmaps']['80%_@_75']['cumsum_tot_error_pct']['-1'] / 100,
        "Depth80@75": data['heatmaps']['80%_@_75']['depth']['-1'][0],
        "Active": 5 * data['n_sensors_act'],
        "Aligned 32 HPs": one_percentile['aligned_count'],
        "BP50>98.5 32HPs": data['n_sensors_above_target_accuracy']['98.5']['50'],
        "BP75>98.5 32HPs": data['n_sensors_above_target_accuracy']['98.5']['75'],
        "Polyclonal (PC)": one_percentile['total_pc_count'],
        "Surface Hit": calc_surface_hit(),
    }


def process_csv(SNR_data):
# ------------------- SNR data comes from SNR.csv -----------------------
    snr_csv_list = list(SNR_data)
    jumps_50 = 10
    jumps_std = 13
    jumps_raw_50 = 4

    # Key: AVG(K26, K28, K30, K32, K34)
    key_idxs = [25, 27, 29, 31, 33]
    key_list = [abs(float(snr_csv_list[idx][jumps_50])) for idx in key_idxs]

    # Noise: AVG(N24, N36, N43, N77, N113, N115, N149, N185, N192, N226, N262, N264, N298, N334, N341, N375, N411, N413, N447, N483, N490, N524, N560, N562, N596, N632)
    noise_idxs = [23, 35, 42, 76, 112, 114, 148, 184, 191, 225, 261, 263, 297, 333, 340, 374, 410, 412, 446, 482, 489, 523, 559, 561, 595, 631]
    noise_list = [abs(float(snr_csv_list[idx][jumps_std])) for idx in noise_idxs]

    # JUMP_WARMUP
    jw_idxs = [6, 8, 10, 12, 14, 16]
    jw_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jw_idxs]

    # JUMP_WARMUP_O
    jwo_idxs = [7, 9, 11, 13, 15, 17]
    jwo_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jwo_idxs]

    # JUMP_B
    jb_idxs = [23, 35, 42, 76, 112, 114, 148, 184, 191, 225, 261, 263, 297, 333, 340, 374, 410, 412, 446, 482, 489, 523, 559, 561, 595, 631]
    jb_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jb_idxs]

    # JUMP_B_O
    jbo_idxs = [24, 36, 43, 77, 113, 115, 149, 185, 192, 226, 262, 264, 298, 334, 341, 375, 411, 413, 447, 483, 490, 524, 560, 562, 596, 632]
    jbo_list = [float(snr_csv_list[idx][jumps_raw_50]) for idx in jbo_idxs]

    return {
        "Key": round(sum(key_list) / len(key_list), 1),
        "Noise": round((sum(noise_list) / len(noise_list)), 1),
        "Jump Warm Up": round((sum(jw_list) / len(jw_list)) - (sum(jwo_list) / len(jwo_list))),
        "Jump B Flows": round((sum(jb_list) / len(jb_list)) - (sum(jbo_list) / len(jbo_list)))
    }