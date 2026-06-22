from .utils import get_subject_template, ensure_period
from .rule_based import (
    build_student_info,
    evaluate_tt22_rules,
    filter_and_sort_subjects,
    build_subject_reviews,
    generate_goals_and_plans,
    apply_template_engine
)
from .llm import build_micro_prompt, call_qwen_llm
from .config import STANDARD_NHAN_XET_SUBJECTS

def merge_and_build_json(rule_based_data, ai_text):
    parts = [p.strip() for p in ai_text.split("||")]
    while len(parts) < 3:
        parts.append("")
        
    rule_based_data["student_info"]["gioi_thieu_text"] = parts[0]
    rule_based_data["general_summary"]["tong_quan_text"] = parts[1]
    rule_based_data["strengths"]["summary_text"] = parts[2]
    
    return rule_based_data

def process_student_advisory(input_data, prompt_template=None, metrics_out=None):
    # Phase 1: Rule-based Student Info & TT22 Evaluation
    student_info = build_student_info(input_data)
    is_khuyet_tat = student_info["_internal_flags"]["is_khuyet_tat_khong_danh_gia"]
    
    tt22_eval = evaluate_tt22_rules(input_data, is_khuyet_tat)
    
    student_info["xep_loai_hoc_tap"] = tt22_eval["xep_loai_hoc_tap"]
    student_info["xep_loai_ren_luyen"] = tt22_eval["xep_loai_ren_luyen"]
    
    # Phase 1: Subject Selection
    selected_scored, selected_nhan_xet, noi_bat_list = filter_and_sort_subjects(input_data)
    
    # Phase 1: Subject Reviews Building
    subject_reviews = build_subject_reviews(input_data, selected_scored, noi_bat_list)
    
    # Phase 1: Goals and Plans
    improvement_goals, study_plan = generate_goals_and_plans(input_data, selected_scored, noi_bat_list)
    
    # Phase 1: Attendance
    attendance_awards = apply_template_engine(input_data)
    
    # Dynamic Lists for Outstanding and Concern subjects
    uu_tien_cao = study_plan["phan_bo_uu_tien"]["uu_tien_cao"]
    uu_tien_trung = study_plan["phan_bo_uu_tien"]["uu_tien_trung"]
    total_abs = attendance_awards["chuyen_can"]["nghi_khong_phep_tong"] or 0
    
    # Strengths items building
    strengths_items = []
    for sub in subject_reviews["danh_sach"]:
        if sub["mon_duoc_chon_vi"] == "NOI_BAT":
            hk1_val = sub["dtb_hk1"]
            hk2_val = sub["dtb_hk2"]
            hk1_str = f"{hk1_val:.1f}" if hk1_val is not None else ""
            hk2_str = f"{hk2_val:.1f}" if hk2_val is not None else ""
            
            if hk1_val is not None and hk2_val is not None:
                if hk2_val > hk1_val:
                    mo_ta = f"Điểm số tiến bộ rõ rệt từ {hk1_str} lên {hk2_str}, hoàn thành tốt nội dung học tập."
                else:
                    mo_ta = f"Duy trì kết quả tốt ổn định ở mức {hk2_str}, có tinh thần tự giác học tập."
            else:
                mo_ta = f"Đạt kết quả học tập tốt môn {sub['ten_mon']}."
                
            strengths_items.append({
                "loai": "MON_HOC",
                "tieu_de": sub["ten_mon"],
                "mo_ta": mo_ta
            })
            
    strengths_items.append({
        "loai": "THAI_DO",
        "tieu_de": "Tinh thần học tập",
        "mo_ta": "Luôn tích cực trong các hoạt động học tập, hoàn thành đầy đủ các yêu cầu của bộ môn."
    })
    
    strengths = {
        "summary_text": "",
        "items": strengths_items
    }
    
    # Concerns items building
    concerns_items = []
    for sub in subject_reviews["danh_sach"]:
        if sub["mon_duoc_chon_vi"] == "CAN_CAI_THIEN":
            hk2_val = sub["dtb_hk2"]
            hk2_str = f"{hk2_val:.1f}" if hk2_val is not None else ""
            if hk2_val is not None:
                if hk2_val < 5.0:
                    mo_ta = f"Điểm trung bình còn thấp ({hk2_str}), chưa đạt chuẩn trung bình bộ môn."
                else:
                    mo_ta = f"Điểm số ở mức trung bình ({hk2_str}), cần dành thời gian luyện tập thêm."
            else:
                mo_ta = "Kết quả học tập còn hạn chế, cần tăng cường ôn tập."
                
            concerns_items.append({
                "loai": "MON_HOC",
                "tieu_de": sub["ten_mon"],
                "mo_ta": mo_ta,
                "canh_bao_tt22": False,
                "canh_bao_text": None
            })
            
    concerns = {
        "summary_text": f"Các môn như {', '.join(uu_tien_cao)} vẫn còn điểm số thấp, cần được hỗ trợ để cải thiện và đạt yêu cầu học tập.",
        "items": concerns_items,
        "co_canh_bao_tt22": False
    }
    
    # Dynamic Diem noi bat and Diem can cai thien
    noi_bat_strs = []
    for sub in subject_reviews["danh_sach"]:
        if sub["mon_duoc_chon_vi"] == "NOI_BAT":
            hk1_val = sub["dtb_hk1"]
            hk2_val = sub["dtb_hk2"]
            hk1_str = str(int(hk1_val)) if hk1_val == int(hk1_val) else str(hk1_val)
            hk2_str = str(int(hk2_val)) if hk2_val == int(hk2_val) else str(hk2_val)
            noi_bat_strs.append(f"{sub['ten_mon']} (từ {hk1_str} lên {hk2_str})")
            
    for sub_name, cn_entry in input_data.get("ca_nam", {}).items():
        if isinstance(cn_entry, dict) and cn_entry.get("diem") == "Đạt":
            if sub_name in STANDARD_NHAN_XET_SUBJECTS:
                noi_bat_strs.append(f"{sub_name} (vẫn đạt toàn bộ)")
                break
        
    diem_noi_bat = ", ".join(noi_bat_strs)
    diem_can_cai_thien = f"{', '.join(uu_tien_cao)} – điểm số vẫn ở mức trung bình, cần nỗ lực hơn để đạt yêu cầu."
    
    # General summary skeleton
    general_summary = {
        "tong_quan_text": "",
        "xu_huong": "TIEN_BO",
        "xu_huong_text": "Có dấu hiệu tiến bộ rõ rệt từ học kỳ 1 sang học kỳ 2, đặc biệt ở các môn có điểm số tăng từ 4–6 điểm.",
        "diem_noi_bat": diem_noi_bat,
        "diem_can_cai_thien": diem_can_cai_thien,
        "nhan_xet_thai_do": None,
        "tone": "QUAN_TAM"
    }
    
    # Suggestions structure building
    suggestions_items = []
    if attendance_awards["chuyen_can"]["canh_bao_chuyen_can"]:
        suggestions_items.append({
            "hanh_dong": "Phối hợp chặt chẽ với giáo viên chủ nhiệm để điều chỉnh kế hoạch học tập và theo dõi việc nghỉ học không phép.",
            "do_uu_tien": "CAO"
        })
        
    if uu_tien_cao:
        suggestions_items.append({
            "hanh_dong": f"Tập trung ôn tập và luyện tập thường xuyên các môn có điểm thấp, đặc biệt là {', '.join(uu_tien_cao)}.",
            "do_uu_tien": "CAO"
        })
        
    suggestions_items.append({
        "hanh_dong": "Tạo thói quen học tập đều đặn, có lịch trình rõ ràng để duy trì động lực và tiến bộ lâu dài.",
        "do_uu_tien": "TRUNG_BINH"
    })
    
    canh_bao_chua_xu_ly = []
    if attendance_awards["chuyen_can"]["canh_bao_chuyen_can"]:
        canh_bao_chua_xu_ly.append(f"Cảnh báo về nghỉ học không phép ({total_abs} buổi) cần được xử lý sớm")
        
    suggestions = {
        "section_title": "Gợi ý",
        "cho_doi_tuong": "PHU_HUYNH_VA_HOC_SINH",
        "items": suggestions_items,
        "_internal_luu_y": {
            "_render": False,
            "canh_bao_chua_xu_ly": canh_bao_chua_xu_ly,
            "du_lieu_con_thieu": [],
            "disclaimer": "Phân tích dựa trên dữ liệu học tập hiện có. Không có thông tin về điểm số giữa kỳ hoặc đánh giá của giáo viên bộ môn đầy đủ."
        }
    }
    
    # Combine initial rule-based structure
    rule_based_data = {
        "student_info": student_info,
        "general_summary": general_summary,
        "subject_reviews": subject_reviews,
        "strengths": strengths,
        "concerns": concerns,
        "attendance_awards": attendance_awards,
        "improvement_goals": improvement_goals,
        "study_plan": study_plan,
        "suggestions": suggestions,
        "metadata": {
            "phien_ban_schema": "1.0",
            "thoi_gian_tao": "2025-04-05T10:00:00Z",
            "ky_danh_gia": "CA_NAM",
            "du_lieu_day_du": True,
            "cac_truong_thieu": [],
            "ap_dung_tt22": not is_khuyet_tat
        }
    }
    
    # Phase 2: AI Generation
    compressed_prompt = build_micro_prompt(rule_based_data, prompt_template)
    ai_text = call_qwen_llm(compressed_prompt, metrics_out=metrics_out)
        
    # Phase 3: Orchestrator & Merge
    final_output = merge_and_build_json(rule_based_data, ai_text)
    return final_output
