import os
import json
import urllib.request
import time
import sys
from ..utils import load_dotenv

def calculate_token_and_speed(prompt_text, response_text, latency_seconds, api_usage=None):
    """
    Tính toán số lượng token đã nhận vào (prompt) và sinh ra (completion),
    cùng với đo tốc độ sinh token (tokens/second) và latency.
    """
    if api_usage and isinstance(api_usage, dict):
        prompt_tokens = api_usage.get("prompt_tokens", 0)
        completion_tokens = api_usage.get("completion_tokens", 0)
        total_tokens = api_usage.get("total_tokens", 0)
    else:
        def estimate_tokens(text):
            if not text:
                return 0
            return int(len(text.split()) * 1.3) + 1
            
        prompt_tokens = estimate_tokens(prompt_text)
        completion_tokens = estimate_tokens(response_text)
        total_tokens = prompt_tokens + completion_tokens
        
    speed_tps = completion_tokens / latency_seconds if latency_seconds > 0 else 0.0
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_seconds": latency_seconds,
        "speed_tps": speed_tps
    }

def report_llm_performance(model_name, usage_dict, latency_seconds, prompt_text=None, response_text=None):
    metrics = calculate_token_and_speed(prompt_text, response_text, latency_seconds, usage_dict)
    
    sys.stderr.write(
        f"\n=== LLM Performance Metrics ===\n"
        f"Model: {model_name}\n"
        f"Prompt Tokens: {metrics['prompt_tokens']}\n"
        f"Completion Tokens: {metrics['completion_tokens']}\n"
        f"Total Tokens: {metrics['total_tokens']}\n"
        f"Latency: {metrics['latency_seconds']:.3f} seconds\n"
        f"Speed: {metrics['speed_tps']:.2f} tokens/second\n"
        f"================================\n\n"
    )
    
    return {
        "model": model_name,
        **metrics
    }

def call_qwen_llm(compressed_prompt, metrics_out=None):
    load_dotenv()
    
    # Read from environment
    nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
    nvidia_model = os.environ.get("NVIDIA_MODEL")
    
    model = nvidia_model or os.environ.get("MODEL") or os.environ.get("QWEN_MODEL")
    api_key = nvidia_api_key or os.environ.get("API_KEY") or os.environ.get("QWEN_API_KEY")
    endpoint_url = os.environ.get("ENDPOINT_URL") or os.environ.get("QWEN_ENDPOINT_URL") or os.environ.get("NVIDIA_ENDPOINT_URL")
    
    # If using NVIDIA and endpoint is not specified, use the standard integrate.api.nvidia.com
    if nvidia_api_key and not endpoint_url:
        endpoint_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
    if not api_key:
        raise ValueError("Missing LLM API Key (NVIDIA_API_KEY / QWEN_API_KEY)")
    if not model:
        raise ValueError("Missing LLM Model (NVIDIA_MODEL / MODEL)")
    if not endpoint_url:
        raise ValueError("Missing LLM Endpoint URL")
        
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": compressed_prompt}
        ],
        "temperature": 0.1
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    start_time = time.time()
    try:
        req = urllib.request.Request(
            endpoint_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            end_time = time.time()
            
            content = res_data["choices"][0]["message"]["content"]
            usage = res_data.get("usage", {})
            
            # Record and display speed and token usage statistics
            metrics = report_llm_performance(model, usage, end_time - start_time, compressed_prompt, content)
            if isinstance(metrics_out, dict):
                metrics_out.update(metrics)
            
            return content
    except Exception as e:
        raise RuntimeError(f"LLM API Call failed: {e}")
