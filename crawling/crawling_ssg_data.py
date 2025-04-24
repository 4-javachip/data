import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from get_product_info import get_product_info
import winsound
import gc

# 카테고리별로 itemId 추출 (특정 범위에 대해서만)
def extract_limited_items_within_range(data, start, end, limit=999999):
    results = []
    def recursive(d, path=[], indexes=[]):
        if isinstance(d, dict):
            for i, (k, v) in enumerate(d.items()):
                new_indexes = indexes + [i]
                if len(new_indexes) == len(start) and not (start <= new_indexes <= end):
                    continue
                recursive(v, path + [k], new_indexes)
        elif isinstance(d, list):
            if start <= indexes <= end:
                for itemId in d[:limit]:
                    results.append((path, indexes, itemId))
    recursive(data)
    return results

# 파일명 생성 (예: 0_1_2.json)
def index_filename(indexes):
    return "_".join(str(i) for i in indexes)

# 실행부
if __name__ == "__main__":
    with open("./ids/ids.json", "r", encoding="utf-8") as f:
        ids_data = json.load(f)

    START = [0, 0, 0]
    END = [0, 0, 0]
    full_list = extract_limited_items_within_range(ids_data, START, END, limit=999999)

    category_map = {}
    for categories, indexes, itemId in full_list:
        key = tuple(indexes)
        if key not in category_map:
            category_map[key] = []
        category_map[key].append((categories, indexes, itemId))

    Path("output").mkdir(exist_ok=True)

    total_count = 0

    for indexes, item_list in category_map.items():
        results = []
        skipped_ids = []
        print(f"\n🚀 시작: 카테고리 {indexes}, 총 {len(item_list)}개")

        # ✅ 병렬 처리
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_item = {
                executor.submit(get_product_info, itemId): (categories, itemId)
                for categories, _, itemId in item_list
            }

            for future in as_completed(future_to_item):
                categories, itemId = future_to_item[future]
                try:
                    data = future.result(timeout=20)

                    if not data["제품명"].strip():
                        print(f"⚠️ 스킵: {itemId} – 제품명 없음")
                        skipped_ids.append(itemId)
                        continue

                    data["카테고리"] = categories
                    results.append(data)
                    total_count += 1
                    print(f"✅ 완료: {itemId} | 누적 저장: {total_count}개")
                    time.sleep(0.3)  # 요청 간격 조정
                except Exception as e:
                    print(f"❌ 실패: {itemId} – {e}")
                    skipped_ids.append(itemId)

        file_key = index_filename(indexes)
        save_path = f"output/{file_key}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 저장 완료: {save_path}")

        if skipped_ids:
            skipped_path = f"output/{file_key}_skipped.json"
            with open(skipped_path, "w", encoding="utf-8") as f:
                json.dump(skipped_ids, f, ensure_ascii=False, indent=2)
            print(f"⚠️ 스킵된 ID 저장 완료: {skipped_path}")

        # ✅ 메모리 정리
        del future_to_item
        del executor
        del results
        del skipped_ids
        gc.collect()

    winsound.Beep(1000, 500)
