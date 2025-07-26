from flask import Flask, request, send_file, render_template_string
import pandas as pd
import os
from parse_delivery_addresses import parse_with_fallback_and_international_phone
from werkzeug.utils import secure_filename

app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<html lang="he">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>עיבוד קובץ משלוחים</title>
<style>
  body { font-family: Arial, sans-serif; text-align: center; background: #f9f9f9; padding: 20px; }
  h2 { margin-bottom: 20px; }
  input[type=file], input[type=text] { font-size: 18px; margin: 10px 0; padding: 10px; width: 90%%; max-width: 300px; }
  input[type=submit] { font-size: 20px; padding: 12px 30px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; }
  input[type=submit]:hover { background: #45a049; }
</style>
</head>
<body>
  <h2>בחר קובץ CSV/Excel לעיבוד</h2>
  <form method="post" enctype="multipart/form-data">
    <input type="file" name="file" required><br>
    <input type="text" name="filename" placeholder="שם קובץ פלט (לא חובה)"><br>
    <input type="submit" value="עבד והורד">
  </form>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            return "לא נבחר קובץ", 400
        
        # שם הקובץ שנבחר להורדה
        user_filename = request.form.get('filename').strip() if request.form.get('filename') else "Circuit_Ready"
        if not user_filename.endswith('.csv'):
            user_filename += '.csv'

        # שמירה זמנית
        filename = secure_filename(file.filename)
        input_path = os.path.join("/tmp", filename)
        file.save(input_path)

        # קריאת קובץ (תמיכה גם ב-Excel וגם ב-CSV)
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(input_path)
        else:
            df = pd.read_csv(input_path)

        # הפעלת פונקציית הפירוק
        processed_rows = []
        for _, row in df.iterrows():
            address, city, phone, cash = parse_with_fallback_and_international_phone(row)
            processed_rows.append({"Address": address, "City": city, "Phone": phone, "Cash": cash})

        output_df = pd.DataFrame(processed_rows)
        output_path = os.path.join("/tmp", user_filename)
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        return send_file(output_path, as_attachment=True)

    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
