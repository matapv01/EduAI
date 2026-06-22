def build_micro_prompt(rule_based_data, prompt_template=None):
    info = rule_based_data.get("student_info", {})
    flags = info.get("_internal_flags", {}) or {}
    reviews = rule_based_data.get("subject_reviews", {}).get("danh_sach", [])
    chuyen_can = rule_based_data.get("attendance_awards", {}).get("chuyen_can", {})
    
    # 1. Outstanding subjects
    noi_bat_list = []
    for sub in reviews:
        if sub.get("mon_duoc_chon_vi") == "NOI_BAT":
            hk1 = sub.get("dtb_hk1")
            hk2 = sub.get("dtb_hk2")
            if hk1 is not None and hk2 is not None:
                noi_bat_list.append(f"{sub.get('ten_mon')} ({hk1} -> {hk2})")
            else:
                noi_bat_list.append(sub.get("ten_mon"))
                
    # 2. Concern subjects
    can_cai_thien_list = []
    for sub in reviews:
        if sub.get("mon_duoc_chon_vi") in ["CAN_CAI_THIEN", "BAO_DONG"]:
            can_cai_thien_list.append(sub.get("ten_mon"))
            
    # 3. Absences
    nghi_khong_phep = chuyen_can.get("nghi_khong_phep_tong", 0)
    abs_str = ""
    if nghi_khong_phep and nghi_khong_phep > 0:
        hk1_abs = chuyen_can.get("nghi_khong_phep_hk1", 0)
        hk2_abs = chuyen_can.get("nghi_khong_phep_hk2", 0)
        if hk2_abs > 0 and hk1_abs == 0:
            hk_str = "học kỳ 2"
        elif hk1_abs > 0 and hk2_abs == 0:
            hk_str = "học kỳ 1"
        else:
            hk_str = "năm học"
        abs_str = f"Nghỉ không phép {nghi_khong_phep} buổi ở {hk_str}"
        
    # Construct dynamic data description block
    data_summary = f"- Khối: {info.get('khoi')}\n"
    data_summary += f"- Trường: {info.get('truong')}\n"
    if flags.get("dien_chinh_sach"):
        data_summary += f"- Diện chính sách: {flags.get('dien_chinh_sach')}\n"
    if flags.get("khu_vuc"):
        data_summary += f"- Khu vực: {flags.get('khu_vuc')}\n"
    if noi_bat_list:
        data_summary += f"- Tiến bộ/Nổi bật: {', '.join(noi_bat_list)}\n"
    if can_cai_thien_list:
        data_summary += f"- Môn cần cải thiện: {', '.join(can_cai_thien_list)}\n"
    if abs_str:
        data_summary += f"- Chuyên cần: {abs_str}\n"
        
    if prompt_template:
        return f"{prompt_template}\n{data_summary}"
        
    # Fallback to general system instructions if no template is provided
    prompt = (
        "Bạn là TRỢ LÝ TƯ VẤN HỌC TẬP của VnEdu. Dựa trên dữ liệu học tập đã qua xử lý rule-based dưới đây, hãy viết đúng 3 câu nhận xét tiếng Việt ngắn gọn, xúc tích, ngăn cách nhau bởi ký tự '||' (không dùng nhân xưng Cô/Thầy, chỉ dùng 'Em' hoặc 'Học sinh'):\n"
        "- Câu 1: Giới thiệu nỗ lực học tập của em vượt qua hoàn cảnh khó khăn (nếu có diện chính sách hoặc khu vực khó khăn).\n"
        "- Câu 2: Nhận xét tổng quan tình hình học tập và sự cố gắng rõ rệt ở kỳ 2.\n"
        "- Câu 3: Nêu bật các điểm mạnh môn học (dựa trên các môn học nổi bật).\n\n"
        f"Dữ liệu học sinh:\n{data_summary}"
    )
    return prompt
