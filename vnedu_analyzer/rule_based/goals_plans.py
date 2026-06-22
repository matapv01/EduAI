from ..utils import safe_float, get_subject_template

def get_subject_plan_details(sub, current_score):
    score = safe_float(current_score)
    if score is None:
        score = 6.0
        
    if score < 5.0:
        return {
            "gio_tuan": 2.0,
            "noi_dung_tap_trung": [
                "Hệ thống hóa lại các kiến thức cơ bản chưa nắm vững",
                "Làm các bài tập cơ bản SGK và bài tập củng cố",
                "Trao đổi với thầy cô và các bạn để giải đáp thắc mắc"
            ],
            "ghi_chu": "Cần ưu tiên dành nhiều thời gian hơn để lấy lại kiến thức căn bản môn học."
        }
    elif score >= 8.0:
        return {
            "gio_tuan": 1.0,
            "noi_dung_tap_trung": [
                "Luyện tập các dạng bài nâng cao và chuyên sâu",
                "Chia sẻ và hỗ trợ các bạn cùng tiến bộ",
                "Tìm hiểu thêm các tài liệu học tập mở rộng"
            ],
            "ghi_chu": "Duy trì phong độ học tập tốt và phát huy năng lực tự học."
        }
    else:
        return {
            "gio_tuan": 1.5,
            "noi_dung_tap_trung": [
                "Luyện tập các bài tập tổng hợp và đề tự luyện",
                "Hệ thống hóa kiến thức trọng tâm theo chương/chủ đề",
                "Xem lại các lỗi sai trong các bài kiểm tra trước"
            ],
            "ghi_chu": "Duy trì nỗ lực đều đặn để cải thiện và ổn định điểm số môn học."
        }

def generate_goals_and_plans(input_data, selected_scored, noi_bat_list):
    ca_nam = input_data.get("ca_nam", {})
    
    # Identify warning/concern and outstanding subjects dynamically
    uu_tien_cao = []
    uu_tien_trung = []
    
    for sub in selected_scored:
        cn_entry = ca_nam.get(sub, {})
        diem_val = safe_float(cn_entry.get("diem"))
        
        # Checking if it was categorized as CAN_CAI_THIEN dynamically
        if sub not in noi_bat_list:
            uu_tien_cao.append(sub)
        else:
            uu_tien_trung.append(sub)
            
    # Nhận xét subjects in input are prioritized as duy_tri
    duy_tri = []
    for k, v in ca_nam.items():
        if isinstance(v, dict) and v.get("diem") in ["Đạt", "Chưa Đạt"]:
            duy_tri.append(k)
            
    # Parse co_muc_tieu_tu_dat
    has_muc_tieu = False
    for k, v in ca_nam.items():
        if isinstance(v, dict) and "diem_muc_tieu" in v:
            has_muc_tieu = True
            break
            
    goals_items = []
    for sub in uu_tien_cao:
        cn_entry = ca_nam.get(sub, {})
        diem_hien_tai = safe_float(cn_entry.get("diem"))
        diem_muc_tieu = safe_float(cn_entry.get("diem_muc_tieu"))
        
        if diem_muc_tieu is None:
            if diem_hien_tai is not None:
                if diem_hien_tai < 5.0:
                    diem_muc_tieu = min(diem_hien_tai + 2.0, 6.0)
                elif diem_hien_tai < 6.5:
                    diem_muc_tieu = min(diem_hien_tai + 1.5, 7.5)
                elif diem_hien_tai < 8.0:
                    diem_muc_tieu = min(diem_hien_tai + 0.5, 8.5)
                else:
                    diem_muc_tieu = min(diem_hien_tai + 0.3, 10.0)
                diem_muc_tieu = round(diem_muc_tieu * 2) / 2.0
                
        goals_items.append({
            "ten_mon": sub,
            "diem_hien_tai": diem_hien_tai,
            "diem_muc_tieu": diem_muc_tieu,
            "muc_do_uu_tien": "CAO"
        })
        
    improvement_goals = {
        "summary_text": f"Học sinh cần tập trung cải thiện điểm số ở các môn có điểm thấp, đặc biệt là {', '.join(uu_tien_cao)} để đạt yêu cầu học tập.",
        "co_muc_tieu_tu_dat": has_muc_tieu,
        "items": goals_items
    }
    
    # Detailed study plan includes all uu_tien_cao + top of uu_tien_trung
    ke_hoach_chi_tiet = []
    plan_subs = list(uu_tien_cao)
    if uu_tien_trung:
        plan_subs.append(uu_tien_trung[0]) # Add first outstanding subject
        
    for sub in plan_subs:
        cn_entry = ca_nam.get(sub, {})
        score = safe_float(cn_entry.get("diem"))
        details = get_subject_plan_details(sub, score)
        ke_hoach_chi_tiet.append({
            "ten_mon": sub,
            "gio_tuan": details["gio_tuan"],
            "noi_dung_tap_trung": details["noi_dung_tap_trung"],
            "ghi_chu": details["ghi_chu"]
        })
        
    study_plan = {
        "section_title": "Kế hoạch học tập",
        "loai_ke_hoach": "THEO_GIO_TUAN",
        "ghi_chu_chung": "Tập trung vào các môn có điểm thấp để cải thiện kết quả học tập, đồng thời duy trì sự cố gắng trong các môn đã có tiến bộ.",
        "tong_gio_tuan": 10,
        "phan_bo_uu_tien": {
            "uu_tien_cao": uu_tien_cao,
            "uu_tien_trung": uu_tien_trung,
            "duy_tri": duy_tri
        },
        "ke_hoach_chi_tiet": ke_hoach_chi_tiet,
        "mon_nhan_xet_chua_dat": [],
        "dinh_huong_giai_doan_tiep": {
            "giai_doan": "HK_SAU",
            "nhan_dinh_chung": "Học sinh có tiềm năng phát triển tốt, cần tiếp tục nỗ lực để đạt điểm số ổn định và đạt yêu cầu học tập.",
            "muc_tieu_xep_loai": "ĐẠT",
            "mon_tap_trung": uu_tien_cao,
            "lop_cuoi_cap": {
                "ap_dung": False,
                "loai": "null",
                "noi_dung_them": None
            },
            "ca_nhan_hoa": {
                "diem_manh_noi_bat": ", ".join(uu_tien_trung),
                "dinh_huong_khoi_nganh_goi_y": None,
                "muc_tieu_truong_cu_the": None,
                "luu_y_rieng": "Học sinh cần duy trì tinh thần học tập và cải thiện các môn còn yếu."
            },
            "dinh_huong_text": f"Học sinh đang có sự tiến bộ rõ rệt, cần tiếp tục nỗ lực để đạt điểm số ổn định và đạt yêu cầu học tập. Các môn còn yếu cần được cải thiện để đảm bảo kết quả học tập tổng thể đạt mức ĐẠT trong học kỳ tới."
        }
    }
    
    return improvement_goals, study_plan
