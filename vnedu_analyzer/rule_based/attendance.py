def apply_template_engine(input_data):
    hk1_abs = input_data.get("hk1", {}).get("nghi_khong_phep", 0)
    hk2_abs = input_data.get("hk2", {}).get("nghi_khong_phep", 0)
    total_abs = input_data.get("ca_nam", {}).get("nghi_khong_phep", 0)
    
    if total_abs is None:
        total_abs = (hk1_abs or 0) + (hk2_abs or 0)
        
    canh_bao_chuyen_can = (total_abs >= 10)
    
    nhan_xet_chuyen_can = None
    if canh_bao_chuyen_can:
        if hk2_abs > 0 and hk1_abs == 0:
            hk_str = "học kỳ 2"
        elif hk1_abs > 0 and hk2_abs == 0:
            hk_str = "học kỳ 1"
        else:
            hk_str = "năm học"
        nhan_xet_chuyen_can = (
            f"Em có {total_abs} buổi nghỉ học không phép trong {hk_str}. "
            f"Việc vắng mặt thường xuyên có thể ảnh hưởng đến khả năng tiếp thu bài và kết quả kiểm tra. "
            f"Gia đình nên phối hợp chặt chẽ với giáo viên chủ nhiệm để theo dõi và hỗ trợ em."
        )
        
    attendance_awards = {
        "chuyen_can": {
            "nghi_co_phep_tong": input_data.get("ca_nam", {}).get("nghi_co_phep", 0),
            "nghi_khong_phep_tong": total_abs,
            "nghi_khong_phep_hk1": hk1_abs,
            "nghi_khong_phep_hk2": hk2_abs,
            "canh_bao_chuyen_can": canh_bao_chuyen_can,
            "nhan_xet_chuyen_can": nhan_xet_chuyen_can
        },
        "khen_thuong": []
    }
    return attendance_awards
