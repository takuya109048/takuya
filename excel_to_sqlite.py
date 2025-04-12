import os
import pandas as pd
import sqlite3

def load_excel_to_dataframe(excel_file_path, header_row):
    """
    Excelファイルを読み込み、Timestamp列をdatetimeに変換し、インデックスに設定する。
    """
    df = pd.read_excel(excel_file_path, header=header_row)
    df.rename(columns={df.columns[0]: "Timestamp"}, inplace=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.set_index("Timestamp", inplace=True)
    df = df.apply(pd.to_numeric, errors='coerce')  # 数値変換（エラーはNaN）
    return df

def resample_and_save_to_db(df, rule, db_file):
    """
    指定された周期で平均化し、SQLite DBに保存。
    各カラムごとにテーブルを作成（Timestamp + 1カラム構成）。
    """
    resampled_df = df.resample(rule).mean()

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    for column in resampled_df.columns:
        table_name = column

        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        cursor.execute(f"""
            CREATE TABLE `{table_name}` (
                Timestamp TEXT,
                `{column}` REAL
            )
        """)

        temp_df = resampled_df[[column]].reset_index()
        temp_df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.close()
    print(f"[✓] {db_file} に {rule} 平均で保存完了。")

def main():
    # --- ユーザー定義セクション ---
    excel_file_name = "sample.xlsx"         # static/excel_files内のExcelファイル名
    header_row = 0                           # ヘッダー行の行番号（0始まり）
    hourly_db = "output_hourly.db"
    daily_db = "output_daily.db"
    # -----------------------------

    excel_file_path = os.path.join("static", "excel_files", excel_file_name)

    df = load_excel_to_dataframe(excel_file_path, header_row)

    resample_and_save_to_db(df, "H", hourly_db)
    resample_and_save_to_db(df, "D", daily_db)

if __name__ == "__main__":
    main()

