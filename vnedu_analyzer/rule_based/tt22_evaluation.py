def evaluate_tt22_rules(input_data, is_khuyet_tat):
    if is_khuyet_tat:
        return {
            "ap_dung_tt22": False,
            "xep_loai_hoc_tap": None,
            "xep_loai_ren_luyen": None,
            "warnings": []
        }
    
    phase = input_data.get("phase", "ca_nam")
    phase_data = input_data.get(phase, {})
    
    scored_subjects = {}
    nhan_xet_subjects = {}
    
    for subject_name, subject_info in phase_data.items():
        if subject_name in ["diem_tb", "kq_ht", "kq_rl", "nghi_co_phep", "nghi_khong_phep"]:
            continue
        if not isinstance(subject_info, dict):
            continue
        diem = subject_info.get("diem")
        if diem is not None:
            try:
                val = float(diem)
                scored_subjects[subject_name] = val
            except ValueError:
                nhan_xet_subjects[subject_name] = diem
                
    nx_chua_dat_count = sum(1 for v in nhan_xet_subjects.values() if v == "Chưa Đạt")
    all_nx_dat = (nx_chua_dat_count == 0)
    
    above_8 = sum(1 for v in scored_subjects.values() if v >= 8.0)
    above_6_5 = sum(1 for v in scored_subjects.values() if v >= 6.5)
    above_5 = sum(1 for v in scored_subjects.values() if v >= 5.0)
    any_below_3_5 = any(v < 3.5 for v in scored_subjects.values())
    any_below_5 = any(v < 5.0 for v in scored_subjects.values())
    any_below_6_5 = any(v < 6.5 for v in scored_subjects.values())
    
    xep_loai = "CHƯA ĐẠT"
    if all_nx_dat and not any_below_6_5 and above_8 >= 6:
        xep_loai = "TỐT"
    elif all_nx_dat and not any_below_5 and above_6_5 >= 6:
        xep_loai = "KHÁ"
    elif nx_chua_dat_count <= 1 and above_5 >= 6 and not any_below_3_5:
        xep_loai = "ĐẠT"
        
    xep_loai_ren_luyen = phase_data.get("kq_rl")
    
    return {
        "ap_dung_tt22": True,
        "xep_loai_hoc_tap": xep_loai,
        "xep_loai_ren_luyen": xep_loai_ren_luyen,
        "warnings": []
    }
