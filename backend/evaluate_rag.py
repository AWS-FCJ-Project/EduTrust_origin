import os
import json
from dotenv import load_dotenv

# Load môi trường
load_dotenv()

# Cấu hình workspace
os.environ["OPIK_WORKSPACE"] = os.getenv("OPIK_WORKSPACE", "thanh-nguy-n-1461")

import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import AnswerRelevance, Hallucination

# Import hệ thống RAG
from src.rag import vector_store, llm_client

def main():
    if not os.environ.get("OPIK_API_KEY"):
        print("Vui lòng thêm OPIK_API_KEY vào file .env trong thư mục backend để chạy!")
        return

    # Khởi tạo các thành phần RAG
    print("Khởi tạo RAG System...")
    store = vector_store.VectorStore()
    store.load_or_skip() # Tải index hiện có nếu có
    
    # Bắt buộc load model lên RAM/VRAM ở luồng chính (Main Thread)
    # Nếu để load tự động trong hàm đánh giá (qua đa luồng) sẽ gây lỗi meta tensor của PyTorch
    print("Warming up models (Loading to GPU/CPU)...")
    _ = store.embed_model
    _ = store.reranker
    
    llm = llm_client.LLMClient()

    local_results = []

    # Định nghĩa task RAG sẽ được Opik gọi để lấy output
    def evaluate_rag_task(item):
        question = item["question"]
        
        # 1. Retrieve context
        contexts = store.retrieve(question)
        
        # 2. Sinh câu trả lời
        answer = llm.generate_answer(question, contexts)
        
        # 3. Trả về format chuẩn cho Opik evaluate
        result = {
            "input": question,
            "output": answer,
            "context": contexts
        }
        
        if "expected_output" in item:
            result["expected_output"] = item["expected_output"]
            
        # 4. Lưu lại kết quả xuống file local JSON
        local_results.append({
            "question": question,
            "expected_output": item.get("expected_output", "N/A"),
            "rag_answer": answer,
            "retrieved_contexts": contexts
        })

        return result

    # Đọc dataset từ file JSON
    dataset_file = "test_dataset.json"
    if not os.path.exists(dataset_file):
        print(f"Lỗi: Không tìm thấy file dataset '{dataset_file}'")
        return
        
    with open(dataset_file, "r", encoding="utf-8") as f:
        dataset_records = json.load(f)

    print("Bỏ dữ liệu vào Opik Dataset...")
    client = opik.Opik()
    dataset_name = "Demo Dataset"
    try:
        # Xóa dataset cũ nếu tồn tại để cập nhật câu hỏi mới
        client.delete_dataset(name=dataset_name)
    except Exception:
        pass
    
    # Tạo dataset mới trên Opik và insert mẫu
    opik_dataset = client.get_or_create_dataset(name=dataset_name)
    opik_dataset.insert(dataset_records)

    print("Bắt đầu đánh giá với Opik...")
    
    # Khởi tạo các bộ chấm điểm
    answer_relevance_metric = AnswerRelevance()
    hallucination_metric = Hallucination()
    
    metrics = [answer_relevance_metric, hallucination_metric]

    # Chạy quy trình đánh giá
    evaluate(
        dataset=opik_dataset,
        task=evaluate_rag_task,
        scoring_metrics=metrics,
        experiment_name="Demo-RAG-Eval",
        task_threads=1 # Bắt buộc là 1 khi dùng PyTorch local model để tránh lỗi Meta Tensor
    )
    
    # Ghi ra file JSON
    output_file = "rag_evaluation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(local_results, f, ensure_ascii=False, indent=4)

    print("\n--- ĐÁNH GIÁ HOÀN TẤT ---")
    print("1. Dashboard: Kết quả dạng bảng (so sánh & điểm số) đã tự động đẩy lên Comet Opik Dashboard.")
    print(f"2. Local File: Dữ liệu câu trả lời (Câu hỏi, RAG trả lời, Đáp án chuẩn...) đã được lưu tại: {output_file}")

if __name__ == "__main__":
    main()
