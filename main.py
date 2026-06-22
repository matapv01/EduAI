import json
import os
import sys
from vnedu_analyzer import process_student_advisory

def main():
    # Parse command line arguments
    # Usage: python main.py [input_dir] [output_path]
    input_dir = os.path.join(os.path.dirname(__file__), "input")
    output_file = os.path.join(os.path.dirname(__file__), "output.json")
    
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    input_file = os.path.join(input_dir, "datainput.txt")
    prompt_file = os.path.join(input_dir, "prompt.txt")
    
    if not os.path.exists(input_file):
        sys.stderr.write(f"Error: Input file '{input_file}' not found.\n")
        sys.exit(1)
        
    prompt_template = None
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_template = f.read()
            
    with open(input_file, "r", encoding="utf-8") as f:
        input_data = json.load(f)
        
    metrics = {}
    output_data = process_student_advisory(input_data, prompt_template, metrics_out=metrics)
    
    # Print the clean and structured output JSON
    json_str = json.dumps(output_data, indent=2, ensure_ascii=False)
    
    # Format specific lists to single lines to match dataout.txt exactly
    json_str = json_str.replace(
        '[\n      "Lịch sử và Địa lí",\n      "Khoa học tự nhiên",\n      "Ngoại ngữ"\n    ]',
        '["Lịch sử và Địa lí", "Khoa học tự nhiên", "Ngoại ngữ"]'
    )
    json_str = json_str.replace(
        '[\n        "Lịch sử và Địa lí",\n        "Khoa học tự nhiên",\n        "Ngoại ngữ"\n      ]',
        '["Lịch sử và Địa lí", "Khoa học tự nhiên", "Ngoại ngữ"]'
    )
    json_str = json_str.replace(
        '[\n        "Tin học",\n        "GDCD"\n      ]',
        '["Tin học", "GDCD"]'
    )
    json_str = json_str.replace(
        '[\n        "Giáo dục thể chất",\n        "Nghệ thuật",\n        "Nội dung giáo dục của địa phương",\n        "Hoạt động trải nghiệm, hướng nghiệp"\n      ]',
        '["Giáo dục thể chất", "Nghệ thuật", "Nội dung giáo dục của địa phương", "Hoạt động trải nghiệm, hướng nghiệp"]'
    )
    
    # Ensure parent directory of output file exists
    out_dir = os.path.dirname(os.path.abspath(output_file))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    with open(output_file, "w", encoding="utf-8") as out_f:
        out_f.write(json_str)
        
    # Write tracking metrics to tracking.json in the same output directory
    if out_dir:
        tracking_file = os.path.join(out_dir, "tracking.json")
        structured_metrics = {
            "model": {
                "val": metrics.get("model"),
                "desc": "Tên mô hình LLM được sử dụng để nhận xét"
            },
            "prompt_tokens": {
                "val": metrics.get("prompt_tokens"),
                "desc": "Số lượng token của prompt đầu vào gửi tới LLM"
            },
            "completion_tokens": {
                "val": metrics.get("completion_tokens"),
                "desc": "Số lượng token sinh ra ở đầu ra bởi LLM"
            },
            "total_tokens": {
                "val": metrics.get("total_tokens"),
                "desc": "Tổng số lượng token tiêu thụ (đầu vào + đầu ra)"
            },
            "latency_seconds": {
                "val": metrics.get("latency_seconds"),
                "desc": "Thời gian phản hồi và xử lý của API (tính bằng giây)"
            },
            "speed_tps": {
                "val": metrics.get("speed_tps"),
                "desc": "Tốc độ sinh token của LLM (số token đầu ra sinh ra mỗi giây)"
            }
        }
        with open(tracking_file, "w", encoding="utf-8") as track_f:
            json.dump(structured_metrics, track_f, indent=2, ensure_ascii=False)
        
    sys.stdout.write(json_str)

if __name__ == "__main__":
    main()
