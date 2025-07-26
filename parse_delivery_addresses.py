
import re

# מסיר מילים כפולות בזוגות
def remove_duplicate_word_pairs(text):
    words = text.split()
    result = []
    i = 0
    while i < len(words):
        if i + 3 < len(words) and words[i] == words[i+2] and words[i+1] == words[i+3]:
            result.append(words[i])
            result.append(words[i+1])
            i += 4
        else:
            result.append(words[i])
            i += 1
    return " ".join(result)

# מנקה מילה 'דירה' מתחילת העיר
def clean_city_name(city):
    city_parts = city.split()
    if city_parts and city_parts[0] == "דירה":
        city_parts = city_parts[1:]
    return " ".join(city_parts)

# פונקציה ראשית
def parse_with_fallback_and_international_phone(row):
    text = str(row['MyDes'])
    phone_fallback = str(row['Phonedes']) if 'Phonedes' in row and row['Phonedes'] is not None else ""

    # --- שלב 1: מציאת טלפון ב-MyDes ---
    parts = text.split()
    parts = parts[2:] if len(parts) > 2 else []
    text_after_skip = " ".join(parts)

    phones = re.findall(r'(?:05|08|077)[\d-]{7,9}', text_after_skip)
    phone = phones[0].replace('-', '') if phones else ""

    clean_text = text_after_skip
    if phones:
        clean_text = text_after_skip.split(phones[0], 1)[-1].strip()
    clean_text = re.sub(r'(?:05|08|077)[\d-]{7,9}', '', clean_text).strip()

    predefined_cities = {"אופקים", "נתיבות", "שדרות"}
    parts = clean_text.replace('.', '').split()
    if parts and parts[-1] in predefined_cities:
        city = parts[-1]
        address = " ".join(parts[:-1])
    else:
        if '.' in clean_text:
            address_part, city_part = clean_text.split('.', 1)
            address = address_part.strip()
            city = city_part.strip()
        else:
            if len(parts) >= 2 and re.match(r'^[א-ת]+$', parts[-1]) and re.match(r'^[א-ת]+$', parts[-2]):
                city = " ".join(parts[-2:])
                address = " ".join(parts[:-2])
            else:
                city = parts[-1] if parts else ""
                address = " ".join(parts[:-1]) if len(parts) > 1 else ""

    city_parts = city.split()
    if city_parts and re.search(r'\d', city_parts[0]):
        address = (address + " " + city_parts[0]).strip()
        city = " ".join(city_parts[1:])

    address = remove_duplicate_word_pairs(address).replace('.', '').strip()
    city = clean_city_name(city)

    # --- שלב 2: fallback ל-Phonedes ---
    if not phone and phone_fallback:
        clean_phone = phone_fallback.replace('-', '').strip()
        if clean_phone.startswith('972') or clean_phone.startswith('+972'):
            clean_phone = '0' + clean_phone[-9:]
        elif clean_phone.startswith('5') or clean_phone.startswith('8') or clean_phone.startswith('77'):
            clean_phone = '0' + clean_phone
        if re.match(r'^(05|08|077)\d{7,8}$', clean_phone):
            phone = clean_phone

    # --- שלב 3: fallback ל-Comment ---
    if not phone and 'Comment' in row:
        comment_value = str(row['Comment']) if row['Comment'] is not None else ""
        phones_comment = re.findall(r'(?:\+?972|05|08|077)[\d-]{7,12}', comment_value)
        if phones_comment:
            clean_comment_phone = phones_comment[0].replace('-', '').replace(' ', '').replace('+', '')
            if clean_comment_phone.startswith('972'):
                clean_comment_phone = '0' + clean_comment_phone[3:]
            elif clean_comment_phone.startswith('5') or clean_comment_phone.startswith('8') or clean_comment_phone.startswith('77'):
                clean_comment_phone = '0' + clean_comment_phone
            if re.match(r'^(05|08|077)\d{7,8}$', clean_comment_phone):
                phone = clean_comment_phone

    # --- שלב 4: Cash ---
    cash = row['Govayna'] if 'Govayna' in row else ""
    if str(cash).strip() == "0.00" or str(cash).lower() == "nan":
        cash = ""
    else:
        cash = str(cash).split('.')[0]  # מסיר ספרות עשרוניות
        if cash:
            cash = "מזומן " + cash

    return address.strip(), city.strip(), phone.strip(), cash
