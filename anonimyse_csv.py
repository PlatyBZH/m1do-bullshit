#!/usr/bin/env python3
"""
Robust pseudonymisation for USER_TABLE.csv and TRANSACTION_DATA.csv.

Usage:
    python anonymize_csv.py USER_TABLE.csv TRANSACTION_DATA.csv \
        anonymized_users.csv anonymized_transactions.csv
"""
import hashlib
import sys
import re
import csv
from typing import Dict, List

SECRET_SALT = "votre_sel_secret_très_long_et_aléatoire_2026"
MAX_GPS_NOISE_DEG = 0.5  # degrees

def sha256_hex(val: str) -> str:
    return hashlib.sha256((val + SECRET_SALT).encode("utf-8")).hexdigest()

def pseudonymize_identifier(orig: str, prefix: str = "id") -> str:
    return f"{prefix}_{sha256_hex(str(orig))[:12]}"

def mask_phone(phone: str) -> str:
    if not phone:
        return phone
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 4:
        return "***" + digits
    return "***-***-" + digits[-4:]

def pseudonymize_email(email: str) -> str:
    if not email or "@" not in email:
        return sha256_hex(str(email))[:12]
    local, domain = email.split("@", 1)
    local_hash = sha256_hex(local)[:12]
    return f"{local_hash}@{domain}"

def deterministic_noise(key: str, max_noise: float = MAX_GPS_NOISE_DEG) -> float:
    h = sha256_hex(str(key))
    intval = int(h[:8], 16)
    norm = intval / 0xFFFFFFFF
    return (norm * 2 - 1) * max_noise

def read_csv_with_clean_header(path: str) -> (List[str], List[List[str]]):
    """
    Read CSV handling BOM and stray whitespace in header. Returns (clean_header, data_rows).
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            raise ValueError(f"CSV file '{path}' is empty")
        # Clean header: strip whitespace and remove BOM if present (utf-8-sig already removes BOM)
        header = [h.strip() for h in raw_header]
        rows = [r for r in reader]
    return header, rows

def rows_to_dicts(header: List[str], rows: List[List[str]]) -> List[Dict[str,str]]:
    dicts = []
    for r in rows:
        # If row has fewer cols than header, pad with empty strings; if more, truncate
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[:len(header)]
        d = {header[i]: r[i] for i in range(len(header))}
        dicts.append(d)
    return dicts

def write_dicts_csv(path: str, fieldnames: List[str], rows: List[Dict[str,str]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def anonymize_user_table(input_path: str, output_path: str) -> Dict[str, str]:
    header, rows = read_csv_with_clean_header(input_path)
    dict_rows = rows_to_dicts(header, rows)

    if "user_id" not in header:
        raise ValueError("Input user CSV must have 'user_id' column")

    mapping = {}
    out_rows = []
    for row in dict_rows:
        orig_uid = row.get("user_id", "")
        pseudo_uid = pseudonymize_identifier(orig_uid, prefix="user")
        mapping[str(orig_uid)] = pseudo_uid
        row["user_id"] = pseudo_uid

        if "first_name" in row:
            row["first_name"] = sha256_hex(row["first_name"])[:12]
        if "last_name" in row:
            row["last_name"] = sha256_hex(row["last_name"])[:12]
        if "email" in row:
            row["email"] = pseudonymize_email(row["email"])
        if "phone_number" in row:
            row["phone_number"] = mask_phone(row["phone_number"])

        out_rows.append(row)

    write_dicts_csv(output_path, header, out_rows)
    print(f"Wrote anonymized users to {output_path}")
    return mapping

def anonymize_transaction_table(input_path: str, output_path: str, user_mapping: Dict[str,str]):
    header, rows = read_csv_with_clean_header(input_path)
    dict_rows = rows_to_dicts(header, rows)

    if "seller_id" not in header or "listing_location_gps" not in header or "listing_id" not in header:
        raise ValueError("Input transaction CSV must have 'seller_id', 'listing_location_gps' and 'listing_id' columns")

    out_rows = []
    for row in dict_rows:
        orig_sid = row.get("seller_id", "")
        if str(orig_sid) in user_mapping:
            row["seller_id"] = user_mapping[str(orig_sid)]
        else:
            row["seller_id"] = pseudonymize_identifier(orig_sid, prefix="seller")

        gps_val = row.get("listing_location_gps", "")
        listing_id = row.get("listing_id", "")
        try:
            coord = float(gps_val)
            noise = deterministic_noise(listing_id)
            new_coord = coord + noise
            row["listing_location_gps"] = f"{new_coord:.5f}"
        except Exception:
            row["listing_location_gps"] = sha256_hex(str(gps_val))[:12]

        out_rows.append(row)

    write_dicts_csv(output_path, header, out_rows)
    print(f"Wrote anonymized transactions to {output_path}")

def main():
    if len(sys.argv) != 5:
        print("Usage: python anonymize_csv.py USER_TABLE.csv TRANSACTION_DATA.csv anonymized_users.csv anonymized_transactions.csv")
        sys.exit(1)

    user_in, trans_in, user_out, trans_out = sys.argv[1:5]
    try:
        mapping = anonymize_user_table(user_in, user_out)
        anonymize_transaction_table(trans_in, trans_out, mapping)
        print("Anonymization complete.")
    except Exception as e:
        print("Error:", e)
        sys.exit(2)

if __name__ == "__main__":
    main()
