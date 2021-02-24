# Should rename this file since it's not populating anything
import json
import csv

def process_json(data):
    one_percentile = data['active_sensor_stats']['one_percentile']

    aligned_count = data['active_sensor_stats']['one_percentile']['aligned_count']
    total_pc_count = one_percentile['total_pc_count']
    cumsum_tot_error_pct_80at75 = data['heatmaps']['80%_@_75']['cumsum_tot_error_pct']['-1']
    depth80at75 = data['heatmaps']['80%_@_75']['depth']['-1'][0]
    # aligned_32hps = data['heatmaps']['80%_@_75']['depth']['-1'][1] # Column L
    bp50greater_than985_32hps = data['n_sensors_above_target_accuracy']['98.5']['50']
    bp75greater_than985_32hps = data['n_sensors_above_target_accuracy']['98.5']['75']
    n_sensors_act = data['n_sensors_act']
    # n_sensors_aligned = data['n_sensors_aligned'] # Column L

    # CLuster size up to 15 sensors
    cs = data['cluster_size']
    # cluster_list = [cs[str(x)] for x in range(1,16)]
    cluster_list = []
    for x in range(1,16):
        # Account for scenario where there is NOT 16 values in cluster_size list
        if str(x) in cs:
            cluster_list.append(cs[str(x)])
        else: break

    if len(cluster_list) < 16:
        surface_hit = ""
    else:
        surface_hit = sum(cluster_list)

    json_data = {
        "Acc80@75": 1 - cumsum_tot_error_pct_80at75 / 100,
        "Depth80@75": depth80at75,
        # "Key": key,
        # "Noise": noise,
        "Active": 5 * n_sensors_act,
        "Aligned 32 HPs": aligned_count,
        "BP50>98.5 32HPs": bp50greater_than985_32hps,
        "BP75>98.5 32HPs": bp75greater_than985_32hps,
        "Polyclonal (PC)": total_pc_count,
        "Surface Hit": surface_hit,
        # "Jump Warm Up":jump_warmup,
        # "Jump B Flows":jump_b
    }

    return json_data


def process_csv(SNR_data):
        # ------------------- SNR data comes from SNR.csv -----------------------
    snr_csv_list = list(SNR_data)
    jumps_50 = 10
    jumps_std = 13
    jumps_raw_50 = 4

    # Key: AVG(K26, K28, K30, K32, K34)
    key_list = [
        abs(float(snr_csv_list[25][jumps_50])),
        abs(float(snr_csv_list[27][jumps_50])),
        abs(float(snr_csv_list[29][jumps_50])),
        abs(float(snr_csv_list[31][jumps_50])),
        abs(float(snr_csv_list[33][jumps_50]))
    ]

    # Noise: AVG(N24, N36, N43, N77, N113, N115, N149, N185, N192, N226, N262, N264, N298, N334, N341, N375, N411, N413, N447, N483, N490, N524, N560, N562, N596, N632)
    noise_list = [
        abs(float(snr_csv_list[23][jumps_std])),
        abs(float(snr_csv_list[35][jumps_std])),
        abs(float(snr_csv_list[42][jumps_std])),
        abs(float(snr_csv_list[76][jumps_std])),
        abs(float(snr_csv_list[112][jumps_std])),
        abs(float(snr_csv_list[114][jumps_std])),
        abs(float(snr_csv_list[148][jumps_std])),
        abs(float(snr_csv_list[184][jumps_std])),
        abs(float(snr_csv_list[191][jumps_std])),
        abs(float(snr_csv_list[225][jumps_std])),
        abs(float(snr_csv_list[261][jumps_std])),
        abs(float(snr_csv_list[263][jumps_std])),
        abs(float(snr_csv_list[297][jumps_std])),
        abs(float(snr_csv_list[333][jumps_std])),
        abs(float(snr_csv_list[340][jumps_std])),
        abs(float(snr_csv_list[374][jumps_std])),
        abs(float(snr_csv_list[410][jumps_std])),
        abs(float(snr_csv_list[412][jumps_std])),
        abs(float(snr_csv_list[446][jumps_std])),
        abs(float(snr_csv_list[482][jumps_std])),
        abs(float(snr_csv_list[489][jumps_std])),
        abs(float(snr_csv_list[523][jumps_std])),
        abs(float(snr_csv_list[559][jumps_std])),
        abs(float(snr_csv_list[561][jumps_std])),
        abs(float(snr_csv_list[595][jumps_std])),
        abs(float(snr_csv_list[631][jumps_std]))
    ]

    jump_warmup_list= [
        (float(snr_csv_list[6][jumps_raw_50])),
        (float(snr_csv_list[8][jumps_raw_50])),
        (float(snr_csv_list[10][jumps_raw_50])),
        (float(snr_csv_list[12][jumps_raw_50])),
        (float(snr_csv_list[14][jumps_raw_50])),
        (float(snr_csv_list[16][jumps_raw_50]))
        ]
    jump_warmup_o_list= [
        (float(snr_csv_list[7][jumps_raw_50])),
        (float(snr_csv_list[9][jumps_raw_50])),
        (float(snr_csv_list[11][jumps_raw_50])),
        (float(snr_csv_list[13][jumps_raw_50])),
        (float(snr_csv_list[15][jumps_raw_50])),
        (float(snr_csv_list[17][jumps_raw_50]))
        ]
    jump_b_list= [
        (float(snr_csv_list[23][jumps_raw_50])),
        (float(snr_csv_list[35][jumps_raw_50])),
        (float(snr_csv_list[42][jumps_raw_50])),
        (float(snr_csv_list[76][jumps_raw_50])),
        (float(snr_csv_list[112][jumps_raw_50])),
        (float(snr_csv_list[114][jumps_raw_50])),
        (float(snr_csv_list[148][jumps_raw_50])),
        (float(snr_csv_list[184][jumps_raw_50])),
        (float(snr_csv_list[191][jumps_raw_50])),
        (float(snr_csv_list[225][jumps_raw_50])),
        (float(snr_csv_list[261][jumps_raw_50])),
        (float(snr_csv_list[263][jumps_raw_50])),
        (float(snr_csv_list[297][jumps_raw_50])),
        (float(snr_csv_list[333][jumps_raw_50])),
        (float(snr_csv_list[340][jumps_raw_50])),
        (float(snr_csv_list[374][jumps_raw_50])),
        (float(snr_csv_list[410][jumps_raw_50])),
        (float(snr_csv_list[412][jumps_raw_50])),
        (float(snr_csv_list[446][jumps_raw_50])),
        (float(snr_csv_list[482][jumps_raw_50])),
        (float(snr_csv_list[489][jumps_raw_50])),
        (float(snr_csv_list[523][jumps_raw_50])),
        (float(snr_csv_list[559][jumps_raw_50])),
        (float(snr_csv_list[561][jumps_raw_50])),
        (float(snr_csv_list[595][jumps_raw_50])),
        (float(snr_csv_list[631][jumps_raw_50]))
    ]
    jump_b_o_list= [
        (float(snr_csv_list[24][jumps_raw_50])),
        (float(snr_csv_list[36][jumps_raw_50])),
        (float(snr_csv_list[43][jumps_raw_50])),
        (float(snr_csv_list[77][jumps_raw_50])),
        (float(snr_csv_list[113][jumps_raw_50])),
        (float(snr_csv_list[115][jumps_raw_50])),
        (float(snr_csv_list[149][jumps_raw_50])),
        (float(snr_csv_list[185][jumps_raw_50])),
        (float(snr_csv_list[192][jumps_raw_50])),
        (float(snr_csv_list[226][jumps_raw_50])),
        (float(snr_csv_list[262][jumps_raw_50])),
        (float(snr_csv_list[264][jumps_raw_50])),
        (float(snr_csv_list[298][jumps_raw_50])),
        (float(snr_csv_list[334][jumps_raw_50])),
        (float(snr_csv_list[341][jumps_raw_50])),
        (float(snr_csv_list[375][jumps_raw_50])),
        (float(snr_csv_list[411][jumps_raw_50])),
        (float(snr_csv_list[413][jumps_raw_50])),
        (float(snr_csv_list[447][jumps_raw_50])),
        (float(snr_csv_list[483][jumps_raw_50])),
        (float(snr_csv_list[490][jumps_raw_50])),
        (float(snr_csv_list[524][jumps_raw_50])),
        (float(snr_csv_list[560][jumps_raw_50])),
        (float(snr_csv_list[562][jumps_raw_50])),
        (float(snr_csv_list[596][jumps_raw_50])),
        (float(snr_csv_list[632][jumps_raw_50]))
    ]

    key = round(sum(key_list) / len(key_list), 1)
    noise = round((sum(noise_list) / len(noise_list)), 1)
    jump_warmup = round(
        (sum(jump_warmup_list) / len(jump_warmup_list)) - (sum(jump_warmup_o_list) / len(jump_warmup_o_list))
    )
    jump_b = round(
        (sum(jump_b_list) / len(jump_b_list)) - (sum(jump_b_o_list) / len(jump_b_o_list))
    )

    csv_data = {
        "Key": key,
        "Noise": noise,
        "Jump Warm Up":jump_warmup,
        "Jump B Flows":jump_b
    }

    return csv_data