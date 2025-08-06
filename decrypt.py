import base64
import time
import pyperclip
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

def decrypt_string(key: str, encrypted_text: str) -> str:
    """
    任意の文字列をキーとして、暗号化された文字列を復号する。

    Args:
        key (str): 復号キー。
        encrypted_text (str): base64エンコードされた暗号化データ。

    Returns:
        str: 復号された平文。
    """
    # base64デコード
    decoded_data = base64.b64decode(encrypted_text)

    # ソルトと暗号化データを分離
    salt = decoded_data[:16]
    encrypted_data = decoded_data[16:]

    # PBKDF2を使用してキーを導出
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    # Fernetインスタンスを作成し、データを復号
    f = Fernet(derived_key)
    decrypted_data = f.decrypt(encrypted_data)

    return decrypted_data.decode('utf-8')

if __name__ == "__main__":
    # キーをコードに埋め込む
    hardcoded_key = "takuyatakuyatakuya"
    command_prefix = "/decrypt "
    
    print("Clipboard decryption script started. Monitoring clipboard...")
    print("Press Ctrl+C to stop.")
    
    # 最後に確認したクリップボードの内容を保持
    recent_clipboard = pyperclip.paste()
    
    while True:
        try:
            clipboard_content = pyperclip.paste()
            # クリップボードの内容が新しくなったか確認
            if clipboard_content != recent_clipboard:
                recent_clipboard = clipboard_content
                
                # コマンド形式に一致するか確認
                if clipboard_content.startswith(command_prefix):
                    # 暗号化文字列を抽出
                    encrypted_text = clipboard_content[len(command_prefix):].strip()
                    
                    # ダブルクォーテーションがあれば削除
                    if encrypted_text.startswith('"') and encrypted_text.endswith('"'):
                        encrypted_text = encrypted_text[1:-1]

                    print(f"\n--- Decrypting command found ---")
                    try:
                        decrypted_string = decrypt_string(hardcoded_key, encrypted_text)
                        print(f"Decrypted string: {decrypted_string}")
                    except Exception as e:
                        print(f"Error during decryption: {e}")
                    finally:
                        print("---------------------------------")
            
            # 1秒待機
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nScript stopped by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            time.sleep(5)