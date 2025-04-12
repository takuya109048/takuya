import os
import pandas as pd
import sqlite3

def load_excel_to_dataframe(excel_file_path, header_row):
    df = pd.read_excel(excel_file_path, header=header_row)
    df.rename(columns={df.columns[0]: "Timestamp"}, inplace=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.set_index("Timestamp", inplace=True)
    df = df.apply(pd.to_numeric, errors='coerce')
    return df

def resample_and_save_to_db(df, mode, db_file_name):
    """
    mode: "1時間平均" または "1日平均"
    db_file_name: 保存するSQLite DBファイル名
    """
    if mode == "1時間平均":
        rule = "H"
    elif mode == "1日平均":
        rule = "D"
    else:
        print(f"[!] 無効なモードです: {mode}")
        return

    resampled_df = df.resample(rule).mean()

    conn = sqlite3.connect(db_file_name)
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
    print(f"[✓] {db_file_name} に {mode} を保存しました。")

def main():
    # --- ユーザー定義セクション ---
    excel_file_name = "データベース.xlsx"
    header_row = 0
    mode = "1時間平均"                  # "1時間平均" または "1日平均"
    db_file_name = "output_hourly.db"  # 保存先のSQLiteファイル名
    # -----------------------------

    excel_file_path = os.path.join("static", "excel_files", excel_file_name)
    df = load_excel_to_dataframe(excel_file_path, header_row)

    resample_and_save_to_db(df, mode, db_file_name)

if __name__ == "__main__":
    main()

