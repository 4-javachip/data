import uuid
import random
from utils import get_random_datetime

def extract_review_data(product_uuid, review_list, user_list):
    """
    리뷰 목록에서 리뷰 및 이미지 데이터 분리
    - product_uuid는 상품 저장 후 반환값으로 받아옴
    """
    review_values = []
    review_image_values = []

    for review in review_list:
        review_uuid = str(uuid.uuid4())
        user_uuid = random.choice(user_list)
        rating = review.get("별점")
        content = review.get("리뷰내용")
        title = review.get("리뷰내용")[:5] + '...'
        created_at = get_random_datetime(within_days=20)
        updated_at = created_at
        deleted = False

        review_values.append(
            (review_uuid, product_uuid, user_uuid, rating, content, title, created_at, updated_at, deleted)
        )

        images = review.get("리뷰이미지url", [])
        if isinstance(images, list):
            for image_url in images:
                review_image_values.append((review_uuid, image_url, created_at, updated_at, deleted))

    return review_values, review_image_values


def insert_bulk_reviews_and_images(cursor, review_values, review_image_values):
    """리뷰와 이미지 일괄 삽입"""
    review_sql = """
        INSERT IGNORE INTO review 
        (review_uuid, product_uuid, user_uuid, rating, content, title, created_at, updated_at, deleted)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    review_image_sql = """
        INSERT IGNORE INTO review_image 
        (review_uuid, image_url, created_at, updated_at, deleted)
        VALUES (%s, %s, %s, %s, %s)
    """

    if review_values:
        cursor.executemany(review_sql, review_values)
    if review_image_values:
        cursor.executemany(review_image_sql, review_image_values)
