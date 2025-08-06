import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import argparse

def encrypt_string(key: str, plaintext: str) -> str:
    """
    任意の文字列をキーとして、別の任意の文字列を暗号化する。

    Args:
        key (str): 暗号化キー。
        plaintext (str): 暗号化する平文。

    Returns:
        str: base64エンコードされたソルトと暗号化されたデータ。
    """
    # ソルトを生成
    salt = os.urandom(16)

    # PBKDF2を使用してキーを導出
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    # Fernetインスタンスを作成し、データを暗号化
    f = Fernet(derived_key)
    encrypted_data = f.encrypt(plaintext.encode())

    # ソルトと暗号化データを結合して返す
    return base64.b64encode(salt + encrypted_data).decode('utf-8')

if __name__ == "__main__":
    # キーをコードに埋め込む
    hardcoded_key = "takuyatakuyatakuya"
    input_file = "input.txt"
    output_file = "encrypted.txt"
    command_prefix = "/decrypt"

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            plaintext = f.read()

        encrypted_string = encrypt_string(hardcoded_key, plaintext)

        # コマンド形式で出力
        output_command = f'{command_prefix} "{encrypted_string}"'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_command)

        print(f"Successfully encrypted and formatted command to '{output_file}'.")
        print("You can now copy the content of this file to trigger decryption.")

    except FileNotFoundError:
        print(f"Error: '{input_file}' not found. Please create it and add the text to encrypt.")
    except Exception as e:
        print(f"An error occurred: {e}")
