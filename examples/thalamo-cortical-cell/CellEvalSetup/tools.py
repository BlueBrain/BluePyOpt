def rename_prot(name):
    if 'RMP' in name:
        name = "(No stim)"
    elif 'Rin_dep' in name:
        #name = name.replace('.Rin','Hyp_-40')
        name = "($-$40%)" #"R_{input} - tonic"
    elif 'Rin_hyp' in name:
        #name = name.replace('.Rin','Hyp_-40')
        name = "($-$40% - b)"
    elif 'hyp' in name and "Step" in name:
        name = '(150% - burst)'
        name = '(225% - burst)'
        name = '(200% - burst)'
    elif 'Step_150' in name:
        name = '(150% - tonic)'
    elif 'Step_200' in name:
        name = '(200% - tonic)'
    elif 'Step_250' in name:
        name = '(250% - tonic)'
    elif 'IV_-140' in name:
        name = "($-$140%)"
    elif 'ThresholdDetection_dep' in name:
         name = ''
    elif 'ThresholdDetection_hyp' in name:
         name = ''
    elif 'hold_dep' in name:
        name = "(I$_{hold}$ - tonic)"
    elif 'hold_hyp' in name:
        name = "(I$_{hold}$ - burst)"

    #name = name.replace("soma.v.", "")
    return name

def rename_featpart(name):
    import json
    namemap = {
        "steady_state_voltage_stimend": "V$_{rest}$",
        "sag_amplitude": "Sag amp.",
        "ohmic_input_resistance_vb_ssse": "R$_{input}$",
        "voltage_base": "Baseline V$_m$",
        "Spikecount": "Num. of APs",
        "voltage_after_stim": "V$_m$ after stim.",
        "inv_first_ISI": "Inv. 1$^{st}$ ISI",
        "inv_last_ISI": "Inv. last ISI",
        "inv_second_ISI": "Inv. 2$^{nd}$ ISI",
        "time_to_first_spike": "Latency 1$^{st}$ AP",
        "AP1_amp": "Amp. 1$^{st}$ AP ",
        "AP2_amp": "Amp. 2$^{nd}$ AP ",
        "AHP_depth": "AHP depth",
        "AHP_depth_abs": "AHP depth",
        "AP_amplitude": "AP amp.",
        "AP_width": "AP width",
        "AP_duration_half_width": "AP half-width",
        "Spikecount_stimint": "Num. of APs",
        "bpo_threshold_current_dep": "I$_{thr}$ - tonic",
        "bpo_threshold_current_hyp": "I$_{thr}$ - burst",
        "time_to_last_spike": "Latency last AP",
        "adaptation_index2": "Adaptation idx",
        "mean_frequency": "Frequency"
    }
    return namemap[name]

def rename_feat(name, sep = " "):
    prot_name = name.split(".")[1]
    feat_name = name.split(".")[-1]
    new_prot = rename_prot(prot_name)
    new_feat = rename_featpart(feat_name)

    return new_feat + sep + new_prot

