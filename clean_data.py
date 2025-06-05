import re
import pandas as pd

# Làm sạch tên sản phẩm
def clean_product_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'style\s?[a-z0-9\-]+', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'[,\-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# Lấy đúng dòng sau "Fabric type"
def extract_fabric_type(details: str) -> str:
    lines = details.lower().splitlines()
    for i, line in enumerate(lines):
        if "fabric type" in line:
            if i + 1 < len(lines):
                return lines[i + 1].strip()
    return ""

# Tiền xử lý từng dòng
def preprocess_row(row):
    # Xử lý giá
    prices = re.findall(r"\d+\.\d+", str(row["Price"]))
    min_price = float(prices[0]) if prices else None
    max_price = float(prices[1]) if len(prices) > 1 else min_price

    # Mô tả chỉ là phần sau "Fabric type"
    fabric_info = extract_fabric_type(str(row["Details"]))

    # Làm sạch tên sản phẩm
    raw_name = row.get("Name", "")
    cleaned_name = clean_product_name(raw_name) if raw_name else "unknown product"

    return {
        "product_name": cleaned_name,
        "min_price": min_price,
        "max_price": max_price,
        "rating": float(row["Rating"]),
        "description": fabric_info,
        "image_url": row["Image"],
        "product_link": row["Link"]
    }

# Đọc file CSV gốc
df = pd.read_csv("E:\\VSCSTD\\DSP\\amazon_products_detailed_test10.csv")

# Áp dụng xử lý
processed_data = df.apply(preprocess_row, axis=1)
processed_df = pd.DataFrame(processed_data.tolist())

# Ghi file ra CSV
processed_df.to_csv("fashion_data_clean.csv", index=False)
