def build_student_info(input_data):
    is_khuyet_tat = input_data.get("IS_KHUYET_TAT_KHONG_DANH_GIA") == "Có"
    dien_chinh_sach = input_data.get("DIEN_CHINH_SACH")
    khu_vuc = input_data.get("KHU_VUC")
    
    ho_ten = input_data.get("ho_ten", "string")
    lop = input_data.get("lop", "string")
    
    khoi_raw = input_data.get("MA_KHOI", 9)
    try:
        khoi = int(khoi_raw)
    except:
        khoi = 9
        
    nam_hoc = input_data.get("NAM_HOC")
    truong = input_data.get("TEN_TRUONG")
    
    student_info = {
        "_internal_flags": {
            "is_khuyet_tat_khong_danh_gia": is_khuyet_tat,
            "dien_chinh_sach": dien_chinh_sach,
            "khu_vuc": khu_vuc
        },
        "gioi_thieu_text": "",
        "ho_ten": ho_ten,
        "lop": lop,
        "khoi": khoi,
        "nam_hoc": nam_hoc,
        "truong": truong,
        "xep_loai_hoc_tap": None,
        "xep_loai_ren_luyen": None,
        "thu_hang_lop": None,
        "si_so_lop": None
    }
    return student_info
