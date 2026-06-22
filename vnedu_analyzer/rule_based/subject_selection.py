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

def generate_diem_thanh_phan(sub, hk1, hk2, hk1_comment, hk2_comment, is_outstanding=True):
    v1 = safe_float(hk1)
    v2 = safe_float(hk2)
    if v1 is None or v2 is None:
        return f"Kết quả học tập môn {sub} được duy trì."
        
    trend = "tăng" if v2 > v1 else "giảm" if v2 < v1 else "ổn định"
    
    if is_outstanding:
        if trend == "tăng":
            return f"Kết quả học tập môn {sub} tiến bộ rõ rệt trong học kỳ 2, tăng từ {v1:.1f} lên {v2:.1f}."
        elif trend == "giảm":
            return f"Duy trì kết quả học tập tốt môn {sub} ở học kỳ 2 với điểm trung bình đạt {v2:.1f}."
        else:
            return f"Kết quả học tập môn {sub} được duy trì ổn định ở mức tốt đạt {v2:.1f}."
    else:
        if trend == "tăng":
            return f"Có tiến bộ nhẹ môn {sub} từ {v1:.1f} lên {v2:.1f} nhưng điểm số nhìn chung vẫn cần nỗ lực cải thiện."
        elif trend == "giảm":
            return f"Điểm số môn {sub} có phần sụt giảm ở học kỳ 2 từ {v1:.1f} xuống {v2:.1f}, cần tập trung ôn tập hơn."
        else:
            return f"Điểm số môn {sub} còn ở mức thấp đạt {v2:.1f}, cần tích cực củng cố lại kiến thức."

def generate_nhan_xet_he_thong(sub, hk1, hk2, is_outstanding=True):
    v2 = safe_float(hk2)
    if v2 is None:
        return f"Kết quả học tập môn {sub} cần được tiếp tục theo dõi."
        
    if is_outstanding:
        if v2 >= 8.0:
            return f"Hoàn thành xuất sắc các nội dung học tập môn {sub}, tiếp thu bài nhanh và tự giác."
        else:
            return f"Hoàn thành tốt yêu cầu môn {sub}, có tinh thần học tập tích cực và chủ động."
    else:
        if v2 < 5.0:
            return f"Chưa hoàn thành đầy đủ yêu cầu bộ môn {sub}, cần tăng cường ôn luyện để đạt kết quả trung bình."
        else:
            return f"Kết quả học tập môn {sub} ở mức trung bình, cần tập trung hơn nữa trong việc làm bài tập."

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
        
        is_outstanding = (vi == "NOI_BAT")
        diem_thanh_phan = generate_diem_thanh_phan(sub, hk1_dtb, hk2_dtb, hk1_comment, hk2_comment, is_outstanding)
        nhan_xet_he_thong = generate_nhan_xet_he_thong(sub, hk1_dtb, hk2_dtb, is_outstanding)
        
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
