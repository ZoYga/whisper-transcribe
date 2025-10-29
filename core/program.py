# core/program.py
import os
import whisper

def transcribe_audio(file_path: str, model_name: str) -> dict:
    try:
        model = whisper.load_model(model_name)  # ← передаём имя "как есть"
        result = model.transcribe(file_path)
        return {"success": True, "text": result["text"]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_transcription(text: str, original_file_path: str, output_dir: str = "transcriptions") -> str:
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(original_file_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_transcription.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return output_path