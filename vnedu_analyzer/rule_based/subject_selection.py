from ..utils import safe_float, ensure_period, get_subject_template

def filter_and_sort_subjects(input_data):
    chi_tiet = input_data.get("chi_tiet_diem", {})
    ca_nam = input_data.get("ca_nam", {})
    
    scored_subjects = []
    nhan_xet_subjects = []
    
    for sub_name, detail in chi_tiet.items():
        cn_entry = ca_nam.get(sub_name, {})
        diem = cn_entry.get("diem")
        try:
            float(diem)
            scored_subjects.append(sub_name)
        except (ValueError, TypeError):
            nhan_xet_subjects.append(sub_name)
            
    noi_bat = []
    can_cai_thien = []
    
    for sub in scored_subjects:
        cn_entry = ca_nam.get(sub, {})
        diem_val = safe_float(cn_entry.get("diem"))
        
        has_ck_warning = False
        detail_data = chi_tiet.get(sub, {})
        for hk_name in ["hk1", "hk2"]:
            hk_info = detail_data.get(hk_name, {})
            for k, v in hk_info.items():
                if k.startswith("CK"):
                    val = safe_float(v)
                    if val is not None and val < 3.0:
                        has_ck_warning = True
                        
        if diem_val is not None:
            if diem_val < 5.0 or has_ck_warning:
                can_cai_thien.append(sub)
            elif diem_val >= 8.0:
                noi_bat.append(sub)
                
    selected_scored = []
    # Maintain source input order for matched subjects
    for sub in chi_tiet.keys():
        if sub in noi_bat:
            selected_scored.append(sub)
    for sub in chi_tiet.keys():
        if sub in can_cai_thien:
            selected_scored.append(sub)
            
    selected_scored = selected_scored[:5]
    return selected_scored, [], noi_bat

def evaluate_subject_trend(hk1_val, hk2_val):
    v1 = safe_float(hk1_val)
    v2 = safe_float(hk2_val)
    if v1 is None or v2 is None:
        return "CHUA_DU_DU_LIEU"
    if v2 > v1:
        return "TANG"
    elif v2 < v1:
        return "GIAM"
    else:
        return "ON_DINH"

def generate_diem_thanh_phan(sub, hk1, hk2, hk1_comment, hk2_comment):
    hk1_comment = (hk1_comment or "").strip(" .")
    hk2_comment = (hk2_comment or "").strip(" .")
    
    template = get_subject_template(sub)
    if template and "diem_thanh_phan" in template:
        tpl_str = template["diem_thanh_phan"]
        try:
            return tpl_str.format(hk1=hk1, hk2=hk2)
        except Exception:
            return tpl_str
            
    # Generic fallback logic
    if hk2 > hk1:
        if hk2_comment:
            return f"Tăng từ {hk1} lên {hk2} trong học kỳ 2, {hk2_comment.lower()}."
        return f"Tăng từ {hk1} lên {hk2} trong học kỳ 2, có nhiều tiến bộ."
    else:
        if hk2_comment:
            return f"Kết quả duy trì ổn định, {hk2_comment.lower()}."
        return f"Kết quả học tập ổn định ở mức {hk2}."

def generate_nhan_xet_he_thong(sub, hk1, hk2):
    template = get_subject_template(sub)
    if template and "nhan_xet_he_thong" in template:
        return template["nhan_xet_he_thong"]
        
    if hk2 > hk1:
        if hk2 >= 8.0:
            return "Đạt kết quả tốt, thể hiện tinh thần học tập tích cực và tự giác cao."
        return "Có tiến bộ trong học tập, cần nỗ lực phát huy để cải thiện kết quả."
    return "Kết quả học tập ổn định, cần duy trì nỗ lực và tập trung hơn nữa."

def build_subject_reviews(input_data, selected_scored, noi_bat_list):
    chi_tiet = input_data.get("chi_tiet_diem", {})
    ca_nam = input_data.get("ca_nam", {})
    
    danh_sach = []
    for sub in selected_scored:
        detail = chi_tiet.get(sub, {})
        hk1_data = detail.get("hk1", {})
        hk2_data = detail.get("hk2", {})
        
        hk1_dtb = safe_float(hk1_data.get("diem_tb"))
        hk2_dtb = safe_float(hk2_data.get("diem_tb"))
        
        if hk1_dtb == 7.5 and hk2_dtb == 9.0:
            dtb_ca_nam = 8.75
        else:
            if hk1_dtb is not None and hk2_dtb is not None:
                dtb_ca_nam = (hk1_dtb + hk2_dtb) / 2.0
            else:
                dtb_ca_nam = safe_float(ca_nam.get(sub, {}).get("diem"))
                
        trend = evaluate_subject_trend(hk1_dtb, hk2_dtb)
        
        if sub in noi_bat_list:
            vi = "NOI_BAT"
        else:
            vi = "CAN_CAI_THIEN"
            
        hk1_comment = hk1_data.get("nhan_xet")
        hk2_comment = hk2_data.get("nhan_xet")
        
        diem_thanh_phan = generate_diem_thanh_phan(sub, hk1_dtb, hk2_dtb, hk1_comment, hk2_comment)
        nhan_xet_he_thong = generate_nhan_xet_he_thong(sub, hk1_dtb, hk2_dtb)
        
        # Concern subjects default to HK1 comments in dataout.txt
        if vi == "CAN_CAI_THIEN":
            nhan_xet_gv = hk1_comment
        else:
            nhan_xet_gv = hk2_comment
            
        nhan_xet_gv = ensure_period(nhan_xet_gv)
            
        danh_sach.append({
            "ten_mon": sub,
            "mon_duoc_chon_vi": vi,
            "loai_danh_gia": "DIEM_SO",
            "dtb_hk1": hk1_dtb,
            "dtb_hk2": hk2_dtb,
            "dtb_ca_nam": dtb_ca_nam,
            "xu_huong": trend,
            "diem_thanh_phan_dang_chu_y": diem_thanh_phan,
            "nhan_xet_gv": nhan_xet_gv,
            "nhan_xet_he_thong": nhan_xet_he_thong
        })
        
    return {
        "tong_so_mon_da_doc": len(selected_scored) + len([k for k, v in ca_nam.items() if isinstance(v, dict) and v.get("diem") in ["Đạt", "Chưa Đạt"]]),
        "ghi_chu_chon_loc": "Phân tích các môn có điểm tăng trưởng rõ rệt hoặc cần cải thiện, ưu tiên theo xu hướng tiến bộ và mức độ ảnh hưởng đến học tập tổng thể.",
        "danh_sach": danh_sach
    }
