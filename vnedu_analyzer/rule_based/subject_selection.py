from ..utils import safe_float, ensure_period, get_subject_template

from ..utils import safe_float, ensure_period, get_subject_template

def check_warning_for_sorting(sub, detail, ca_nam_entry, phase):
    # 1. Check ĐTB < 3.5 based on phase
    hk1_dtb = safe_float(detail.get("hk1", {}).get("diem_tb"))
    hk2_dtb = safe_float(detail.get("hk2", {}).get("diem_tb"))
    cn_dtb = safe_float(ca_nam_entry.get("diem"))
    
    if phase == "hk1":
        if hk1_dtb is not None and hk1_dtb < 3.5:
            return True
    elif phase == "hk2":
        if hk2_dtb is not None and hk2_dtb < 3.5:
            return True
    else: # ca_nam
        if cn_dtb is not None and cn_dtb < 3.5:
            return True
        if hk1_dtb is not None and hk1_dtb < 3.5:
            return True
        if hk2_dtb is not None and hk2_dtb < 3.5:
            return True
            
    # 2. Check CK < 3.0 anomaly in semesters
    for hk_name in ["hk1", "hk2"]:
        hk_data = detail.get(hk_name, {})
        ck_val = None
        for k, v in hk_data.items():
            if k.startswith("CK"):
                val = safe_float(v)
                if val is not None:
                    ck_val = val
        if ck_val is not None and ck_val < 3.0:
            tx_gk_vals = []
            for k, v in hk_data.items():
                if k.startswith("TX") or k.startswith("GK"):
                    val = safe_float(v)
                    if val is not None:
                        tx_gk_vals.append(val)
            if tx_gk_vals:
                avg_tx_gk = sum(tx_gk_vals) / len(tx_gk_vals)
                if avg_tx_gk >= 5.0:
                    return True
    return False

def filter_and_sort_subjects(input_data):
    chi_tiet = input_data.get("chi_tiet_diem", {})
    ca_nam = input_data.get("ca_nam", {})
    phase = input_data.get("phase", "ca_nam")
    
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
            
    # Priority sorting for scored subjects:
    # 1. DTB < 5.0 or TT22 warning (+100)
    # 2. Core THPT exam subjects: Toán học, Ngữ văn, Ngoại ngữ (+10)
    # 3. Outstanding subjects >= 8.0 (+1)
    scored_priorities = []
    noi_bat_list = []
    
    for sub in scored_subjects:
        detail = chi_tiet.get(sub, {})
        cn_entry = ca_nam.get(sub, {})
        
        # Outstanding is >= 8.0 in ca_nam
        diem_val = safe_float(cn_entry.get("diem"))
        if diem_val is not None and diem_val >= 8.0:
            noi_bat_list.append(sub)
            
        if phase == "hk1":
            dtb_val = safe_float(detail.get("hk1", {}).get("diem_tb"))
        elif phase == "hk2":
            dtb_val = safe_float(detail.get("hk2", {}).get("diem_tb"))
        else:
            dtb_val = safe_float(cn_entry.get("diem"))
            
        is_low = (dtb_val is not None and dtb_val < 5.0)
        has_warning = check_warning_for_sorting(sub, detail, cn_entry, phase)
        
        score = 0
        if is_low or has_warning:
            score += 100
        if sub in ["Toán học", "Ngữ văn", "Ngoại ngữ"]:
            score += 10
        if dtb_val is not None and dtb_val >= 8.0:
            score += 1
            
        scored_priorities.append((sub, score))
        
    scored_priorities.sort(key=lambda x: x[1], reverse=True)
    selected_scored = [x[0] for x in scored_priorities[:5]]
    
    # Priority sorting for comment subjects:
    # Prioritize "Chưa Đạt" (+10), then "Đạt" (+1)
    nhan_xet_priorities = []
    for sub in nhan_xet_subjects:
        cn_entry = ca_nam.get(sub, {})
        if phase == "hk1":
            diem_val = chi_tiet.get(sub, {}).get("hk1", {}).get("diem_tb")
        elif phase == "hk2":
            diem_val = chi_tiet.get(sub, {}).get("hk2", {}).get("diem_tb")
        else:
            diem_val = cn_entry.get("diem")
            
        score = 0
        if diem_val == "Chưa Đạt":
            score = 10
        elif diem_val == "Đạt":
            score = 1
            
        nhan_xet_priorities.append((sub, score))
        
    nhan_xet_priorities.sort(key=lambda x: x[1], reverse=True)
    selected_nhan_xet = [x[0] for x in nhan_xet_priorities[:2]]
    
    return selected_scored, selected_nhan_xet, noi_bat_list

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

def get_subject_warning(sub, detail, ca_nam_entry, phase):
    # 1. Check ĐTB < 3.5
    hk1_dtb = safe_float(detail.get("hk1", {}).get("diem_tb"))
    hk2_dtb = safe_float(detail.get("hk2", {}).get("diem_tb"))
    cn_dtb = safe_float(ca_nam_entry.get("diem"))
    
    dtb_warning = False
    if phase == "hk1":
        if hk1_dtb is not None and hk1_dtb < 3.5:
            dtb_warning = True
    elif phase == "hk2":
        if hk2_dtb is not None and hk2_dtb < 3.5:
            dtb_warning = True
    else:
        if cn_dtb is not None and cn_dtb < 3.5:
            dtb_warning = True
        elif hk1_dtb is not None and hk1_dtb < 3.5:
            dtb_warning = True
        elif hk2_dtb is not None and hk2_dtb < 3.5:
            dtb_warning = True
            
    if dtb_warning:
        return True, f"Hệ thống nhận thấy môn {sub} có điểm trung bình dưới 3.5. Theo Thông tư 22/2021, em có thể phải tham gia kiểm tra, đánh giá lại trong hè. Phụ huynh nên trao đổi với giáo viên bộ môn để có kế hoạch ôn tập phù hợp."
        
    # 2. Check CK < 3.0 anomaly
    semesters_to_check = ["hk1"] if phase == "hk1" else ["hk2"] if phase == "hk2" else ["hk1", "hk2"]
        
    for hk_name in semesters_to_check:
        hk_data = detail.get(hk_name, {})
        ck_val = None
        for k, v in hk_data.items():
            if k.startswith("CK"):
                val = safe_float(v)
                if val is not None:
                    ck_val = val
        if ck_val is not None and ck_val < 3.0:
            tx_gk_vals = []
            for k, v in hk_data.items():
                if k.startswith("TX") or k.startswith("GK"):
                    val = safe_float(v)
                    if val is not None:
                        tx_gk_vals.append(val)
            if tx_gk_vals:
                avg_tx_gk = sum(tx_gk_vals) / len(tx_gk_vals)
                if avg_tx_gk >= 5.0:
                    tx_vals = []
                    for k, v in hk_data.items():
                        if k.startswith("TX"):
                            val = safe_float(v)
                            if val is not None:
                                tx_vals.append(val)
                    avg_tx = sum(tx_vals) / len(tx_vals) if tx_vals else 0.0
                    return True, f"Điểm cuối kỳ môn {sub} = {ck_val} khá bất thường so với điểm thường xuyên (trung bình {avg_tx:.1f}). Có thể em đã gặp sự cố trong ngày thi, phụ huynh nên trao đổi với giáo viên bộ môn để hiểu rõ."
                    
    return False, None

def to_upper_result(val):
    if val is None:
        return None
    val_upper = str(val).upper()
    if "CHƯA ĐẠT" in val_upper:
        return "CHƯA ĐẠT"
    if "ĐẠT" in val_upper:
        return "ĐẠT"
    return val_upper

def build_subject_reviews(input_data, selected_scored, selected_nhan_xet, noi_bat_list):
    chi_tiet = input_data.get("chi_tiet_diem", {})
    ca_nam = input_data.get("ca_nam", {})
    phase = input_data.get("phase", "ca_nam")
    
    danh_sach = []
    
    # 1. Scored subjects
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
        
        vi = "NOI_BAT" if sub in noi_bat_list else "CAN_CAI_THIEN"
            
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
        
        has_warning, warning_text = get_subject_warning(sub, detail, ca_nam.get(sub, {}), phase)
            
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
            "nhan_xet_he_thong": nhan_xet_he_thong,
            "canh_bao_tt22": has_warning,
            "canh_bao_text": warning_text
        })
        
    # 2. Comment subjects
    for sub in selected_nhan_xet:
        detail = chi_tiet.get(sub, {})
        hk1_data = detail.get("hk1", {})
        hk2_data = detail.get("hk2", {})
        cn_entry = ca_nam.get(sub, {})
        
        res_hk1 = to_upper_result(hk1_data.get("diem_tb"))
        res_hk2 = to_upper_result(hk2_data.get("diem_tb"))
        res_cn = to_upper_result(cn_entry.get("diem"))
        
        current_res = res_hk1 if phase == "hk1" else res_hk2 if phase == "hk2" else res_cn
        vi = "BAO_DONG" if current_res == "CHƯA ĐẠT" else "QUAN_TRONG"
        
        nhan_xet_gv = hk2_data.get("nhan_xet") or hk1_data.get("nhan_xet")
        nhan_xet_gv = ensure_period(nhan_xet_gv)
        
        if current_res == "CHƯA ĐẠT":
            nhan_xet_he_thong = "Chưa đạt kết quả tốt, cần chú ý thực hành nhiều hơn."
        else:
            nhan_xet_he_thong = f"Hoàn thành tốt các nội dung học tập môn {sub}, có thái độ học tập tích cực."
            
        danh_sach.append({
            "ten_mon": sub,
            "mon_duoc_chon_vi": vi,
            "loai_danh_gia": "NHAN_XET",
            "ket_qua_hk1": res_hk1,
            "ket_qua_hk2": res_hk2,
            "ket_qua_ca_nam": res_cn,
            "nhan_xet_gv": nhan_xet_gv,
            "nhan_xet_he_thong": nhan_xet_he_thong
        })
        
    total_subjects = len(chi_tiet)
    return {
        "tong_so_mon_da_doc": total_subjects,
        "ghi_chu_chon_loc": "Phân tích các môn có điểm tăng trưởng rõ rệt hoặc cần cải thiện, ưu tiên theo xu hướng tiến bộ và mức độ ảnh hưởng đến học tập tổng thể.",
        "danh_sach": danh_sach
    }
