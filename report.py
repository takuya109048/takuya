import json
import os
import re
import webbrowser
from flask import Flask
from flask import jsonify, request, send_file

app = Flask(__name__)

def insert_comments_in_headings(markdown_file):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        # 見出し行を検出
        if re.match(r'#+\s+.+', line):
            # 次の行が存在し、かつコメント行でない場合
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('>'):
                new_lines.append('> コメント\n')

    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def save_comments_to_files(markdown_file):
    current_path = None
    comment_buffer = []
    processed_paths = set()
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 見出しからパスを抽出
            path_match = re.search(r'<!--(.+?)-->', line)
            if path_match:
                # 前のパスのコメントを保存
                if current_path:
                    comment_file = os.path.join(current_path, 'comment.txt')
                    os.makedirs(os.path.dirname(comment_file), exist_ok=True)
                    with open(comment_file, 'w', encoding='utf-8') as cf:
                        cf.write('\n'.join(comment_buffer))
                    processed_paths.add(current_path)
                    comment_buffer = []
                
                current_path = path_match.group(1)
                
            # '>'で始まるコメント行を収集
            elif line.strip().startswith('>'):
                comment = line.strip()[1:].strip()
                if comment:
                    comment_buffer.append(comment)
    
    # 最後のパスのコメントを保存
    if current_path:
        comment_file = os.path.join(current_path, 'comment.txt')
        os.makedirs(os.path.dirname(comment_file), exist_ok=True)
        with open(comment_file, 'w', encoding='utf-8') as cf:
            cf.write('\n'.join(comment_buffer))
        processed_paths.add(current_path)

def list_directories(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(root_dir):
            # .venvディレクトリを除外
            dirs[:] = [d for d in dirs if d != '.venv']
            # ルートディレクトリ自体をスキップ
            if root == root_dir:
                continue
            level = root.replace(root_dir, '').count(os.sep)
            indent = '#' * (level + 1)
            relative_path = os.path.relpath(root, root_dir)
            f.write(f'{indent} {os.path.basename(root)} <!--{relative_path}-->\n')
            
            # comment.txtからコメントを読み込み
            comment_file = os.path.join(root, 'comment.txt')
            if os.path.exists(comment_file):
                with open(comment_file, 'r', encoding='utf-8') as cf:
                    comments = cf.readlines()
                    for comment in comments:
                        if comment.strip():
                            f.write(f'> {comment.strip()}\n')
                    f.write('\n')
            
            # 画像ファイルの処理
            image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            if image_files:
                # 既存のJSONファイルを読み込む
                json_file = os.path.join(root, 'images.json')
                existing_data = {}
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as jf:
                        existing_data = json.load(jf)
                
                # 新しい画像のみFalseとし、既存の値は保持
                images_data = {}
                for file in image_files:
                    if file in existing_data:
                        images_data[file] = existing_data[file]
                    else:
                        images_data[file] = 'False'
                        
                # JSONファイルを保存
                with open(json_file, 'w', encoding='utf-8') as jf:
                    json.dump(images_data, jf, ensure_ascii=False, indent=4)
                
                f.write('\n')
                f.write('<table>\n')
                for i in range(0, len(image_files), 2):
                    img1 = os.path.join(root, image_files[i])
                    img2 = os.path.join(root, image_files[i + 1]) if i + 1 < len(image_files) else ''
                    f.write('<tr>\n')
                    f.write(f'  <td><img src="{img1}" style="width: 100%;"></td>\n')
                    if img2:
                        f.write(f'  <td><img src="{img2}" style="width: 100%;"></td>\n')
                    else:
                        f.write('  <td></td>\n')
                    f.write('</tr>\n')
                f.write('</table>\n')
                f.write('\n')

def list_directories_without_images(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        # ヘッダーの書き込み
        f.write('| 項目 | コメント |\n')
        f.write('|-----------|----------|\n')
        
        for root, dirs, files in os.walk(root_dir):
            # .venvディレクトリを除外
            dirs[:] = [d for d in dirs if d != '.venv']
            # ルートディレクトリはスキップ
            if root == root_dir:
                continue
                
            # 相対パスとディレクトリ名を取得
            relative_path = os.path.relpath(root, root_dir)
            dir_name = os.path.basename(root)
            
            # ディレクトリの階層に応じてインデントを追加
            level = relative_path.count(os.sep)
            indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * level  # HTMLスペースでインデント
            
            # コメントファイルの読み込み
            comments = []
            comment_file = os.path.join(root, 'comment.txt')
            if os.path.exists(comment_file):
                with open(comment_file, 'r', encoding='utf-8') as cf:
                    comments = [line.strip() for line in cf.readlines() if line.strip() and line.strip() != '> コメント']
                    if comments == ['コメント']:
                        comments = []
            
            # コメントを改行で結合
            comment_text = '<br>'.join(comments) if comments else ''
            
            # テーブル行をHTML形式で書き込み
            f.write(f'| {indent}{dir_name} <!--{relative_path}--> | {comment_text} |\n')

def create_report_md(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d != '.venv']
            if root == root_dir:
                continue
            level = root.replace(root_dir, '').count(os.sep)
            indent = '#' * (level + 1)
            relative_path = os.path.relpath(root, root_dir)
            f.write(f'{indent} {os.path.basename(root)} <!--{relative_path}-->\n')
            
            # comment.txtからコメントを読み込み
            comment_file = os.path.join(root, 'comment.txt')
            if os.path.exists(comment_file):
                with open(comment_file, 'r', encoding='utf-8') as cf:
                    comments = cf.readlines()
                    for comment in comments:
                        if comment.strip() and comment.strip() != 'コメント':
                            f.write(f'> {comment.strip()}\n')
                    f.write('\n')
            
            # 画像ファイルの処理
            image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            if image_files:
                # 既存のJSONファイルを読み込む
                json_file = os.path.join(root, 'images.json')
                existing_data = {}
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as jf:
                        existing_data = json.load(jf)
                
                # Falseである画像を除外
                image_files = [file for file in image_files if existing_data.get(file, 'True') == 'True']
                
                if image_files:
                    f.write('\n')
                    f.write('<table>\n')
                    for i in range(0, len(image_files), 2):
                        img1 = os.path.join(root, image_files[i])
                        img2 = os.path.join(root, image_files[i + 1]) if i + 1 < len(image_files) else ''
                        f.write('<tr>\n')
                        f.write(f'  <td><img src="{img1}" style="width: 100%;"></td>\n')
                        if img2:
                            f.write(f'  <td><img src="{img2}" style="width: 100%;"></td>\n')
                        else:
                            f.write('  <td></td>\n')
                        f.write('</tr>\n')
                    f.write('</table>\n')
                    f.write('\n')

def process_table_for_three_columns(table_html):
    # 画像タグをすべて抽出
    img_tags = re.findall(r'<td><img[^>]+></td>', table_html)
    
    # 3列のテーブル構造を作成
    new_table = ['<table>']
    for i in range(0, len(img_tags), 3):
        row = ['<tr>']
        # 1行に最大3枚の画像を配置
        for j in range(3):
            if i + j < len(img_tags):
                row.append(img_tags[i + j])
            else:
                row.append('  <td></td>')
        row.append('</tr>')
        new_table.append('\n'.join(row))
    new_table.append('</table>')
    
    return '\n'.join(new_table)

def create_html_from_markdown(markdown_file):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # サイドバー用の見出しを抽出（HTMLコメントを含む）
    headings = re.findall(r'^(#+)\s+(.+?(?:\s+<!--.*?-->)?)$', content, re.MULTILINE)
    sidebar_content = []
    for index, (level, text) in enumerate(headings):
        # サイドバー表示用にHTMLコメントを削除
        clean_text = re.sub(r'\s*<!--.*?-->', '', text).strip()
        indent = '&nbsp;' * (len(level) - 1) * 4
        sidebar_content.append(f'<div class="sidebar-item" onclick="document.getElementById(\'heading-{index}\').scrollIntoView();">{indent}{clean_text}</div>')
    
    # 見出しをIDつきのHTMLに変換（コンテンツ内のHTMLコメントは保持）
    content = re.sub(r'^(#+)\s+(.+?(?:\s+<!--.*?-->)?)$', 
                    lambda m: f'<h{len(m.group(1))} id="heading-{headings.index((m.group(1), m.group(2)))}">{m.group(2)}</h{len(m.group(1))}>',
                    content, flags=re.MULTILINE)
    
    # 引用をテキストエリアに変換
    content = re.sub(r'^\>\s*(.+?)$', r'<textarea class="comment">\1</textarea>', content, flags=re.MULTILINE)
    
    # テーブル構造を3列に修正
    content = re.sub(r'<table>\n(?:<tr>\n(?:\s*<td>.*?</td>\n){2}\s*</tr>\n)*</table>',
                    lambda m: process_table_for_three_columns(m.group(0)),
                    content, flags=re.DOTALL)
    
    # 画像パスを相対パスに保持し、クリックイベントを追加
    content = re.sub(r'<img src="([^"]+)"', lambda m: f'<img src="/image/{m.group(1)}" onclick="toggleBorder(this)"', content)
    
    # 画像タグにdata-path属性を追加し、images.jsonから選択状態を読み込み
    def add_data_path_and_selected_class(match):
        img_path = match.group(1)
        json_file = os.path.join(os.path.dirname(img_path), 'images.json')
        selected_class = ''
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as jf:
                images_data = json.load(jf)
                if images_data.get(os.path.basename(img_path)) == 'True':
                    selected_class = ' selected'
        return f'<img src="/image/{img_path}" data-path="{img_path}" class="{selected_class}" onclick="toggleBorder(this)"'
    
    content = re.sub(r'<img src="/image/([^"]+)"', add_data_path_and_selected_class, content)
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
    html {{ scroll-behavior: smooth; }}
    body {{ 
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
    }}
    #sidebar {{
        width: 250px;
        background: #f5f5f5;
        padding: 20px;
        height: 100vh;
        position: fixed;
        overflow-y: auto;
        left: 0;
        top: 0;
    }}
    .sidebar-item {{
        padding: 5px 0;
        cursor: pointer;
    }}
    .sidebar-item:hover {{
        background: #e0e0e0;
    }}
    #main-content {{
        margin-left: 290px;
        padding: 2em;
        max-width: 1200px;
        flex-grow: 1;
        width: calc(100% - 290px);
        box-sizing: border-box;
    }}
    .comment {{ 
        color: #666; 
        margin-left: 2em; 
        width: 100%; 
        height: 100px; 
        border: 1px solid #ccc; 
        border-radius: 4px; 
        padding: 10px; 
        box-sizing: border-box; 
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    td {{ padding: 10px; width: 33.33%; }}
    img {{ 
        max-width: 100%; 
        height: auto; 
        border: 3px solid #ddd; 
        border-radius: 4px;
        transition: border-color 0.3s ease;
    }}
    img.selected {{ 
        border: 6px solid #2196F3;
        box-shadow: 0 0 15px rgba(33, 150, 243, 0.7);
    }}
    #apply-button {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 20px;
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }}
    #apply-button:hover {{
        background-color: #1976D2;
    }}
    </style>
    <script>
    let selectedImages = new Set();

    function toggleBorder(img) {{
        img.classList.toggle('selected');
        let path = img.getAttribute('data-path');
        if (img.classList.contains('selected')) {{
            selectedImages.add(path);
        }} else {{
            selectedImages.delete(path);
        }}
    }}

    function applyChanges() {{
        let imageData = {{}};
        document.querySelectorAll('img').forEach(img => {{
            let path = img.getAttribute('data-path');
            if (path) {{
                imageData[path] = img.classList.contains('selected');
            }}
        }});

        let commentsData = {{}};
        document.querySelectorAll('textarea.comment').forEach((textarea, index) => {{
            commentsData[index] = textarea.value;
        }});

        fetch('/update_images', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{ images: imageData, comments: commentsData }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                alert(data.message);
                window.location.reload();
            }} else {{
                alert('エラーが発生しました: ' + data.error);
            }}
        }})
        .catch(error => {{
            alert('エラーが発生しました: ' + error);
        }});
    }}

    // ページが読み込まれたときに既に選択されている画像をセットに追加
    document.addEventListener('DOMContentLoaded', () => {{
        document.querySelectorAll('img.selected').forEach(img => {{
            let path = img.getAttribute('data-path');
            if (path) {{
                selectedImages.add(path);
            }}
        }});
    }});
    </script>
</head>
<body>
<div id="sidebar">{chr(10).join(sidebar_content)}<div style="height: 100px;"></div></div>
<div id="main-content">{content}</div>
<button id="apply-button" onclick="applyChanges()">Apply</button>
</body>
</html>'''
    return html_content

@app.route('/')
def index():
    insert_comments_in_headings('directory_structure.md')
    save_comments_to_files('directory_structure.md')
    list_directories('.', 'directory_structure.md')
    list_directories_without_images('.', 'directory_structure_summary.md')
    create_report_md('.', 'report.md')
    html_content = create_html_from_markdown('directory_structure.md')
    return html_content

@app.route('/image/<path:image_path>')
def serve_image(image_path):
    return send_file(image_path)

@app.route('/update_images', methods=['POST'])
def update_images():
    try:
        data = request.json
        image_data = data.get('images', {})
        comments_data = data.get('comments', {})

        # 画像パスをディレクトリごとにグループ化
        dir_images = {}
        for path, selected in image_data.items():
            dir_path = os.path.dirname(path)
            if dir_path not in dir_images:
                dir_images[dir_path] = {}
            filename = os.path.basename(path)
            dir_images[dir_path][filename] = "True" if selected else "False"
        
        # images.jsonの更新
        for dir_path, images in dir_images.items():
            json_path = os.path.join(dir_path, 'images.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                for filename in images:
                    existing_data[filename] = images[filename]
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=4, ensure_ascii=False)

        # コメントの更新
        with open('directory_structure.md', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        comment_index = 0
        with open('directory_structure.md', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith('>'):
                    if str(comment_index) in comments_data:
                        if comments_data[str(comment_index)].strip():
                            new_comment_lines = comments_data[str(comment_index)].split('\n')
                            new_comment = '\n'.join([f'> {line}' for line in new_comment_lines])
                            f.write(f'{new_comment}\n')
                        else:
                            f.write(line)
                    else:
                        f.write(line)
                    comment_index += 1
                else:
                    f.write(line)

        return jsonify({"success": True, "message": "更新が完了しました。ページをリロードします。"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    if os.path.exists('directory_structure.md'):
        save_comments_to_files('directory_structure.md')

    list_directories('.', 'directory_structure.md')
    list_directories_without_images('.', 'directory_structure_summary.md')
    create_report_md('.', 'report.md')

    # ブラウザを開くURLを設定
    url = 'http://127.0.0.1:5000'
    # 新しいブラウザウィンドウでURLを開く
    webbrowser.open(url)
    # Flaskアプリケーションを起動
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        threaded=True
    )