import os
import pandas as pd
import sqlite3

# --- ユーザー定義セクション ---
excel_file_name = "データベース.xlsx"       # static/excel_files 内のExcelファイル名
header_row = 0                         # ヘッダー行番号（例：2行目なら1）
hourly_db_name = "output_hourly.db"   # 1時間平均DB
daily_db_name = "output_daily.db"     # 1日平均DB
# ----------------------------

# Excelパス構築
excel_path = os.path.join("static", "excel_files", excel_file_name)

# Excelファイルの読み込み
df = pd.read_excel(excel_path, header=header_row)

# Timestamp列名を統一（最左列がTimestamp）
df.rename(columns={df.columns[0]: "Timestamp"}, inplace=True)

# Timestampをdatetime型に変換
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# インデックスに設定（リサンプルのため）
df.set_index("Timestamp", inplace=True)

# データ型を float に変換（エラーはNaN）
df = df.apply(pd.to_numeric, errors="coerce")

# ------------------------------
# 平均処理と保存関数
# ------------------------------
def save_aggregated_to_db(df_resampled, db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for column in df_resampled.columns:
        table_name = column

        # テーブル作成（既存テーブル削除）
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        cursor.execute(f"""
            CREATE TABLE `{table_name}` (
                Timestamp TEXT,
                `{column}` REAL
            )
        """)

        # DataFrameとして保存（リサンプル結果）
        temp_df = df_resampled[[column]].reset_index()
        temp_df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.close()
    print(f"{db_name} に保存完了。")

# ------------------------------
# 1時間平均（Hourly）
# ------------------------------
hourly_df = df.resample("H").mean()
save_aggregated_to_db(hourly_df, hourly_db_name)

# ------------------------------
# 1日平均（Daily）
# ------------------------------
daily_df = df.resample("D").mean()
save_aggregated_to_db(daily_df, daily_db_name)
